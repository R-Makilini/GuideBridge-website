from sqlalchemy.orm import Session

from app.core.constants import BookmarkTargetType, NotificationType, QuestionVisibility, UserRole
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.core.pagination import PageMeta
from app.modules.notifications.service import NotificationService
from app.modules.questions.models import Answer, HelpfulVote, Question
from app.modules.questions.repository import QuestionRepository
from app.modules.questions.schemas import AnswerCreate, AnswerUpdate, QuestionCreate, QuestionOut, QuestionUpdate


class QuestionService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = QuestionRepository(db)
        self.notifications = NotificationService(db)

    def _to_out(self, q: Question) -> QuestionOut:
        return QuestionOut(
            id=q.id,
            title=q.title,
            body=q.body,
            subject_id=q.subject_id,
            visibility=q.visibility,
            view_count=q.view_count,
            author_name=q.public_author_name(),
            created_at=q.created_at,
        )

    def create_question(self, student_id: str, payload: QuestionCreate) -> QuestionOut:
        question = Question(
            student_id=student_id,
            subject_id=payload.subject_id,
            title=payload.title,
            body=payload.body,
            visibility=payload.visibility,
        )
        self.repo.create(question)
        self.repo.commit()
        return self._to_out(question)

    def update_question(self, student_id: str, question_id: str, payload: QuestionUpdate) -> QuestionOut:
        question = self.repo.get(question_id)
        if not question:
            raise NotFoundError("Question not found.")
        if question.student_id != student_id:
            raise ForbiddenError("You can only edit your own questions.")
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(question, field, value)
        self.db.add(question)
        self.repo.commit()
        return self._to_out(question)

    def delete_question(self, student_id: str, question_id: str) -> None:
        question = self.repo.get(question_id)
        if not question:
            raise NotFoundError("Question not found.")
        if question.student_id != student_id:
            raise ForbiddenError("You can only delete your own questions.")
        question.is_deleted = True
        self.db.add(question)
        self.repo.commit()

    def get_question_detail(self, question_id: str) -> QuestionOut:
        question = self.repo.get(question_id)
        if not question:
            raise NotFoundError("Question not found.")
        question.view_count += 1
        self.db.add(question)
        self.repo.commit()
        return self._to_out(question)

    def feed(self, page: int, page_size: int, subject_id: str | None = None, search: str | None = None):
        items, total = self.repo.feed(page, page_size, subject_id, search)
        out = [self._to_out(q) for q in items]
        total_pages = (total + page_size - 1) // page_size if total else 0
        meta = PageMeta(page=page, page_size=page_size, total_items=total, total_pages=total_pages)
        return out, meta

    def trending(self, limit: int = 10):
        return [self._to_out(q) for q in self.repo.trending(limit)]

    # --- Answers ---
    def create_answer(self, mentor_id: str, question_id: str, payload: AnswerCreate) -> Answer:
        question = self.repo.get(question_id)
        if not question:
            raise NotFoundError("Question not found.")

        answer = Answer(question_id=question_id, mentor_id=mentor_id, body=payload.body)
        self.repo.create_answer(answer)

        # Never expose student identity for anonymous questions, even internally in notifications.
        self.notifications.notify(
            question.student_id, NotificationType.NEW_ANSWER, "New Answer to Your Question",
            f"Your question '{question.title}' has received a new answer.", auto_commit=False,
        )
        self.repo.commit()
        return answer

    def update_answer(self, mentor_id: str, answer_id: str, payload: AnswerUpdate) -> Answer:
        answer = self.repo.get_answer(answer_id)
        if not answer:
            raise NotFoundError("Answer not found.")
        if answer.mentor_id != mentor_id:
            raise ForbiddenError("You can only edit your own answers.")
        answer.body = payload.body
        self.db.add(answer)
        self.repo.commit()
        return answer

    def delete_answer(self, mentor_id: str, answer_id: str) -> None:
        answer = self.repo.get_answer(answer_id)
        if not answer:
            raise NotFoundError("Answer not found.")
        if answer.mentor_id != mentor_id:
            raise ForbiddenError("You can only delete your own answers.")
        answer.is_deleted = True
        self.db.add(answer)
        self.repo.commit()

    def vote_helpful(self, user_id: str, answer_id: str) -> Answer:
        answer = self.repo.get_answer(answer_id)
        if not answer:
            raise NotFoundError("Answer not found.")

        existing = self.repo.get_helpful_vote(answer_id, user_id)
        if existing:
            raise ConflictError("You have already voted this answer as helpful.")

        self.repo.add_helpful_vote(HelpfulVote(answer_id=answer_id, user_id=user_id))
        answer.helpful_count += 1
        self.db.add(answer)

        mentor_profile = None
        from app.modules.mentors.repository import MentorRepository

        mentor_profile = MentorRepository(self.db).get_by_user_id(answer.mentor_id)
        if mentor_profile:
            mentor_profile.helpful_score += 1
            self.db.add(mentor_profile)
            self.notifications.notify(
                answer.mentor_id, NotificationType.HELPFUL_VOTE, "Your answer was marked helpful",
                "A student marked your answer as helpful.", auto_commit=False,
            )

        self.repo.commit()
        return answer
