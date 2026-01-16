# backend/engine/cli/run_job.py
"""
전체 파이프라인 실행
"""
import subprocess
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(override=True)


def run_step(name, cmd):
    """단계별 실행"""
    print(f"\n{'='*60}")
    print(f"▶ {name}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"❌ {name} 실패!")
        sys.exit(1)
    print(f"✅ {name} 완료")


def run_orchestrator(out_dir: Path, total_questions: int, use_llm: bool = True) -> dict:
    """
    Orchestrator 실행 → allocation 반환
    """
    from backend.engine.core.question_orchestrator import orchestrate_question_allocation
    
    # section_contexts에서 섹션 정보 읽기
    contexts_dir = out_dir / "section_contexts"
    index_path = contexts_dir / "index.json"
    
    if not index_path.exists():
        print("⚠️ section_contexts/index.json 없음")
        return {}
    
    index_data = json.loads(index_path.read_text(encoding="utf-8"))
    
    sections = []
    for item in index_data.get("items", []):
        # path가 "section_contexts\\section_S001.json" 형태일 수 있음
        item_path = item["path"]
        # 상대 경로에서 파일명만 추출
        if "\\" in item_path or "/" in item_path:
            item_path = Path(item_path).name
        section_path = contexts_dir / item_path
        if section_path.exists():
            section_data = json.loads(section_path.read_text(encoding="utf-8"))
            sections.append(section_data)
    
    if not sections:
        print("⚠️ 섹션 데이터 없음")
        return {}
    
    # Orchestrator 실행
    result = orchestrate_question_allocation(
        sections=sections,
        total_questions=total_questions,
        use_llm=use_llm,
        max_workers=4,
        cache_dir=out_dir / "cache",
    )
    
    allocation = result["allocation"]
    method = result["method"]
    
    print(f"✅ Orchestration 완료 ({method} 방식)")
    print(f"   배분: {allocation}")
    
    # ✅ allocation 저장 (Job Builder가 읽을 수 있도록)
    allocation_path = out_dir / "allocation.json"
    allocation_path.parent.mkdir(parents=True, exist_ok=True)
    allocation_path.write_text(
        json.dumps(allocation, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"💾 Allocation 저장: {allocation_path}")
    
    return allocation




def convert_to_spec(pdf_id: str, out_dir: Path):
    """
    명세 형식으로 변환
    """
    input_path = out_dir / "questions_verified_aggregate.json"
    output_path = Path("data") / "results" / f"{pdf_id}.questions.json"
    
    if not input_path.exists():
        print(f"⚠️ 입력 파일 없음: {input_path}")
        return 0, output_path
    
    data = json.loads(input_path.read_text(encoding="utf-8"))
    
    questions = []
    q_counter = 1
    
    for item in data.get("items", []):
        for q in item.get("questions", []):
            if q.get("verdict") != "OK":
                continue
            
            converted = {
                "question_id": f"q_{q_counter:03d}",
                "type": q["type"],
                "difficulty": q["difficulty"],
                "verdict": q["verdict"],
                "question_text": q.get("question_text") or q.get("question", ""),
                "correct_answer": q.get("correct_answer") or q.get("answer", ""),
                "explanation": q.get("explanation", "")
            }

            if q["type"] == "MCQ":
                options = []
                for choice in q.get("options") or q.get("choices", []):
                    text = choice.split(") ", 1)[1] if ") " in choice else choice
                    options.append(text)
                converted["options"] = options

            # 명세 필드 추가
            if "source_pages" in q:
                converted["source_pages"] = q["source_pages"]
            if "table_refs" in q:
                converted["table_refs"] = q["table_refs"]
            if "confidence" in q:
                converted["confidence"] = q["confidence"]
            if "issues" in q:
                converted["issues"] = q["issues"]

            if "generated_table" in q and q["generated_table"]:
                converted["generated_table"] = q["generated_table"]

            if "evidence" in q and q["evidence"]:
                converted["evidence"] = q["evidence"]

            questions.append(converted)
            q_counter += 1
    
    result = {
        "pdf_id": pdf_id,
        "total_questions": len(questions),
        "questions": questions
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    
    return len(questions), output_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf_id", required=True, help="PDF ID")
    parser.add_argument("--job_id", type=str, default=None, help="Job ID (API 호출 시 사용)")
    parser.add_argument("--num_questions", type=int, default=10, help="생성할 총 문제 개수")
    parser.add_argument("--difficulty", type=str, default="mixed",
                        choices=["easy", "medium", "hard", "mixed"], help="문제 난이도")
    parser.add_argument("--mcq_ratio", type=float, default=1.0, help="MCQ(객관식) 비율 (0.0~1.0)")
    parser.add_argument("--saq_ratio", type=float, default=0.0, help="SAQ(단답형) 비율 (0.0~1.0)")
    parser.add_argument("--no_llm_orchestrate", action="store_true", help="LLM 사용 안함 (통계적 방법)")
    args = parser.parse_args()
    
    base = Path(__file__).parent.parent.parent.parent
    pdf_path = str(base / "data" / "pdfs" / f"{args.pdf_id}.pdf")
    pdf_id = args.pdf_id
    out_dir = base / "artifacts" / pdf_id
    
    print(f"📁 Base path: {base}")
    print(f"📄 PDF path: {pdf_path}")
    print(f"📂 Output dir: {out_dir}")
    
    # 1. Prepare
    run_step("1. PDF 준비", 
        f'python -m backend.engine.core.prepare_runner --pdf_path "{pdf_path}" --pdf_id {pdf_id} --out_dir "{out_dir}"')
    
    # 2. Table Presence
    run_step("2. 표 존재 확인",
        f'python -m backend.engine.core.run_table_presence --out_dir "{out_dir}" --pdf_id {pdf_id}')
    
    # 3. Table Extract
    run_step("3. 표 추출",
        f'python -m backend.engine.core.run_table_extract_mm --out_dir "{out_dir}" --pdf_id {pdf_id}')
    
    # 4. Section Indexer
    run_step("4. 섹션 인덱싱",
        f'python -m backend.engine.core.section_indexer --out_dir "{out_dir}" --pdf_id {pdf_id}')
    
    # 5. Section Packager
    run_step("5. 섹션 패키징",
        f'python -m backend.engine.core.section_context_packager --out_dir "{out_dir}" --pdf_id {pdf_id}')
    
    # ✅ 5.5. Orchestrator (먼저!)
    print("\n" + "="*60)
    print("▶ 5.5. 문제 개수 배분 (Orchestrator)")
    print("="*60)
    allocation = run_orchestrator(
        out_dir=out_dir,
        total_questions=args.num_questions,
        use_llm=not args.no_llm_orchestrate
    )
    
    if not allocation:
        print("❌ Orchestrator 실패!")
        sys.exit(1)
    
    # ✅ 6. Job Builder (allocation 사용)
    run_step("6. Job 빌드",
        f'python -m backend.engine.core.job_builder --out_dir "{out_dir}" --pdf_id {pdf_id} '
        f'--allocation_file "{out_dir}/allocation.json" --overwrite '
        f'--difficulty {args.difficulty} --mcq_ratio {args.mcq_ratio} --saq_ratio {args.saq_ratio}')
    
    # 7. Question Pipeline
    run_step("7. 문제 생성",
        f'python -m backend.engine.core.run_question_pipeline --out_dir "{out_dir}" --pdf_id {pdf_id}')
    
    # 8. API 명세 형식 변환
    print("\n" + "="*60)
    print("▶ 8. API 명세 형식 변환")
    print("="*60)
    q_count, output_path = convert_to_spec(pdf_id, out_dir)
    print(f"✅ 변환 완료: {q_count}개 문제")
    
    print("\n" + "="*60)
    print("🎉 전체 파이프라인 완료!")
    print(f"📁 원본: {out_dir}/questions_verified_aggregate.json")
    print(f"📁 명세: {output_path}")
    print(f"📊 요청: {args.num_questions}개 / 생성: {q_count}개")
    print("="*60)