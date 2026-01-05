"""Job API"""
from fastapi import APIRouter
from app.services.job_service import JobService
from app.models.job import JobStatus

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """
    Job 상태 조회 (폴링)
    
    - **job_id**: Job ID
    """
    return JobService.get_job_status(job_id)

