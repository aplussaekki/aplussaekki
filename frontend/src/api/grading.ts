// 채점 API 호출 함수

import { apiClient } from "./client";
import type { GradeRequest, GradeResponse, WrongNoteResponse } from "../types";

export const gradingApi = {
  // 1.5 사용자 답 채점
  gradeAnswer: async (
    pdfId: string,
    questionId: string,
    userAnswer: string
  ): Promise<GradeResponse> => {
    const body: GradeRequest = { user_answer: userAnswer };
    return apiClient.post<GradeResponse>(`/questions/${questionId}/grade`, body, {
      params: { pdf_id: pdfId },
    });
  },

  // 1.6 오답노트 조회
  getWrongNotes: async (): Promise<WrongNoteResponse> => {
    return apiClient.get<WrongNoteResponse>("/users/me/wrong-questions");
  },
};
