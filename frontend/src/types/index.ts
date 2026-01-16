// 백엔드 API 명세서에 맞춘 타입 정의

// ============================================
// 공통 ENUM
// ============================================

// 문제 유형
export type QuestionType = "MCQ" | "SAQ";

// 난이도
export type Difficulty = "easy" | "medium" | "hard" | "mixed";

// 문제 심사 상태
export type Verdict = "OK" | "FIXABLE" | "REJECT";

// Job 상태
export type JobStatusType = "QUEUED" | "RUNNING" | "DONE" | "FAILED";

// Job 진행 단계
export type JobStage = "PARSING" | "GENERATING" | "VERIFYING" | "SAVING";

// ============================================
// 공통 에러 응답
// ============================================
export interface ApiError {
  error: string;
  message: string;
}

// ============================================
// 1.1 PDF 업로드
// ============================================
export interface PDFUploadResponse {
  pdf_id: string;
  status: "UPLOADED";
  page_count: number;
}

// ============================================
// 1.2 문제 생성 Job 시작
// ============================================
export interface QuestionGenerationRequest {
  num_questions: number;
  difficulty: Difficulty;
  types_ratio: {
    MCQ: number;
    SAQ: number;
  };
  chunking: {
    mode: "whole" | "chunked";
    pages_per_chunk?: number; // chunked 모드일 때 필수
  };
}

export interface QuestionGenerationResponse {
  job_id: string;
  pdf_id: string;
  status: "QUEUED";
}

// ============================================
// 1.3 Job 상태 조회
// ============================================
export interface JobProgress {
  stage: JobStage;
  done: number;
  total: number;
}

export interface JobError {
  code: string;
  message: string;
}

export interface JobStatusResponse {
  job_id: string;
  status: JobStatusType;
  progress?: JobProgress;
  error?: JobError;
}

// ============================================
// 1.4 문제 조회
// ============================================
export interface Question {
  question_id: string;
  type: QuestionType;
  question: string;
  options?: string[]; // MCQ인 경우에만
  source?: string; // optional
}

export interface QuestionListResponse {
  items: Question[];
}

// ============================================
// 1.5 사용자 답 채점
// ============================================
export interface GradeRequest {
  user_answer: string;
}

export interface GradeResponse {
  question_id: string;
  type: QuestionType;
  is_correct: boolean;
  score: number;
  user_answer: string;
  correct_answer: string;
  feedback: string;
  graded_at: string; // ISO 8601
}

// ============================================
// 1.6 오답노트 조회
// ============================================
export interface WrongQuestionItem {
  question_id: string;
  question: string;
  last_user_answer: string;
  correct_answer: string;
  explanation: string;
  wrong_count: number;
  last_wrong_at: string; // ISO 8601
}

export interface WrongNoteResponse {
  user_id: string;
  items: WrongQuestionItem[];
  total: number;
}

// ============================================
// 프론트엔드 전용 타입
// ============================================

// 옵션 설정 폼 상태
export interface QuestionOptions {
  numQuestions: number;
  difficulty: Difficulty;
  mcqRatio: number; // 0~1, SAQ는 자동 계산
  chunkingMode: "whole" | "chunked";
  pagesPerChunk: number;
}

// 퀴즈 진행 상태
export interface QuizState {
  pdfId: string;
  questions: Question[];
  currentIndex: number;
  answers: Record<string, string>; // question_id -> user_answer
  results: Record<string, GradeResponse>; // question_id -> result
}
