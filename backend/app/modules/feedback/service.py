from sqlalchemy.orm import Session

from app.core.constants import BookingStatus, UserRole
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.modules.bookings.repository import BookingRepository
from app.modules.feedback.models import SessionFeedback
from app.modules.feedback.repository import FeedbackRepository
from app.modules.feedback.schemas import FeedbackCreate, FeedbackModerationRequest
from app.modules.mentors.repository import MentorRepository


class FeedbackService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = FeedbackRepository(db)
        self.booking_repo = BookingRepository(db)
        self.mentor_repo = MentorRepository(db)

    def submit_feedback(self, user_id: str, role: UserRole, booking_id: str, payload: FeedbackCreate) -> SessionFeedback:
        booking = self.booking_repo.get(booking_id)
        if not booking:
            raise NotFoundError("Booking not found.")
        if booking.status != BookingStatus.COMPLETED:
            raise ConflictError("Feedback can only be submitted for completed sessions.")

        if role == UserRole.STUDENT and booking.student_id != user_id:
            raise ForbiddenError("This booking does not belong to you.")
        if role == UserRole.MENTOR and booking.mentor.user_id != user_id:
            raise ForbiddenError("This booking does not belong to you.")

        if self.repo.get(booking_id, user_id):
            raise ConflictError("You have already submitted feedback for this session.")

        feedback = SessionFeedback(
            booking_id=booking_id,
            author_id=user_id,
            author_role=role.value,
            rating=payload.rating,
            comment=payload.comment,
        )
        self.repo.create(feedback)

        if role == UserRole.STUDENT:
            mentor = self.mentor_repo.get_by_id(booking.mentor_id)
            mentor.average_rating = self.repo.average_rating_for_mentor(mentor.id)
            self.db.add(mentor)

        self.repo.commit()
        return feedback

    def list_for_booking(self, booking_id: str):
        return self.repo.list_for_booking(booking_id)

    def moderate(self, feedback_id: str, payload: FeedbackModerationRequest) -> SessionFeedback:
        feedback = self.repo.get_by_id(feedback_id)
        if not feedback:
            raise NotFoundError("Feedback not found.")
        feedback.is_hidden = payload.is_hidden
        self.db.add(feedback)
        self.repo.commit()
        return feedback

    def list_flagged(self):
        return self.repo.list_flagged()
