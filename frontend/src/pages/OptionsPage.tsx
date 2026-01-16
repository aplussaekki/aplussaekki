// 화면 2: 옵션 설정 페이지

import { OptionsForm } from "../components";

interface OptionsPageProps {
  pdfId: string;
  pageCount: number;
  onJobStart?: (jobId: string) => void;
}

const OptionsPage = ({ pdfId, pageCount, onJobStart }: OptionsPageProps) => {
  return (
    <div className="page options-page">
      <div className="page-content">
        <div className="page-header">
          <h1>문제 생성 옵션</h1>
          <p className="page-description">
            생성할 문제의 개수, 난이도, 유형을 설정하세요
          </p>
        </div>

        <div className="pdf-info-card">
          <span className="pdf-icon">📄</span>
          <div className="pdf-details">
            <span className="pdf-id">{pdfId}</span>
            <span className="pdf-pages">{pageCount}페이지</span>
          </div>
        </div>

        <OptionsForm pdfId={pdfId} pageCount={pageCount} onJobStart={onJobStart} />
      </div>
    </div>
  );
};

export default OptionsPage;
