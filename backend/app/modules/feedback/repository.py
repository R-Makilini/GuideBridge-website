from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.feedback.models import SessionFeedback


class FeedbackRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, booking_id: str, author_id: str) -> SessionFeedback | None:
        return (
            self.db.query(SessionFeedback)
            .filter(SessionFeedback.booking_id == booking_id, SessionFeedback.author_id == author_id)
            .first()
        )

    def create(self, feedback: SessionFeedback) -> SessionFeedback:
        self.db.add(feedback)
        self.db.flush()
        return feedback

    def list_for_booking(self, booking_id: str):
        return self.db.query(SessionFeedback).filter(SessionFeedback.booking_id == booking_id).all()

    def average_rating_for_mentor(self, mentor_id: str) -> float:
        from app.modules.bookings.models import Booking

        avg = (
            self.db.query(func.avg(SessionFeedback.rating))
            .join(Booking, Booking.id == SessionFeedback.booking_id)
            .filter(Booking.mentor_id == mentor_id, SessionFeedback.author_role == "STUDENT", SessionFeedback.is_hidden.is_(False))
            .scalar()
        )
        return float(avg) if avg else 0.0

    def list_flagged(self):
        return self.db.query(SessionFeedback).filter(SessionFeedback.is_flagged.is_(True)).all()

    def get_by_id(self, feedback_id: str) -> SessionFeedback | None:
        return self.db.query(SessionFeedback).filter(SessionFeedback.id == feedback_id).first()

    def commit(self):
        self.db.commit()
