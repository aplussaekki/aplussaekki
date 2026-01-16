// 메인 앱 - 라우팅 및 상태 관리

import { useState } from "react";
import { BrowserRouter, Routes, Route, useNavigate } from "react-router-dom";
import {
  UploadPage,
  OptionsPage,
  LoadingPage,
  QuizPage,
  WrongNotesPage,
} from "./pages";
import "./App.css";

// 앱 상태 타입
interface AppState {
  pdfId: string | null;
  pageCount: number;
  jobId: string | null;
}

// 메인 앱 내용 (라우터 내부)
function AppContent() {
  const navigate = useNavigate();
  const [state, setState] = useState<AppState>({
    pdfId: null,
    pageCount: 0,
    jobId: null,
  });

  // PDF 업로드 성공 시
  const handleUploadSuccess = (pdfId: string, pageCount: number) => {
    setState((prev) => ({ ...prev, pdfId, pageCount }));
    navigate("/options");
  };

  // 문제 생성 Job 시작 시
  const handleJobStart = (jobId: string) => {
    setState((prev) => ({ ...prev, jobId }));
    navigate("/loading");
  };

  // 문제 생성 완료 시
  const handleGenerationComplete = () => {
    navigate("/quiz");
  };

  // 에러 발생 시
  const handleError = (message: string) => {
    alert(`오류 발생: ${message}`);
    navigate("/");
  };

  // 퀴즈 완료 시
  const handleQuizComplete = () => {
    navigate("/wrong-notes");
  };

  return (
    <div className="app">
      {/* 헤더 */}
      <header className="app-header">
        <h1 onClick={() => navigate("/")}>Aplus</h1>
        <nav>
          <button onClick={() => navigate("/")}>홈</button>
          <button onClick={() => navigate("/wrong-notes")}>오답노트</button>
        </nav>
      </header>

      {/* 메인 콘텐츠 */}
      <main className="app-main">
        <Routes>
          {/* 화면 1: PDF 업로드 */}
          <Route
            path="/"
            element={<UploadPage onUploadSuccess={handleUploadSuccess} />}
          />

          {/* 화면 2: 옵션 설정 */}
          <Route
            path="/options"
            element={
              state.pdfId ? (
                <OptionsPage
                  pdfId={state.pdfId}
                  pageCount={state.pageCount}
                  onJobStart={handleJobStart}
                />
              ) : (
                <UploadPage onUploadSuccess={handleUploadSuccess} />
              )
            }
          />

          {/* 화면 3: 로딩/진행률 */}
          <Route
            path="/loading"
            element={
              state.jobId ? (
                <LoadingPage
                  jobId={state.jobId}
                  onComplete={handleGenerationComplete}
                  onError={handleError}
                />
              ) : (
                <UploadPage onUploadSuccess={handleUploadSuccess} />
              )
            }
          />

          {/* 화면 4: 문제 풀이 */}
          <Route
            path="/quiz"
            element={
              state.pdfId ? (
                <QuizPage pdfId={state.pdfId} onComplete={handleQuizComplete} />
              ) : (
                <UploadPage onUploadSuccess={handleUploadSuccess} />
              )
            }
          />

          {/* 화면 5: 오답노트 */}
          <Route path="/wrong-notes" element={<WrongNotesPage />} />
        </Routes>
      </main>

      {/* 푸터 */}
      <footer className="app-footer">
        <p>© 2025 Aplus - 강의안 기반 문제 생성 서비스</p>
      </footer>
    </div>
  );
}

// 앱 루트
function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}

export default App;
