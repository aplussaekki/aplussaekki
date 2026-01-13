// 화면 1: PDF 업로드 페이지

import { PDFUploader } from "../components";

interface UploadPageProps {
  onUploadSuccess?: (pdfId: string, pageCount: number) => void;
}

const UploadPage = ({ onUploadSuccess }: UploadPageProps) => {
  return (
    <div className="page upload-page">
      <div className="page-content">
        <div className="hero-section">
          <h1 className="hero-title">Aplus</h1>
          <p className="hero-subtitle">
            강의안 PDF를 업로드하면
            <br />
            AI가 자동으로 문제를 생성해드립니다
          </p>
        </div>
        <PDFUploader onUploadSuccess={onUploadSuccess} />
      </div>
    </div>
  );
};

export default UploadPage;
