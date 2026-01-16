// 화면 5: 오답노트 페이지

import { WrongNotesList } from "../components";

const WrongNotesPage = () => {
  return (
    <div className="page wrong-notes-page">
      <div className="page-content">
        <div className="page-header">
          <h1>📝 오답노트</h1>
          <p className="page-description">
            틀린 문제를 복습하고 실력을 향상시키세요
          </p>
        </div>
        <WrongNotesList />
      </div>
    </div>
  );
};

export default WrongNotesPage;
