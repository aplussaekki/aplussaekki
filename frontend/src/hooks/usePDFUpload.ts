// PDF 업로드 관련 커스텀 훅

import { useState, useCallback } from "react";
import type { PDFUploadResponse } from "../types";
import { pdfApi } from "../api";

export const usePDFUpload = () => {
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<PDFUploadResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const uploadPDF = useCallback(async (file: File): Promise<PDFUploadResponse> => {
    // 파일 검증
    if (!file.type.includes("pdf") && !file.name.toLowerCase().endsWith(".pdf")) {
      const err = "PDF 파일만 업로드할 수 있습니다.";
      setError(err);
      throw new Error(err);
    }

    setUploading(true);
    setError(null);
    try {
      const result = await pdfApi.upload(file);
      setUploadResult(result);
      return result;
    } catch (e) {
      const message = e instanceof Error ? e.message : "업로드 실패";
      setError(message);
      throw e;
    } finally {
      setUploading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setUploadResult(null);
    setError(null);
  }, []);

  return {
    uploading,
    uploadResult,
    error,
    uploadPDF,
    reset,
  };
};
