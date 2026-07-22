from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.modules.questions.models import Answer, HelpfulVote, Question


class QuestionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, question: Question) -> Question:
        self.db.add(question)
        self.db.flush()
        return question

    def get(self, question_id: str) -> Question | None:
        return (
            self.db.query(Question)
            .options(joinedload(Question.student), joinedload(Question.answers))
            .filter(Question.id == question_id, Question.is_deleted.is_(False))
            .first()
        )

    def feed(self, page: int, page_size: int, subject_id: str | None = None, search: str | None = None):
        query = self.db.query(Question).filter(Question.is_deleted.is_(False))
        if subject_id:
            query = query.filter(Question.subject_id == subject_id)
        if search:
            query = query.filter(or_(Question.title.ilike(f"%{search}%"), Question.body.ilike(f"%{search}%")))
        query = query.order_by(Question.created_at.desc())
        total = query.order_by(None).with_entities(func.count()).scalar() or 0
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def trending(self, limit: int = 10):
        return (
            self.db.query(Question)
            .filter(Question.is_deleted.is_(False))
            .order_by(Question.view_count.desc())
            .limit(limit)
            .all()
        )

    def create_answer(self, answer: Answer) -> Answer:
        self.db.add(answer)
        self.db.flush()
        return answer

    def get_answer(self, answer_id: str) -> Answer | None:
        return self.db.query(Answer).filter(Answer.id == answer_id, Answer.is_deleted.is_(False)).first()

    def get_helpful_vote(self, answer_id: str, user_id: str) -> HelpfulVote | None:
        return (
            self.db.query(HelpfulVote)
            .filter(HelpfulVote.answer_id == answer_id, HelpfulVote.user_id == user_id)
            .first()
        )

    def add_helpful_vote(self, vote: HelpfulVote) -> None:
        self.db.add(vote)

    def commit(self):
        self.db.commit()
