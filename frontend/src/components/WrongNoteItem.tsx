// 오답 아이템 컴포넌트

import { useState } from "react";
import type { WrongQuestionItem } from "../types";
import { formatDate } from "../utils";

interface WrongNoteItemProps {
  item: WrongQuestionItem;
}

const WrongNoteItem = ({ item }: WrongNoteItemProps) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="wrong-note-item">
      {/* 헤더 (클릭하면 펼침/접힘) */}
      <div className="item-header" onClick={() => setExpanded(!expanded)}>
        <div className="question-preview">
          <span className="wrong-count">❌ {item.wrong_count}회</span>
          <p className="question-text">{item.question}</p>
        </div>
        <span className="expand-icon">{expanded ? "▲" : "▼"}</span>
      </div>

      {/* 상세 내용 (펼쳤을 때) */}
      {expanded && (
        <div className="item-details">
          <div className="detail-row">
            <span className="label">내 마지막 답:</span>
            <span className="value incorrect">{item.last_user_answer}</span>
          </div>
          <div className="detail-row">
            <span className="label">정답:</span>
            <span className="value correct">{item.correct_answer}</span>
          </div>
          {item.explanation && (
            <div className="explanation">
              <span className="label">해설:</span>
              <p>{item.explanation}</p>
            </div>
          )}
          <div className="meta">
            <span>마지막 오답: {formatDate(item.last_wrong_at)}</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default WrongNoteItem;
