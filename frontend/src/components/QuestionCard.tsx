// 문제 카드 컴포넌트 (MCQ/SAQ 지원)

import { useState } from "react";
import type { Question } from "../types";

interface QuestionCardProps {
  question: Question;
  onSubmit: (answer: string) => void;
  disabled?: boolean;
}

const QuestionCard = ({ question, onSubmit, disabled }: QuestionCardProps) => {
  const [selectedOption, setSelectedOption] = useState<string>("");
  const [textAnswer, setTextAnswer] = useState("");

  const handleSubmit = () => {
    const answer = question.type === "MCQ" ? selectedOption : textAnswer;
    if (answer.trim()) {
      onSubmit(answer);
    }
  };

  const isMCQ = question.type === "MCQ";

  return (
    <div className="question-card">
      {/* 문제 유형 뱃지 */}
      <span className={`type-badge ${question.type.toLowerCase()}`}>
        {isMCQ ? "객관식" : "단답형"}
      </span>

      {/* 문제 텍스트 */}
      <p className="question-text">{question.question}</p>

      {/* 답안 입력 영역 */}
      {isMCQ && question.options ? (
        // 객관식: 옵션 선택
        <div className="options-list">
          {question.options.map((option, index) => {
            const optionLabel = String.fromCharCode(65 + index); // A, B, C, D...
            return (
              <label
                key={index}
                className={`option ${selectedOption === optionLabel ? "selected" : ""}`}
              >
                <input
                  type="radio"
                  name={`question-${question.question_id}`}
                  value={optionLabel}
                  checked={selectedOption === optionLabel}
                  onChange={(e) => setSelectedOption(e.target.value)}
                  disabled={disabled}
                />
                <span className="option-label">{optionLabel}.</span>
                <span className="option-text">{option}</span>
              </label>
            );
          })}
        </div>
      ) : (
        // 단답형: 텍스트 입력
        <div className="text-answer">
          <input
            type="text"
            placeholder="답을 입력하세요..."
            value={textAnswer}
            onChange={(e) => setTextAnswer(e.target.value)}
            disabled={disabled}
            onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
          />
        </div>
      )}

      {/* 제출 버튼 */}
      <button
        className="submit-btn"
        onClick={handleSubmit}
        disabled={disabled || (isMCQ ? !selectedOption : !textAnswer.trim())}
      >
        제출
      </button>
    </div>
  );
};

export default QuestionCard;
