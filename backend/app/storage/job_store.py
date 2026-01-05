"""Job 저장소 (파일 기반)"""
import json
from pathlib import Path
from typing import Optional
from app.core.paths import get_job_path
from app.core.errors import JobNotFoundError
from app.models.job import JobStatus, Progress, JobError


class JobStore:
    """Job 저장 및 조회 (JSON 파일 기반)"""
    
    @staticmethod
    def create_job(job_id: str, pdf_id: str) -> JobStatus:
        """Job 생성"""
        job = JobStatus(
            job_id=job_id,
            status="RUNNING",
            progress=Progress(stage="PREPARING", done=0, total=1)
        )
        JobStore._save_job(job)
        return job
    
    @staticmethod
    def update_job_progress(
        job_id: str,
        stage: str,
        done: int,
        total: int
    ) -> JobStatus:
        """Job 진행 상황 업데이트"""
        job = JobStore.get_job(job_id)
        if not job:
            raise JobNotFoundError(job_id)
        
        job.progress = Progress(stage=stage, done=done, total=total)
        JobStore._save_job(job)
        return job
    
    @staticmethod
    def complete_job(job_id: str) -> JobStatus:
        """Job 완료"""
        job = JobStore.get_job(job_id)
        if not job:
            raise JobNotFoundError(job_id)
        
        job.status = "DONE"
        job.progress = None
        JobStore._save_job(job)
        return job
    
    @staticmethod
    def fail_job(job_id: str, error_code: str, error_message: str) -> JobStatus:
        """Job 실패 처리"""
        job = JobStore.get_job(job_id)
        if not job:
            raise JobNotFoundError(job_id)
        
        job.status = "FAILED"
        job.progress = None
        job.error = JobError(code=error_code, message=error_message)
        JobStore._save_job(job)
        return job
    
    @staticmethod
    def get_job(job_id: str) -> Optional[JobStatus]:
        """Job 조회"""
        job_path = get_job_path(job_id)
        if not job_path.exists():
            return None
        
        with open(job_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return JobStatus(**data)
    
    @staticmethod
    def _save_job(job: JobStatus) -> None:
        """Job 저장 (내부 메서드)"""
        job_path = get_job_path(job.job_id)
        job_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Pydantic v2 호환성: model_dump() 우선, 없으면 dict() 사용
        job_data = job.model_dump() if hasattr(job, 'model_dump') else job.dict()
        
        with open(job_path, 'w', encoding='utf-8') as f:
            json.dump(job_data, f, ensure_ascii=False, indent=2)

