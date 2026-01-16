// 오답노트 관련 커스텀 훅

import { useState, useCallback } from "react";
import type { WrongQuestionItem } from "../types";
import { gradingApi } from "../api";

export const useWrongNotes = () => {
  const [items, setItems] = useState<WrongQuestionItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 오답노트 로드
  const loadWrongNotes = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await gradingApi.getWrongNotes();
      setItems(response.items);
      setTotal(response.total);
    } catch (e) {
      const message = e instanceof Error ? e.message : "오답노트 로드 실패";
      setError(message);
      throw e;
    } finally {
      setLoading(false);
    }
  }, []);

  // 오답 횟수로 정렬 (많은 순)
  const sortedByWrongCount = [...items].sort(
    (a, b) => b.wrong_count - a.wrong_count
  );

  // 최근 틀린 순으로 정렬
  const sortedByRecent = [...items].sort(
    (a, b) =>
      new Date(b.last_wrong_at).getTime() - new Date(a.last_wrong_at).getTime()
  );

  return {
    items,
    total,
    loading,
    error,
    sortedByWrongCount,
    sortedByRecent,
    loadWrongNotes,
  };
};
