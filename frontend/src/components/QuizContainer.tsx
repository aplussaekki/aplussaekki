// 퀴즈 컨테이너 컴포넌트

import { useEffect } from "react";
import { useQuiz } from "../hooks";
import QuestionCard from "./QuestionCard";
import AnswerResult from "./AnswerResult";

interface QuizContainerProps {
  pdfId: string;
  onComplete?: () => void;
}

const QuizContainer = ({ pdfId, onComplete }: QuizContainerProps) => {
  const {
    questions,
    currentIndex,
    currentQuestion,
    currentResult,
    loading,
    error,
    totalAnswered,
    totalQuestions,
    correctCount,
    accuracy,
    loadQuestions,
    submitAnswer,
    nextQuestion,
    prevQuestion,
  } = useQuiz();

  useEffect(() => {
    loadQuestions(pdfId);
  }, [pdfId, loadQuestions]);

  // 모든 문제를 풀었을 때
  const isComplete = totalAnswered === totalQuestions && totalQuestions > 0;

  if (loading && questions.length === 0) {
    return <div className="loading">문제를 불러오는 중...</div>;
  }

  if (error) {
    return <div className="error">❌ {error}</div>;
  }

  if (questions.length === 0) {
    return <div className="empty">생성된 문제가 없습니다.</div>;
  }

  return (
    <div className="quiz-container">
      {/* 상단 정보 */}
      <div className="quiz-header">
        <span className="progress">
          {currentIndex + 1} / {totalQuestions}
        </span>
        <span className="score">
          정답: {correctCount} | 정답률: {accuracy.toFixed(0)}%
        </span>
      </div>

      {/* 문제 카드 */}
      {currentQuestion && (
        <QuestionCard
          question={currentQuestion}
          onSubmit={submitAnswer}
          disabled={loading || !!currentResult}
        />
      )}

      {/* 채점 결과 */}
      {currentResult && <AnswerResult result={currentResult} />}

      {/* 네비게이션 */}
      <div className="quiz-nav">
        <button onClick={prevQuestion} disabled={currentIndex === 0}>
          ← 이전
        </button>

        {currentResult ? (
          currentIndex < totalQuestions - 1 ? (
            <button onClick={nextQuestion}>다음 →</button>
          ) : (
            <button onClick={onComplete} className="complete-btn">
              결과 보기
            </button>
          )
        ) : null}
      </div>

      {/* 완료 상태 */}
      {isComplete && (
        <div className="quiz-complete">
          <h3>🎉 모든 문제를 풀었습니다!</h3>
          <p>
            총 {totalQuestions}문제 중 {correctCount}문제 정답
          </p>
          <p>정답률: {accuracy.toFixed(1)}%</p>
        </div>
      )}
    </div>
  );
};

export default QuizContainer;

