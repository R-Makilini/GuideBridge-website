from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, NotFoundError
from app.modules.mentors.repository import MentorRepository
from app.modules.mentors.schemas import MentorProfileUpdate


class MentorService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = MentorRepository(db)

    def get_own_profile(self, user_id: str):
        profile = self.repo.get_by_user_id(user_id)
        if not profile:
            raise NotFoundError("Mentor profile not found.")
        return profile

    def update_own_profile(self, user_id: str, payload: MentorProfileUpdate):
        profile = self.get_own_profile(user_id)
        data = payload.model_dump(exclude_unset=True)

        subject_ids = data.pop("subject_ids", None)
        tag_ids = data.pop("expertise_tag_ids", None)
        languages = data.pop("languages", None)

        for field, value in data.items():
            setattr(profile, field, value)

        if subject_ids is not None:
            self.repo.replace_subjects(profile.id, subject_ids)
        if tag_ids is not None:
            self.repo.replace_expertise_tags(profile.id, tag_ids)
        if languages is not None:
            self.repo.replace_languages(profile.id, languages)

        self.db.add(profile)
        self.repo.commit()
        self.db.refresh(profile)
        return profile

    def get_public_profile(self, mentor_id: str):
        profile = self.repo.get_public_profile(mentor_id)
        if not profile:
            raise NotFoundError("Mentor not found or not publicly visible.")
        return profile

    def dashboard_summary(self, user_id: str):
        from app.core.constants import BookingStatus, PaymentStatus
        from app.modules.bookings.models import Booking
        from app.modules.payments.models import Payment
        from app.modules.questions.models import Answer
        from app.modules.mentors.schemas import MentorDashboardOut, MentorEarningsSummaryOut

        mentor = self.get_own_profile(user_id)

        total_bookings = self.db.query(Booking).filter(Booking.mentor_id == mentor.id).count()
        upcoming = (
            self.db.query(Booking)
            .filter(Booking.mentor_id == mentor.id, Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.ACCEPTED]))
            .count()
        )
        completed = (
            self.db.query(Booking)
            .filter(Booking.mentor_id == mentor.id, Booking.status == BookingStatus.COMPLETED)
            .count()
        )
        total_answers = self.db.query(Answer).filter(Answer.mentor_id == user_id).count()

        return MentorDashboardOut(
            total_bookings=total_bookings,
            upcoming_bookings=upcoming,
            completed_sessions=completed,
            total_answers_given=total_answers,
            helpful_score=mentor.helpful_score,
            average_rating=mentor.average_rating,
            profile_completion_percentage=mentor.profile_completion_percentage,
            verification_status=mentor.verification_status.value,
        )

    def earnings_summary(self, user_id: str):
        from app.core.constants import PaymentStatus
        from app.modules.bookings.models import Booking
        from app.modules.payments.models import Payment
        from app.modules.mentors.schemas import MentorEarningsSummaryOut

        mentor = self.get_own_profile(user_id)

        rows = (
            self.db.query(Payment)
            .join(Booking, Booking.id == Payment.booking_id)
            .filter(Booking.mentor_id == mentor.id, Payment.status == PaymentStatus.PAID)
            .order_by(Payment.paid_at.desc())
            .all()
        )
        total_earnings = sum(float(p.mentor_earnings) for p in rows)
        last_payout = float(rows[0].mentor_earnings) if rows else None

        return MentorEarningsSummaryOut(
            total_earnings=total_earnings,
            pending_earnings=0.0,
            completed_payment_count=len(rows),
            last_payout_amount=last_payout,
        )
