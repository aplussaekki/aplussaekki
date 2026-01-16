"""FastAPI 메인 애플리케이션"""
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드 (backend 디렉토리 기준)
env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=env_path)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import api_router

# API 프리픽스
API_PREFIX = "/api/v1"

app = FastAPI(
    title="Aplus API",
    description="강의안 PDF 기반 문제 생성 API",
    version="1.0.0"
)

# CORS 설정 (프론트엔드 연결용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173", "http://127.0.0.1:5175"],  # Vite 포트
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=API_PREFIX)


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {"message": "Aplus API"}


@app.get("/health")
async def health():
    """헬스 체크"""
    return {"status": "ok"}


