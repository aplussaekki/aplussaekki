"""PDF 저장소"""
import os
import tempfile
from pathlib import Path
from typing import Optional
from app.core.paths import get_pdf_path, PDF_DIR
from app.core.errors import PDFNotFoundError
from app.models.pdf import PDFStatus
import pypdf


class PDFStore:
    """PDF 저장 및 조회"""
    
    @staticmethod
    def save_pdf(file_content: bytes, pdf_id: str) -> Path:
        """PDF 파일 저장"""
        pdf_path = get_pdf_path(pdf_id)
        pdf_path.write_bytes(file_content)
        return pdf_path
    
    @staticmethod
    def save_and_count_pages(pdf_id: str, pdf_bytes: bytes) -> int:
        """
        PDF 저장과 페이지 수 계산을 한 번에 처리
        - 원자적 저장(깨짐 방지): 임시 파일에 쓰고 검증 후 rename
        """
        final_path = get_pdf_path(pdf_id)
        tmp_path = None

        try:
            # 1) 임시 파일 작성
            with tempfile.NamedTemporaryFile(delete=False, dir=str(PDF_DIR), suffix=".tmp") as tmp:
                tmp.write(pdf_bytes)
                tmp_path = Path(tmp.name)

            # 2) PDF 파싱해서 페이지 수 구하기
            reader = pypdf.PdfReader(str(tmp_path))
            page_count = len(reader.pages)

            if page_count <= 0:
                raise ValueError("페이지 수를 확인할 수 없습니다.")

            # 3) 최종 파일로 원자적 이동
            os.replace(str(tmp_path), str(final_path))
            tmp_path = None  # 성공했으므로 삭제하지 않음

            return page_count

        except Exception as e:
            # 실패하면 tmp 삭제
            if tmp_path and tmp_path.exists():
                try:
                    tmp_path.unlink()
                except Exception:
                    pass
            # PDF 손상/파싱 오류 등은 ValueError로 변환
            if isinstance(e, ValueError):
                raise
            raise ValueError("PDF를 열 수 없습니다. 파일이 손상되었거나 비정상 형식입니다.") from e
    
    @staticmethod
    def get_page_count(pdf_path: Path) -> int:
        """PDF 페이지 수 조회"""
        try:
            with open(pdf_path, 'rb') as f:
                reader = pypdf.PdfReader(f)
                page_count = len(reader.pages)
                if page_count == 0:
                    raise ValueError("PDF 파일에 페이지가 없습니다.")
                return page_count
        except Exception as e:
            # pypdf의 다양한 에러 타입을 ValueError로 변환
            if isinstance(e, ValueError):
                raise
            raise ValueError(f"PDF 파일을 읽을 수 없습니다: {str(e)}")
    
    @staticmethod
    def get_pdf_status(pdf_id: str) -> Optional[PDFStatus]:
        """PDF 상태 조회"""
        pdf_path = get_pdf_path(pdf_id)
        if not pdf_path.exists():
            return None
        
        page_count = PDFStore.get_page_count(pdf_path)
        return PDFStatus(
            pdf_id=pdf_id,
            status="UPLOADED",
            page_count=page_count
        )
    
    @staticmethod
    def pdf_exists(pdf_id: str) -> bool:
        """PDF 존재 여부 확인"""
        return get_pdf_path(pdf_id).exists()

