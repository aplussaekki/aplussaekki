// PDF 업로드 컴포넌트

import { useRef, useState, type DragEvent } from "react";
import { usePDFUpload } from "../hooks";

interface PDFUploaderProps {
  onUploadSuccess?: (pdfId: string, pageCount: number) => void;
}

const PDFUploader = ({ onUploadSuccess }: PDFUploaderProps) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const { uploading, uploadResult, error, uploadPDF, reset } = usePDFUpload();

  const handleFileSelect = async (file: File) => {
    try {
      const result = await uploadPDF(file);
      onUploadSuccess?.(result.pdf_id, result.page_count);
    } catch {
      // 에러는 hook에서 처리됨
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFileSelect(file);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFileSelect(file);
  };

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  return (
    <div className="pdf-uploader">
      {/* 드래그 앤 드롭 영역 */}
      <div
        className={`drop-zone ${isDragging ? "dragging" : ""} ${uploading ? "uploading" : ""}`}
        onClick={() => fileInputRef.current?.click()}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,application/pdf"
          onChange={handleInputChange}
          hidden
        />

        {uploading ? (
          <div className="uploading-state">
            <div className="spinner" />
            <p>업로드 중...</p>
          </div>
        ) : uploadResult ? (
          <div className="success-state">
            <p>✅ 업로드 완료!</p>
            <p>PDF ID: {uploadResult.pdf_id}</p>
            <p>페이지 수: {uploadResult.page_count}</p>
            <button onClick={(e) => { e.stopPropagation(); reset(); }}>
              다른 파일 업로드
            </button>
          </div>
        ) : (
          <div className="default-state">
            <p>📄</p>
            <p>PDF 파일을 드래그하거나 클릭하여 업로드</p>
          </div>
        )}
      </div>

      {/* 에러 메시지 */}
      {error && <p className="error-message">❌ {error}</p>}
    </div>
  );
};

export default PDFUploader;
