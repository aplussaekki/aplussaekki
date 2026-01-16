// 진행률 표시 컴포넌트

import { useEffect } from "react";
import { useQuestionGeneration } from "../hooks";

interface ProgressDisplayProps {
  jobId: string;
  onComplete?: () => void;
  onError?: (message: string) => void;
}

// 스테이지 한글 이름
const STAGE_NAMES: Record<string, string> = {
  PARSING: "PDF 분석 중",
  GENERATING: "문제 생성 중",
  VERIFYING: "문제 검증 중",
  SAVING: "저장 중",
};

const ProgressDisplay = ({ jobId, onComplete, onError }: ProgressDisplayProps) => {
  const { status, progressPercent, error, pollStatus } = useQuestionGeneration();

  useEffect(() => {
    pollStatus(jobId)
      .then(() => onComplete?.())
      .catch((e) => onError?.(e.message));
  }, [jobId, pollStatus, onComplete, onError]);

  const stageName = status?.progress?.stage
    ? STAGE_NAMES[status.progress.stage] || status.progress.stage
    : "준비 중";

  return (
    <div className="progress-display">
      {/* 상태 표시 */}
      <div className="status-badge" data-status={status?.status || "QUEUED"}>
        {status?.status || "QUEUED"}
      </div>

      {/* 진행 단계 */}
      <p className="stage-name">{stageName}</p>

      {/* 프로그레스 바 */}
      <div className="progress-bar">
        <div
          className="progress-fill"
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      {/* 진행률 텍스트 */}
      {status?.progress && (
        <p className="progress-text">
          {status.progress.done} / {status.progress.total} ({progressPercent}%)
        </p>
      )}

      {/* 에러 메시지 */}
      {error && (
        <div className="error-box">
          <p>❌ 오류 발생</p>
          <p>{error}</p>
        </div>
      )}
    </div>
  );
};

export default ProgressDisplay;

