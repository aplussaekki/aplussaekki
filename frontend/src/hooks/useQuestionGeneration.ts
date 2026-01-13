// 문제 생성 Job 관련 커스텀 훅

import { useState, useCallback } from "react";
import type {
  QuestionGenerationRequest,
  QuestionGenerationResponse,
  JobStatusResponse,
  QuestionOptions,
} from "../types";
import { pdfApi, jobApi } from "../api";

// 기본 옵션 값
export const DEFAULT_OPTIONS: QuestionOptions = {
  numQuestions: 10,
  difficulty: "mixed",
  mcqRatio: 0.7,
  chunkingMode: "chunked",
  pagesPerChunk: 10,
};

// QuestionOptions -> API Request 변환
const toApiRequest = (options: QuestionOptions): QuestionGenerationRequest => ({
  num_questions: options.numQuestions,
  difficulty: options.difficulty,
  types_ratio: {
    MCQ: options.mcqRatio,
    SAQ: 1 - options.mcqRatio,
  },
  chunking: {
    mode: options.chunkingMode,
    pages_per_chunk: options.pagesPerChunk,
  },
});

export const useQuestionGeneration = () => {
  const [jobId, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState<JobStatusResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 문제 생성 시작
  const startGeneration = useCallback(
    async (
      pdfId: string,
      options: QuestionOptions = DEFAULT_OPTIONS
    ): Promise<QuestionGenerationResponse> => {
      setLoading(true);
      setError(null);
      try {
        const response = await pdfApi.startQuestionGeneration(
          pdfId,
          toApiRequest(options)
        );
        setJobId(response.job_id);
        return response;
      } catch (e) {
        const message = e instanceof Error ? e.message : "문제 생성 시작 실패";
        setError(message);
        throw e;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  // Job 상태 폴링 (진행률 업데이트)
  const pollStatus = useCallback(
    async (targetJobId?: string): Promise<JobStatusResponse> => {
      const id = targetJobId || jobId;
      if (!id) throw new Error("Job ID가 없습니다");

      setLoading(true);
      setError(null);
      try {
        const result = await jobApi.pollUntilDone(id, (s) => setStatus(s));
        setStatus(result);
        return result;
      } catch (e) {
        const message = e instanceof Error ? e.message : "Job 폴링 실패";
        setError(message);
        throw e;
      } finally {
        setLoading(false);
      }
    },
    [jobId]
  );

  // 진행률 퍼센트 계산
  const progressPercent =
    status?.progress && status.progress.total > 0
      ? Math.round((status.progress.done / status.progress.total) * 100)
      : 0;

  return {
    jobId,
    status,
    loading,
    error,
    progressPercent,
    startGeneration,
    pollStatus,
  };
};

