// Job API 호출 함수

import { apiClient } from "./client";
import type { JobStatusResponse } from "../types";

export const jobApi = {
  // 1.3 Job 상태 조회 (폴링)
  getStatus: async (jobId: string): Promise<JobStatusResponse> => {
    return apiClient.get<JobStatusResponse>(`/jobs/${jobId}`);
  },

  // Job 상태 폴링 유틸리티
  pollUntilDone: async (
    jobId: string,
    onProgress?: (status: JobStatusResponse) => void,
    intervalMs: number = 2000
  ): Promise<JobStatusResponse> => {
    return new Promise((resolve, reject) => {
      const poll = async () => {
        try {
          const status = await jobApi.getStatus(jobId);
          onProgress?.(status);

          if (status.status === "DONE") {
            resolve(status);
          } else if (status.status === "FAILED") {
            reject(new Error(status.error?.message || "Job failed"));
          } else {
            setTimeout(poll, intervalMs);
          }
        } catch (error) {
          reject(error);
        }
      };
      poll();
    });
  },
};
