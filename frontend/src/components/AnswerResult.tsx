// 채점 결과 컴포넌트

import type { GradeResponse } from "../types";

interface AnswerResultProps {
  result: GradeResponse;
}

const AnswerResult = ({ result }: AnswerResultProps) => {
  const { is_correct, user_answer, correct_answer, feedback, score } = result;

  return (
    <div className={`answer-result ${is_correct ? "correct" : "incorrect"}`}>
      {/* 정답/오답 표시 */}
      <div className="result-header">
        <span className="result-icon">{is_correct ? "✅" : "❌"}</span>
        <span className="result-text">
          {is_correct ? "정답입니다!" : "오답입니다"}
        </span>
        <span className="score">+{score}점</span>
      </div>

      {/* 상세 정보 */}
      <div className="result-details">
        <div className="detail-row">
          <span className="label">내 답:</span>
          <span className="value">{user_answer}</span>
        </div>
        {!is_correct && (
          <div className="detail-row">
            <span className="label">정답:</span>
            <span className="value correct-answer">{correct_answer}</span>
          </div>
        )}
      </div>

      {/* 피드백 */}
      <p className="feedback">{feedback}</p>
    </div>
  );
};

export default AnswerResult;
