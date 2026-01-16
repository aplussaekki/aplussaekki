// 오답노트 목록 컴포넌트

import { useEffect, useState } from "react";
import { useWrongNotes } from "../hooks";
import WrongNoteItem from "./WrongNoteItem";

type SortMode = "wrong_count" | "recent";

const WrongNotesList = () => {
  const { items, total, loading, error, sortedByWrongCount, sortedByRecent, loadWrongNotes } =
    useWrongNotes();
  const [sortMode, setSortMode] = useState<SortMode>("recent");

  useEffect(() => {
    loadWrongNotes();
  }, [loadWrongNotes]);

  const displayItems = sortMode === "wrong_count" ? sortedByWrongCount : sortedByRecent;

  if (loading) {
    return <div className="loading">오답노트를 불러오는 중...</div>;
  }

  if (error) {
    return <div className="error">❌ {error}</div>;
  }

  if (items.length === 0) {
    return (
      <div className="empty-state">
        <p>📝</p>
        <p>아직 틀린 문제가 없습니다.</p>
        <p>문제를 풀고 오답노트를 확인해보세요!</p>
      </div>
    );
  }

  return (
    <div className="wrong-notes-list">
      {/* 헤더 */}
      <div className="list-header">
        <span className="total">총 {total}개의 오답</span>

        {/* 정렬 옵션 */}
        <div className="sort-options">
          <button
            className={sortMode === "recent" ? "active" : ""}
            onClick={() => setSortMode("recent")}
          >
            최근 순
          </button>
          <button
            className={sortMode === "wrong_count" ? "active" : ""}
            onClick={() => setSortMode("wrong_count")}
          >
            오답 횟수 순
          </button>
        </div>
      </div>

      {/* 오답 목록 */}
      <div className="items-container">
        {displayItems.map((item) => (
          <WrongNoteItem key={item.question_id} item={item} />
        ))}
      </div>
    </div>
  );
};

export default WrongNotesList;

