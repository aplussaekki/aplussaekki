"""에러 정의"""
from fastapi import HTTPException, status


class AppError(HTTPException):
    """애플리케이션 기본 에러"""
    pass


class PDFNotFoundError(AppError):
    """PDF를 찾을 수 없음"""
    def __init__(self, pdf_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "PDF_NOT_FOUND",
                "message": f"PDF를 찾을 수 없습니다: {pdf_id}"
            }
        )


class JobNotFoundError(AppError):
    """Job을 찾을 수 없음"""
    def __init__(self, job_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "JOB_NOT_FOUND",
                "message": f"Job을 찾을 수 없습니다: {job_id}"
            }
        )


class LLMError(AppError):
    """LLM 관련 에러"""
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM 오류: {message}"
        )

