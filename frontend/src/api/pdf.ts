// PDF API 호출 함수

import { apiClient } from "./client";
import type {
  PDFUploadResponse,
  QuestionListResponse,
  QuestionGenerationRequest,
  QuestionGenerationResponse,
} from "../types";

export const pdfApi = {
  // 1.1 PDF 업로드
  upload: async (file: File): Promise<PDFUploadResponse> => {
    const formData = new FormData();
    formData.append("file", file);
    return apiClient.postForm<PDFUploadResponse>("/pdfs", formData);
  },

  // 1.2 문제 생성 Job 시작
  startQuestionGeneration: async (
    pdfId: string,
    options: QuestionGenerationRequest
  ): Promise<QuestionGenerationResponse> => {
    return apiClient.post<QuestionGenerationResponse>(
      `/pdfs/${pdfId}/jobs/question-generation`,
      options
    );
  },

  // 1.4 문제 조회
  getQuestions: async (pdfId: string): Promise<QuestionListResponse> => {
    return apiClient.get<QuestionListResponse>(`/pdfs/${pdfId}/questions`);
  },
};
