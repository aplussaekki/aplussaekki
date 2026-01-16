# app.py
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import threading
import time
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import Body, FastAPI, HTTPException, Query, Request
from pydantic import BaseModel, Field

# ✅ local-only prepare (in-process)
from core.prepare_runner import run_prepare

app = FastAPI(title="question-generator-api", version="1.0.0")

# =============================================================================
# Storage dirs (file-based, restart-safe)
# =============================================================================
DATA_DIR_DEFAULT = Path("data")
PDFS_DIR = DATA_DIR_DEFAULT / "pdfs"          # data/pdfs/{pdf_id}/source.pdf
JOBS_DIR = DATA_DIR_DEFAULT / "jobs"          # data/jobs/{job_id}.json, .log
RESULTS_DIR = DATA_DIR_DEFAULT / "results"    # data/results/{pdf_id}.questions.json

PDFS_DIR.mkdir(parents=True, exist_ok=True)
JOBS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# =============================================================================
# In-memory cache (backed by disk)
# =============================================================================
RUNS: Dict[str, Dict[str, Any]] = {}
RUNS_LOCK = threading.Lock()
EXECUTOR = ThreadPoolExecutor(max_workers=max(2, (os.cpu_count() or 4) // 2))

# =============================================================================
# Schemas (existing)
# =============================================================================
class PrepareRequest(BaseModel):
    pdf_path: str
    pdf_id: str = "lecture"
    out_dir: str = "artifacts/lecture"
    dpi: int = 150


class GenerateRequest(BaseModel):
    # 입력/기본
    pdf_path: Optional[str] = None  # 있으면 prepare까지 같이 실행 가능
    jobs_jsonl: str = "question_jobs.jsonl"
    out_dir: str = "artifacts/lecture"
    pdf_id: str = "lecture"
    data_dir: str = "data"

    # 공통
    overwrite: bool = True
    max_retries: int = 5
    flush_every: int = 1

    # 단계별 workers
    presence_workers: int = 3
    extract_workers: int = 3
    q_workers: int = 2

    # prepare 옵션
    dpi: int = 150

    # job builder 옵션
    total_q: int = 0
    no_require_table_q: bool = False  # 표 기반 문제 강제 끄고싶을 때만 True (권장X)

    # question pipeline 옵션
    preview: int = 0
    ordered_preview: bool = False
    save_generated: bool = True
    save_answers_only: bool = True

    model: str = "gpt-4o-mini"
    table_model: str = "gpt-4o-mini"
    fallback_model: str = "gpt-4o-mini"
    temperature: float = 0.3

    # 문제 유형/난이도 설정
    difficulty: str = "mixed"  # easy | medium | hard | mixed
    mcq_ratio: float = 1.0  # MCQ(객관식) 비율 (0.0~1.0)
    saq_ratio: float = 0.0  # SAQ(단답형) 비율 (0.0~1.0)

    # 단계 선택(운영/디버그 편의)
    run_prepare: bool = True
    run_presence: bool = True
    run_extract: bool = True
    run_section_indexer: bool = True
    run_section_packager: bool = True
    run_job_builder: bool = True
    run_question_pipeline: bool = True


class RunStatusResponse(BaseModel):
    run_id: str
    status: str  # QUEUED / RUNNING / DONE / FAILED
    stage: str
    started_at: float
    updated_at: float
    finished_at: Optional[float] = None
    error: Optional[str] = None

    jobs_total: Optional[int] = None
    jobs_done: Optional[int] = None

    results_spec: Optional[str] = None
    verified_aggregate: Optional[str] = None
    log_path: Optional[str] = None


# =============================================================================
# Schemas (spec API)
# =============================================================================
class PdfCreateBody(BaseModel):
    pdf_path: Optional[str] = Field(default=None, description="Server-local existing PDF path")
    pdf_id: Optional[str] = Field(default=None, description="If omitted, server generates one")


class PdfCreateResponse(BaseModel):
    pdf_id: str
    stored_path: str


class JobCreateBody(BaseModel):
    # Optional override of pipeline settings
    out_dir: Optional[str] = None
    data_dir: Optional[str] = None

    overwrite: Optional[bool] = None
    presence_workers: Optional[int] = None
    extract_workers: Optional[int] = None
    q_workers: Optional[int] = None

    model: Optional[str] = None
    table_model: Optional[str] = None
    fallback_model: Optional[str] = None
    temperature: Optional[float] = None

    run_prepare: Optional[bool] = None
    run_presence: Optional[bool] = None
    run_extract: Optional[bool] = None
    run_section_indexer: Optional[bool] = None
    run_section_packager: Optional[bool] = None
    run_job_builder: Optional[bool] = None
    run_question_pipeline: Optional[bool] = None

    total_q: Optional[int] = None
    no_require_table_q: Optional[bool] = None

    # prepare dpi override
    dpi: Optional[int] = None

    # 문제 유형/난이도 설정
    difficulty: Optional[str] = None  # easy | medium | hard | mixed
    mcq_ratio: Optional[float] = None  # MCQ 비율 (0.0~1.0)
    saq_ratio: Optional[float] = None  # SAQ 비율 (0.0~1.0)


class JobCreateResponse(BaseModel):
    job_id: str
    pdf_id: str
    status: str
    stage: str


class JobStatusResponse(BaseModel):
    job_id: str
    pdf_id: str
    status: str  # QUEUED/RUNNING/DONE/FAILED
    stage: str
    detail_stage: Optional[str] = None
    error: Optional[str] = None
    started_at: float
    updated_at: float
    finished_at: Optional[float] = None
    jobs_total: Optional[int] = None
    jobs_done: Optional[int] = None


# =============================================================================
# Helpers
# =============================================================================
def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def _job_state_path(job_id: str) -> Path:
    return JOBS_DIR / f"{job_id}.json"


def _job_log_path(job_id: str) -> Path:
    return JOBS_DIR / f"{job_id}.log"


def _append_log(job_id: str, line: str) -> None:
    p = _job_log_path(job_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(line)
        if not line.endswith("\n"):
            f.write("\n")


def _atomic_write_json(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def _load_json_safe(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def _read_jsonl_count(path: Path) -> int:
    if not path.exists():
        return 0
    n = 0
    with path.open("r", encoding="utf-8-sig") as f:
        for ln in f:
            ln = (ln or "").strip()
            if not ln or ln.startswith("#"):
                continue
            n += 1
    return n


def _count_verified_jobs(out_dir: Path) -> int:
    qv = out_dir / "questions_verified"
    if not qv.exists():
        return 0
    return len(list(qv.glob("job_*.json")))


def _resolve_jobs_path(out_dir: Path, jobs_jsonl: str) -> Path:
    jp = Path(jobs_jsonl)
    if jp.is_absolute():
        return jp
    if len(jp.parts) > 1:
        return jp
    return out_dir / jp


def _set_run(job_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
    with RUNS_LOCK:
        cur = RUNS.get(job_id, {})
        cur.update(patch)
        cur["job_id"] = job_id
        cur["run_id"] = job_id  # legacy alias
        RUNS[job_id] = cur
        _atomic_write_json(_job_state_path(job_id), cur)
        return dict(cur)


def _get_run(job_id: str) -> Optional[Dict[str, Any]]:
    with RUNS_LOCK:
        info = RUNS.get(job_id)
        if info:
            return dict(info)
    st = _load_json_safe(_job_state_path(job_id))
    if st:
        with RUNS_LOCK:
            RUNS[job_id] = st
        return dict(st)
    return None


def _run_cmd_stream(job_id: str, stage: str, cmd: List[str], cwd: Optional[str] = None) -> None:
    _append_log(job_id, f"\n===== STAGE {stage} START =====")
    _append_log(job_id, "CMD: " + " ".join(cmd))

    proc = subprocess.Popen(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        universal_newlines=True,
    )

    assert proc.stdout is not None
    for line in proc.stdout:
        _append_log(job_id, line.rstrip("\n"))

    rc = proc.wait()
    _append_log(job_id, f"===== STAGE {stage} END (rc={rc}) =====\n")
    if rc != 0:
        raise RuntimeError(f"{stage} failed (exit_code={rc})")


def _run_module_with_args_fallback(
    job_id: str,
    stage: str,
    module: str,
    args: List[str],
    allow_fallback_noargs: bool = True,
) -> None:
    py = os.environ.get("PYTHON_EXE", sys.executable)

    cmd = [py, "-m", module, *args]
    try:
        _run_cmd_stream(job_id, stage, cmd)
        return
    except Exception as e:
        if not allow_fallback_noargs:
            raise
        msg = str(e)
        _append_log(job_id, f"[WARN] {stage} first try failed: {msg}")
        cmd2 = [py, "-m", module]
        _append_log(job_id, f"[WARN] retry without args: {' '.join(cmd2)}")
        _run_cmd_stream(job_id, stage, cmd2)


def _preferred_result_paths(req: GenerateRequest) -> Dict[str, str]:
    out_dir = Path(req.out_dir)
    pdf_id = req.pdf_id
    data_dir = Path(req.data_dir)
    return {
        "results_spec": str(data_dir / "results" / f"{pdf_id}.questions.json"),
        "verified_aggregate": str(out_dir / "questions_verified_aggregate.json"),
        "verified_dir": str(out_dir / "questions_verified"),
        "answers_only_dir": str(out_dir / "answers_only"),
        "generated_dir": str(out_dir / "questions_generated"),
    }


def _aggregate_prefer_spec(pdf_id: str, out_dir: Path, data_dir: Path) -> Dict[str, Any]:
    spec_path = data_dir / "results" / f"{pdf_id}.questions.json"
    agg_path = out_dir / "questions_verified_aggregate.json"

    obj = _load_json_safe(spec_path)
    if obj:
        return {"source": str(spec_path), "data": obj}

    obj = _load_json_safe(agg_path)
    if obj:
        return {"source": str(agg_path), "data": obj}

    qv = out_dir / "questions_verified"
    if not qv.exists():
        raise FileNotFoundError(f"questions_verified not found: {qv}")

    items = []
    for fp in sorted(qv.glob("job_*.json")):
        items.append(_load_json_safe(fp) or {"file": fp.name, "error": "read_failed"})

    return {"source": f"scan:{qv}", "data": {"pdf_id": pdf_id, "items": items}}


# view=student에서 제거할 키(최소 안전선)
_SENSITIVE_KEYS = {
    "answer", "answers", "correct_answer", "correctAnswer", "solution",
    "explanation", "rationale", "reason",
}

def _strip_sensitive(obj: Any) -> Any:
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if isinstance(k, str) and k in _SENSITIVE_KEYS:
                continue
            out[k] = _strip_sensitive(v)
        return out
    if isinstance(obj, list):
        return [_strip_sensitive(x) for x in obj]
    return obj


# =============================================================================
# Core: start async pipeline (used by /generate and spec job endpoint)
# =============================================================================
def _start_pipeline(req: GenerateRequest) -> Dict[str, Any]:
    job_id = uuid.uuid4().hex
    now = time.time()

    out_dir = Path(req.out_dir)
    jobs_path = _resolve_jobs_path(out_dir, req.jobs_jsonl)
    jobs_total = _read_jsonl_count(jobs_path)

    _set_run(job_id, {
        "status": "QUEUED",
        "stage": "QUEUED",
        "detail_stage": None,
        "started_at": now,
        "updated_at": now,
        "finished_at": None,
        "error": None,
        "req": req.model_dump(),
        "pdf_id": req.pdf_id,
        "jobs_total": jobs_total,
        "jobs_done": 0,
        "paths": _preferred_result_paths(req),
    })
    _append_log(job_id, f"[INIT] job_id={job_id}")
    _append_log(job_id, f"[INIT] request={req.model_dump()}")
    _append_log(job_id, f"[INIT] jobs_path={str(jobs_path)} jobs_total={jobs_total}")

    def _task():
        try:
            _set_run(job_id, {"status": "RUNNING", "stage": "START", "updated_at": time.time()})

            # 1) PREPARE (in-process)
            if req.run_prepare:
                if not req.pdf_path:
                    raise RuntimeError("run_prepare=True but pdf_path is empty")
                _set_run(job_id, {"stage": "PREPARE", "updated_at": time.time()})
                _append_log(job_id, "[PREPARE] calling run_prepare() (local-only)")
                run_prepare(
                    pdf_path=Path(req.pdf_path),
                    pdf_id=req.pdf_id,
                    out_dir=Path(req.out_dir),
                    dpi=req.dpi,
                )

            # 2) TABLE PRESENCE (MM)
            if req.run_presence:
                _set_run(job_id, {"stage": "TABLE_PRESENCE", "updated_at": time.time()})
                args = [
                    "--out_dir", req.out_dir,
                    "--pdf_id", req.pdf_id,
                    "--workers", str(req.presence_workers),
                    "--max_retries", str(req.max_retries),
                    "--flush_every", str(req.flush_every),
                ]
                if req.overwrite:
                    args.append("--overwrite")
                _run_module_with_args_fallback(job_id, "TABLE_PRESENCE", "core.run_table_presence", args)

            # 3) TABLE EXTRACT (MM)
            if req.run_extract:
                _set_run(job_id, {"stage": "TABLE_EXTRACT", "updated_at": time.time()})
                args = [
                    "--out_dir", req.out_dir,
                    "--pdf_id", req.pdf_id,
                    "--workers", str(req.extract_workers),
                    "--max_retries", str(req.max_retries),
                    "--flush_every", str(req.flush_every),
                ]
                if req.overwrite:
                    args.append("--overwrite")
                _run_module_with_args_fallback(job_id, "TABLE_EXTRACT", "core.run_table_extract_mm", args)

            # 4) SECTION INDEXER (local; fallback no-args allowed)
            if req.run_section_indexer:
                _set_run(job_id, {"stage": "SECTION_INDEXER", "updated_at": time.time()})
                args = ["--out_dir", req.out_dir, "--pdf_id", req.pdf_id]
                _run_module_with_args_fallback(
                    job_id, "SECTION_INDEXER", "core.section_indexer", args, allow_fallback_noargs=True
                )

            # 5) SECTION CONTEXT PACKAGER
            if req.run_section_packager:
                _set_run(job_id, {"stage": "SECTION_PACKAGER", "updated_at": time.time()})
                args = ["--out_dir", req.out_dir, "--pdf_id", req.pdf_id]
                if req.overwrite:
                    args.append("--overwrite")
                _run_module_with_args_fallback(job_id, "SECTION_PACKAGER", "core.section_context_packager", args)

            # 6) JOB BUILDER
            if req.run_job_builder:
                _set_run(job_id, {"stage": "JOB_BUILDER", "updated_at": time.time()})
                args = [
                    "--out_dir", req.out_dir,
                    "--pdf_id", req.pdf_id,
                    "--total_q", str(req.total_q),
                    "--difficulty", req.difficulty,
                    "--mcq_ratio", str(req.mcq_ratio),
                    "--saq_ratio", str(req.saq_ratio),
                ]
                if req.overwrite:
                    args.append("--overwrite")
                if req.no_require_table_q:
                    args.append("--no_require_table_q")
                _run_module_with_args_fallback(job_id, "JOB_BUILDER", "core.job_builder", args)

            # 7) QUESTION PIPELINE
            if req.run_question_pipeline:
                _set_run(job_id, {"stage": "QUESTION_PIPELINE", "updated_at": time.time()})
                args = [
                    "--out_dir", req.out_dir,
                    "--jobs", req.jobs_jsonl,
                    "--pdf_id", req.pdf_id,
                    "--workers", str(req.q_workers),
                    "--max_retries", str(req.max_retries),
                    "--model", req.model,
                    "--table_model", req.table_model,
                    "--fallback_model", req.fallback_model,
                    "--temperature", str(req.temperature),
                    "--data_dir", req.data_dir,
                ]
                if req.overwrite:
                    args.append("--overwrite")
                if req.preview:
                    args += ["--preview", str(req.preview)]
                if req.ordered_preview:
                    args.append("--ordered_preview")
                if req.save_generated:
                    args.append("--save_generated")
                if not req.save_answers_only:
                    args.append("--no_answers_only")

                _run_module_with_args_fallback(
                    job_id,
                    "QUESTION_PIPELINE",
                    "core.run_question_pipeline",
                    args,
                    allow_fallback_noargs=False,
                )

            jobs_done = _count_verified_jobs(Path(req.out_dir))
            _set_run(job_id, {
                "status": "DONE",
                "stage": "DONE",
                "updated_at": time.time(),
                "finished_at": time.time(),
                "jobs_done": jobs_done,
            })
            _append_log(job_id, f"[DONE] jobs_done={jobs_done}")
            _append_log(job_id, f"[DONE] outputs={_preferred_result_paths(req)}")

        except Exception as e:
            err_txt = "".join(traceback.format_exception(type(e), e, e.__traceback__))[-40000:]
            _append_log(job_id, "\n[FATAL]\n" + err_txt + "\n")
            _set_run(job_id, {
                "status": "FAILED",
                "stage": "FAILED",
                "updated_at": time.time(),
                "finished_at": time.time(),
                "error": err_txt,
            })

    EXECUTOR.submit(_task)
    return {"job_id": job_id, "jobs_total": jobs_total}


# =============================================================================
# Spec Routes
# =============================================================================
@app.get("/health")
def health():
    return {"ok": True, "time": _now_iso()}


@app.post("/pdfs", response_model=PdfCreateResponse)
async def create_pdf(request: Request):
    """
    Register a PDF for later job execution.

    Supports BOTH:
      - multipart/form-data with fields:
          - file: (uploaded file)
          - pdf_id: (optional)
      - application/json body:
          { "pdf_path": "...", "pdf_id": "..."? }

    Note:
      We parse based on Content-Type to avoid FastAPI treating the endpoint
      as multipart-only (which breaks JSON body parsing).
    """
    ctype = (request.headers.get("content-type") or "").lower()

    def alloc_pdf_id(maybe: Optional[str]) -> str:
        return maybe or uuid.uuid4().hex

    # --- multipart upload ---
    if "multipart/form-data" in ctype:
        form = await request.form()
        up = form.get("file")
        pdf_id = alloc_pdf_id(form.get("pdf_id") or None)

        if up is None or not hasattr(up, "read"):
            raise HTTPException(status_code=400, detail="multipart requires field 'file'")

        target_dir = PDFS_DIR / pdf_id
        target_dir.mkdir(parents=True, exist_ok=True)
        stored_path = target_dir / "source.pdf"

        with stored_path.open("wb") as f:
            while True:
                chunk = await up.read(1024 * 1024)
                if not chunk:
                    break
                f.write(chunk)

        return PdfCreateResponse(pdf_id=pdf_id, stored_path=str(stored_path))

    # --- JSON path registration ---
    if "application/json" in ctype or ctype.startswith("application/json"):
        data = await request.json()
        body = PdfCreateBody.model_validate(data)
        pdf_id = alloc_pdf_id(body.pdf_id)

        if not body.pdf_path:
            raise HTTPException(status_code=400, detail="json requires 'pdf_path'")

        src = Path(body.pdf_path)
        if not src.exists():
            raise HTTPException(status_code=400, detail=f"pdf_path not found: {src}")

        target_dir = PDFS_DIR / pdf_id
        target_dir.mkdir(parents=True, exist_ok=True)
        stored_path = target_dir / "source.pdf"
        shutil.copyfile(src, stored_path)

        return PdfCreateResponse(pdf_id=pdf_id, stored_path=str(stored_path))

    raise HTTPException(
        status_code=400,
        detail="unsupported content-type; use multipart/form-data (file) or application/json (pdf_path)",
    )


@app.post("/pdfs/{pdf_id}/jobs/question-generation", response_model=JobCreateResponse)
def create_question_generation_job(pdf_id: str, body: JobCreateBody = Body(default=JobCreateBody())):
    stored_pdf = PDFS_DIR / pdf_id / "source.pdf"
    if not stored_pdf.exists():
        raise HTTPException(status_code=404, detail=f"pdf_id not found or source.pdf missing: {pdf_id}")

    out_dir = body.out_dir or f"artifacts/{pdf_id}"
    data_dir = body.data_dir or str(DATA_DIR_DEFAULT)

    req = GenerateRequest(
        pdf_path=str(stored_pdf),
        pdf_id=pdf_id,
        out_dir=out_dir,
        data_dir=data_dir,
    )

    # apply overrides
    for k, v in body.model_dump(exclude_none=True).items():
        if hasattr(req, k):
            setattr(req, k, v)

    started = _start_pipeline(req)
    job_id = started["job_id"]
    info = _get_run(job_id) or {}

    return JobCreateResponse(
        job_id=job_id,
        pdf_id=pdf_id,
        status=info.get("status", "QUEUED"),
        stage=info.get("stage", "QUEUED"),
    )


@app.get("/jobs/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str):
    info = _get_run(job_id)
    if not info:
        raise HTTPException(status_code=404, detail=f"job_id not found: {job_id}")

    req = info.get("req", {}) if isinstance(info.get("req"), dict) else {}
    pdf_id = info.get("pdf_id") or req.get("pdf_id") or "lecture"
    out_dir = Path(req.get("out_dir", f"artifacts/{pdf_id}"))

    jobs_done = _count_verified_jobs(out_dir)
    _set_run(job_id, {"jobs_done": jobs_done, "updated_at": time.time()})
    info = _get_run(job_id) or info

    return JobStatusResponse(
        job_id=job_id,
        pdf_id=pdf_id,
        status=info.get("status", "UNKNOWN"),
        stage=info.get("stage", "UNKNOWN"),
        detail_stage=info.get("detail_stage"),
        error=info.get("error"),
        started_at=float(info.get("started_at", 0.0)),
        updated_at=float(info.get("updated_at", 0.0)),
        finished_at=info.get("finished_at"),
        jobs_total=info.get("jobs_total"),
        jobs_done=info.get("jobs_done"),
    )


@app.get("/pdfs/{pdf_id}/questions")
def get_questions(pdf_id: str, view: str = Query(default="teacher", pattern="^(teacher|student)$")):
    # 1) preferred spec result path
    spec_path = RESULTS_DIR / f"{pdf_id}.questions.json"
    obj = _load_json_safe(spec_path)

    # 2) fallback aggregate scan
    if obj is None:
        out_dir = Path(f"artifacts/{pdf_id}")
        try:
            payload = _aggregate_prefer_spec(pdf_id=pdf_id, out_dir=out_dir, data_dir=DATA_DIR_DEFAULT)
            obj = payload.get("data")
        except Exception:
            obj = None

    if obj is None:
        raise HTTPException(status_code=404, detail=f"questions not found for pdf_id={pdf_id}")

    if view == "student":
        obj = _strip_sensitive(obj)

    return {"ok": True, "pdf_id": pdf_id, "view": view, "data": obj}


# =============================================================================
# Legacy / Compatibility Routes (optional but handy)
# =============================================================================
@app.post("/prepare")
def prepare(req: PrepareRequest):
    pdf_path = Path(req.pdf_path)
    out_dir = Path(req.out_dir)

    if not pdf_path.exists():
        raise HTTPException(status_code=400, detail=f"pdf_path not found: {pdf_path}")

    result = run_prepare(
        pdf_path=pdf_path,
        pdf_id=req.pdf_id,
        out_dir=out_dir,
        dpi=req.dpi,
    )
    return {"ok": True, "result": result}


@app.post("/generate")
def generate(req: GenerateRequest):
    started = _start_pipeline(req)
    return {"ok": True, "run_id": started["job_id"], "jobs_total": started["jobs_total"]}


@app.get("/result/{run_id}", response_model=RunStatusResponse)
def result(run_id: str):
    info = _get_run(run_id)
    if not info:
        raise HTTPException(status_code=404, detail=f"run_id not found: {run_id}")

    req = info.get("req", {}) if isinstance(info.get("req"), dict) else {}
    pdf_id = info.get("pdf_id") or req.get("pdf_id") or "lecture"
    out_dir = Path(req.get("out_dir", f"artifacts/{pdf_id}"))

    jobs_done = _count_verified_jobs(out_dir)
    _set_run(run_id, {"jobs_done": jobs_done, "updated_at": time.time()})
    info = _get_run(run_id) or info

    paths = info.get("paths", {}) if isinstance(info.get("paths"), dict) else {}
    return RunStatusResponse(
        run_id=run_id,
        status=info.get("status", "UNKNOWN"),
        stage=info.get("stage", "UNKNOWN"),
        started_at=float(info.get("started_at", 0.0)),
        updated_at=float(info.get("updated_at", 0.0)),
        finished_at=info.get("finished_at"),
        error=info.get("error"),
        jobs_total=info.get("jobs_total"),
        jobs_done=info.get("jobs_done"),
        results_spec=paths.get("results_spec"),
        verified_aggregate=paths.get("verified_aggregate"),
        log_path=str(_job_log_path(run_id)),
    )


@app.get("/aggregate")
def aggregate(
    run_id: Optional[str] = None,
    out_dir: Optional[str] = None,
    pdf_id: str = "lecture",
    data_dir: str = "data",
):
    if out_dir:
        target_out = Path(out_dir)
    elif run_id:
        info = _get_run(run_id)
        if not info:
            raise HTTPException(status_code=404, detail=f"run_id not found: {run_id}")
        req = info.get("req", {}) if isinstance(info.get("req"), dict) else {}
        pdf_id = req.get("pdf_id", pdf_id)
        data_dir = req.get("data_dir", data_dir)
        target_out = Path(req.get("out_dir", f"artifacts/{pdf_id}"))
    else:
        target_out = Path("artifacts/lecture")

    try:
        payload = _aggregate_prefer_spec(
            pdf_id=pdf_id,
            out_dir=target_out,
            data_dir=Path(data_dir),
        )
        return {"ok": True, **payload}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/runs")
def list_runs():
    with RUNS_LOCK:
        slim = {}
        for k, v in RUNS.items():
            slim[k] = {
                "status": v.get("status"),
                "stage": v.get("stage"),
                "started_at": v.get("started_at"),
                "updated_at": v.get("updated_at"),
                "finished_at": v.get("finished_at"),
                "jobs_total": v.get("jobs_total"),
                "jobs_done": v.get("jobs_done"),
                "pdf_id": v.get("pdf_id"),
            }
    return {"ok": True, "runs": slim}


@app.get("/logs/{run_id}")
def read_log(run_id: str, tail: int = 200):
    p = _job_log_path(run_id)
    if not p.exists():
        raise HTTPException(status_code=404, detail="log not found")
    lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    tail = max(1, min(5000, int(tail)))
    return {"ok": True, "run_id": run_id, "tail": tail, "lines": lines[-tail:]}
