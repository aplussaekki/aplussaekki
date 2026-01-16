// 화면 3: 로딩/진행률 페이지

import { ProgressDisplay } from "../components";

interface LoadingPageProps {
  jobId: string;
  onComplete?: () => void;
  onError?: (message: string) => void;
}

const LoadingPage = ({ jobId, onComplete, onError }: LoadingPageProps) => {
  return (
    <div className="page loading-page">
      <div className="page-content">
        <div className="loading-container">
          <div className="loading-icon">
            <div className="pulse-ring"></div>
            <span>🧠</span>
          </div>
          <h1>AI가 문제를 생성하고 있습니다</h1>
          <p className="loading-description">
            잠시만 기다려주세요. 보통 1~2분 정도 소요됩니다.
          </p>
          <ProgressDisplay jobId={jobId} onComplete={onComplete} onError={onError} />
        </div>
      </div>
    </div>
  );
};

export default LoadingPage;
