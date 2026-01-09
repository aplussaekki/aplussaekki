"""
API 명세 형식으로 변환
python convert_to_spec.py
"""
import json
from pathlib import Path

def convert_to_spec(input_path: Path, output_path: Path):
    data = json.loads(input_path.read_text(encoding="utf-8"))
    
    questions = []
    q_counter = 1
    
    for item in data.get("items", []):
        for q in item.get("questions", []):
            # verdict가 OK인 것만
            if q.get("verdict") != "OK":
                continue
            
            converted = {
                "question_id": f"q_{q_counter:03d}",
                "type": q["type"],
                "difficulty": q["difficulty"],
                "verdict": q["verdict"],
                "question_text": q["question"],
                "answer": q["answer"],
                "explanation": q["explanation"]
            }
            
            # MCQ만 options 추가
            if q["type"] == "MCQ":
                # "A) 텍스트" → "A"로 변환
                options = []
                for choice in q.get("choices", []):
                    # "A) " 부분 제거
                    text = choice.split(") ", 1)[1] if ") " in choice else choice
                    options.append(text)
                converted["options"] = options
            
            questions.append(converted)
            q_counter += 1
    
    result = {
        "pdf_id": data["pdf_id"],
        "questions": questions
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    
    print(f"✅ 변환 완료!")
    print(f"   입력: {input_path}")
    print(f"   출력: {output_path}")
    print(f"   문제 수: {len(questions)}")

if __name__ == "__main__":
    base = Path(__file__).parent
    
    input_file = base / "artifacts" / "Ch6" / "questions_verified_aggregate.json"
    output_file = base / "data" / "results" / "Ch6.questions.json"
    
    convert_to_spec(input_file, output_file)
