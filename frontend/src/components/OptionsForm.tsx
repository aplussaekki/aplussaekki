// 옵션 설정 폼 컴포넌트

import { useState } from "react";
import type { QuestionOptions, Difficulty } from "../types";
import { useQuestionGeneration, DEFAULT_OPTIONS } from "../hooks";

interface OptionsFormProps {
  pdfId: string;
  pageCount: number;
  onJobStart?: (jobId: string) => void;
}

const OptionsForm = ({ pdfId, pageCount, onJobStart }: OptionsFormProps) => {
  const [options, setOptions] = useState<QuestionOptions>(DEFAULT_OPTIONS);
  const { loading, error, startGeneration } = useQuestionGeneration();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const result = await startGeneration(pdfId, options);
      onJobStart?.(result.job_id);
    } catch {
      // 에러는 hook에서 처리됨
    }
  };

  const updateOption = <K extends keyof QuestionOptions>(
    key: K,
    value: QuestionOptions[K]
  ) => {
    setOptions((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <form className="options-form" onSubmit={handleSubmit}>
      {/* 문제 개수 */}
      <div className="form-group">
        <label htmlFor="numQuestions">문제 개수</label>
        <input
          id="numQuestions"
          type="number"
          min={1}
          max={50}
          value={options.numQuestions}
          onChange={(e) => updateOption("numQuestions", Number(e.target.value))}
        />
      </div>

      {/* 난이도 */}
      <div className="form-group">
        <label htmlFor="difficulty">난이도</label>
        <select
          id="difficulty"
          value={options.difficulty}
          onChange={(e) => updateOption("difficulty", e.target.value as Difficulty)}
        >
          <option value="easy">쉬움</option>
          <option value="medium">보통</option>
          <option value="hard">어려움</option>
          <option value="mixed">혼합</option>
        </select>
      </div>

      {/* 객관식 비율 */}
      <div className="form-group">
        <label htmlFor="mcqRatio">
          객관식 비율: {Math.round(options.mcqRatio * 100)}%
        </label>
        <input
          id="mcqRatio"
          type="range"
          min={0}
          max={1}
          step={0.1}
          value={options.mcqRatio}
          onChange={(e) => updateOption("mcqRatio", Number(e.target.value))}
        />
        <div className="ratio-display">
          <span>MCQ: {Math.round(options.mcqRatio * 100)}%</span>
          <span>SAQ: {Math.round((1 - options.mcqRatio) * 100)}%</span>
        </div>
      </div>

      {/* 청킹 모드 */}
      <div className="form-group">
        <label htmlFor="chunkingMode">PDF 처리 방식</label>
        <select
          id="chunkingMode"
          value={options.chunkingMode}
          onChange={(e) =>
            updateOption("chunkingMode", e.target.value as "whole" | "chunked")
          }
        >
          <option value="whole">전체 한번에</option>
          <option value="chunked">페이지 분할</option>
        </select>
      </div>

      {/* 페이지당 분할 수 (chunked 모드일 때만) */}
      {options.chunkingMode === "chunked" && (
        <div className="form-group">
          <label htmlFor="pagesPerChunk">
            분할 단위 (페이지 수, 전체: {pageCount}페이지)
          </label>
          <input
            id="pagesPerChunk"
            type="number"
            min={1}
            max={pageCount}
            value={options.pagesPerChunk}
            onChange={(e) =>
              updateOption("pagesPerChunk", Number(e.target.value))
            }
          />
        </div>
      )}

      {/* 에러 메시지 */}
      {error && <p className="error-message">❌ {error}</p>}

      {/* 제출 버튼 */}
      <button type="submit" disabled={loading} className="submit-btn">
        {loading ? "시작 중..." : "문제 생성 시작"}
      </button>
    </form>
  );
};

export default OptionsForm;

