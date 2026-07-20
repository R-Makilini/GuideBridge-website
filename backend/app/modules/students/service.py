from sqlalchemy.orm import Session

from app.core.constants import BookingStatus, BookmarkTargetType
from app.core.exceptions import NotFoundError
from app.modules.bookings.models import Booking
from app.modules.bookmarks.models import Bookmark
from app.modules.payments.models import Payment
from app.modules.questions.models import Question
from app.modules.students.repository import StudentRepository
from app.modules.students.schemas import StudentDashboardOut, StudentProfileUpdate


class StudentService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = StudentRepository(db)

    def get_profile(self, user_id: str):
        profile = self.repo.get_by_user_id(user_id)
        if not profile:
            raise NotFoundError("Student profile not found.")
        return profile

    def update_profile(self, user_id: str, payload: StudentProfileUpdate):
        profile = self.get_profile(user_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(profile, field, value)
        self.db.add(profile)
        self.repo.commit()
        return profile

    def dashboard_summary(self, user_id: str) -> StudentDashboardOut:
        from app.modules.chat.models import Conversation

        total_bookings = self.db.query(Booking).filter(Booking.student_id == user_id).count()
        upcoming = (
            self.db.query(Booking)
            .filter(
                Booking.student_id == user_id,
                Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.ACCEPTED]),
            )
            .count()
        )
        completed = (
            self.db.query(Booking)
            .filter(Booking.student_id == user_id, Booking.status == BookingStatus.COMPLETED)
            .count()
        )
        questions_asked = self.db.query(Question).filter(Question.student_id == user_id).count()
        saved_mentors = (
            self.db.query(Bookmark)
            .filter(Bookmark.user_id == user_id, Bookmark.target_type == BookmarkTargetType.MENTOR)
            .count()
        )
        total_payments = self.db.query(Payment).filter(Payment.student_id == user_id).count()
        saved_resources_count = (
            self.db.query(Bookmark)
            .filter(Bookmark.user_id == user_id, Bookmark.target_type == BookmarkTargetType.RESOURCE)
            .count()
        )

        recent_questions = [
            {"id": q.id, "title": q.title, "created_at": str(q.created_at)}
            for q in self.db.query(Question)
            .filter(Question.student_id == user_id)
            .order_by(Question.created_at.desc())
            .limit(5)
            .all()
        ]
        upcoming_sessions = [
            {"id": b.id, "status": b.status.value, "fee": float(b.fee)}
            for b in self.db.query(Booking)
            .filter(Booking.student_id == user_id, Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.ACCEPTED]))
            .order_by(Booking.created_at.desc())
            .limit(5)
            .all()
        ]
        recent_chats = [
            {"id": c.id, "mentor_user_id": c.mentor_user_id, "last_message_at": str(c.last_message_at)}
            for c in self.db.query(Conversation)
            .filter(Conversation.student_id == user_id)
            .order_by(Conversation.last_message_at.desc())
            .limit(5)
            .all()
        ]

        return StudentDashboardOut(
            total_bookings=total_bookings,
            upcoming_bookings=upcoming,
            completed_sessions=completed,
            total_questions_asked=questions_asked,
            saved_mentors=saved_mentors,
            total_payments=total_payments,
            saved_resources_count=saved_resources_count,
            recent_questions=recent_questions,
            upcoming_sessions=upcoming_sessions,
            recent_chats=recent_chats,
        )
