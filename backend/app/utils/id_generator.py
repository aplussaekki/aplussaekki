"""ID 생성 유틸리티"""
import secrets


def generate_pdf_id() -> str:
    """PDF ID 생성"""
    # secrets.token_hex(6)은 12자리 hex 문자열 생성 (암호학적으로 안전)
    return f"pdf_{secrets.token_hex(6)}"


def generate_job_id() -> str:
    """Job ID 생성"""
    # secrets.token_hex(4)는 8자리 hex 문자열 생성
    return f"job_{secrets.token_hex(4)}"

