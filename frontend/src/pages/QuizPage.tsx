// 화면 4: 문제 풀이 페이지

import { QuizContainer } from "../components";

interface QuizPageProps {
  pdfId: string;
  onComplete?: () => void;
}

const QuizPage = ({ pdfId, onComplete }: QuizPageProps) => {
  return (
    <div className="page quiz-page">
      <div className="page-content">
        <QuizContainer pdfId={pdfId} onComplete={onComplete} />
      </div>
    </div>
  );
};

export default QuizPage;
