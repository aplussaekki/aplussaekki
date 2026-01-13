// 퀴즈 관련 커스텀 훅

import { useState, useCallback } from "react";
import type { Question, GradeResponse } from "../types";
import { pdfApi, gradingApi } from "../api";

export const useQuiz = () => {
  const [pdfId, setPdfId] = useState<string | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [results, setResults] = useState<Record<string, GradeResponse>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 문제 목록 로드
  const loadQuestions = useCallback(async (targetPdfId: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await pdfApi.getQuestions(targetPdfId);
      setPdfId(targetPdfId);
      setQuestions(response.items);
      setCurrentIndex(0);
      setResults({});
    } catch (e) {
      const message = e instanceof Error ? e.message : "문제 로드 실패";
      setError(message);
      throw e;
    } finally {
      setLoading(false);
    }
  }, []);

  // 답안 제출 및 채점
  const submitAnswer = useCallback(
    async (answer: string): Promise<GradeResponse> => {
      const question = questions[currentIndex];
      if (!question) throw new Error("현재 문제가 없습니다");

      if (!pdfId) throw new Error("PDF ID가 없습니다");

      setLoading(true);
      setError(null);
      try {
        const result = await gradingApi.gradeAnswer(pdfId, question.question_id, answer);
        setResults((prev) => ({
          ...prev,
          [question.question_id]: result,
        }));
        return result;
      } catch (e) {
        const message = e instanceof Error ? e.message : "채점 실패";
        setError(message);
        throw e;
      } finally {
        setLoading(false);
      }
    },
    [pdfId, questions, currentIndex]
  );

  // 다음 문제로 이동
  const nextQuestion = useCallback(() => {
    if (currentIndex < questions.length - 1) {
      setCurrentIndex((prev) => prev + 1);
    }
  }, [currentIndex, questions.length]);

  // 이전 문제로 이동
  const prevQuestion = useCallback(() => {
    if (currentIndex > 0) {
      setCurrentIndex((prev) => prev - 1);
    }
  }, [currentIndex]);

  // 특정 문제로 이동
  const goToQuestion = useCallback(
    (index: number) => {
      if (index >= 0 && index < questions.length) {
        setCurrentIndex(index);
      }
    },
    [questions.length]
  );

  // 현재 문제
  const currentQuestion = questions[currentIndex] || null;

  // 현재 문제의 채점 결과
  const currentResult = currentQuestion
    ? results[currentQuestion.question_id]
    : null;

  // 전체 진행률
  const totalAnswered = Object.keys(results).length;
  const totalQuestions = questions.length;

  // 정답률 계산
  const correctCount = Object.values(results).filter((r) => r.is_correct).length;
  const accuracy = totalAnswered > 0 ? (correctCount / totalAnswered) * 100 : 0;

  return {
    pdfId,
    questions,
    currentIndex,
    currentQuestion,
    currentResult,
    results,
    loading,
    error,
    totalAnswered,
    totalQuestions,
    correctCount,
    accuracy,
    loadQuestions,
    submitAnswer,
    nextQuestion,
    prevQuestion,
    goToQuestion,
  };
};
