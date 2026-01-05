"""PDF 서비스"""
from fastapi import UploadFile
from app.storage.pdf_store import PDFStore
from app.models.pdf import PDFStatus
from app.core.errors import PDFNotFoundError
from app.utils.id_generator import generate_pdf_id


class PDFService:
    """PDF 업로드 및 관리 서비스"""
    
    @staticmethod
    async def upload_pdf(file: UploadFile) -> PDFStatus:
        """PDF 업로드"""
        # PDF ID 생성
        pdf_id = generate_pdf_id()
        
        # 파일 읽기
        file_bytes = await file.read()
        if not file_bytes:
            raise ValueError("빈 파일입니다.")
        
        # 저장과 페이지 수 계산을 한 번에 처리
        page_count = PDFStore.save_and_count_pages(pdf_id=pdf_id, pdf_bytes=file_bytes)
        
        # PDFStatus 모델 반환
        return PDFStatus(
            pdf_id=pdf_id,
            status="UPLOADED",
            page_count=page_count
        )
    
    @staticmethod
    def get_pdf_status(pdf_id: str) -> PDFStatus:
        """PDF 상태 조회"""
        status = PDFStore.get_pdf_status(pdf_id)
        if not status:
            raise PDFNotFoundError(pdf_id)
        return status

