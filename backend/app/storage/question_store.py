"""문제 저장소"""
import json
from pathlib import Path
from typing import Optional, List
from app.core.paths import get_questions_path
from app.models.question import Question


class QuestionStore:
    """문제 저장 및 조회"""
    
    @staticmethod
    def save_questions(pdf_id: str, questions: List[Question]) -> Path:
        """문제 목록 저장"""
        questions_path = get_questions_path(pdf_id)
        questions_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Pydantic 모델을 dict로 변환 (v2 호환성)
        questions_data = []
        for q in questions:
            if hasattr(q, 'model_dump'):
                questions_data.append(q.model_dump())
            elif hasattr(q, 'dict'):
                questions_data.append(q.dict())
            else:
                questions_data.append(q)
        
        with open(questions_path, 'w', encoding='utf-8') as f:
            json.dump({"items": questions_data}, f, ensure_ascii=False, indent=2)
        
        return questions_path
    
    @staticmethod
    def load_questions(pdf_id: str) -> Optional[List[dict]]:
        """문제 목록 로드"""
        questions_path = get_questions_path(pdf_id)
        if not questions_path.exists():
            return None
        
        with open(questions_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("items", [])

