"""Job 모델"""
from pydantic import BaseModel
from typing import Literal, Optional


class Progress(BaseModel):
    """진행 상황"""
    stage: str
    done: int
    total: int


class JobError(BaseModel):
    """Job 에러 정보"""
    code: str
    message: str


class JobStatus(BaseModel):
    """Job 상태"""
    job_id: str
    status: Literal["RUNNING", "DONE", "FAILED"]
    progress: Optional[Progress] = None
    error: Optional[JobError] = None

