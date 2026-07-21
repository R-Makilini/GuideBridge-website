from datetime import datetime, timedelta, timezone
from app.core.datetime_utils import utcnow

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.constants import BookingStatus, PaymentStatus, UserRole, VerificationStatus
from app.modules.analytics.schemas import (
    AnalyticsSeriesOut,
    FeaturedMentorOut,
    MonthlyPoint,
    PlatformStatsOut,
    PopularSubjectOut,
)
from app.modules.bookings.models import Booking
from app.modules.mentors.models import MentorProfile
from app.modules.payments.models import Payment
from app.modules.questions.models import Question
from app.modules.resources.models import Resource
from app.modules.users.models import User


def _month_key_expr(column):
    return func.date_format(column, "%Y-%m")


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def _monthly_series(self, model, column, filters, months: int = 12) -> list[MonthlyPoint]:
        since = utcnow() - timedelta(days=30 * months)
        rows = (
            self.db.query(_month_key_expr(column).label("month"), func.count().label("cnt"))
            .filter(column >= since, *filters)
            .group_by("month")
            .order_by("month")
            .all()
        )
        return [MonthlyPoint(month=r.month, value=float(r.cnt)) for r in rows]

    def _monthly_sum_series(self, column, sum_column, filters, months: int = 12) -> list[MonthlyPoint]:
        since = utcnow() - timedelta(days=30 * months)
        rows = (
            self.db.query(_month_key_expr(column).label("month"), func.coalesce(func.sum(sum_column), 0).label("total"))
            .filter(column >= since, *filters)
            .group_by("month")
            .order_by("month")
            .all()
        )
        return [MonthlyPoint(month=r.month, value=float(r.total)) for r in rows]

    def get_series(self) -> AnalyticsSeriesOut:
        return AnalyticsSeriesOut(
            user_growth=self._monthly_series(User, User.created_at, [User.role == UserRole.STUDENT]),
            mentor_growth=self._monthly_series(User, User.created_at, [User.role == UserRole.MENTOR]),
            booking_counts=self._monthly_series(Booking, Booking.created_at, []),
            revenue=self._monthly_sum_series(Payment.created_at, Payment.platform_commission, [Payment.status == PaymentStatus.PAID]),
            mentor_earnings=self._monthly_sum_series(Payment.created_at, Payment.mentor_earnings, [Payment.status == PaymentStatus.PAID]),
        )

    def get_platform_stats(self) -> PlatformStatsOut:
        total_students = self.db.query(func.count(User.id)).filter(User.role == UserRole.STUDENT).scalar() or 0
        total_mentors = (
            self.db.query(func.count(MentorProfile.id))
            .filter(MentorProfile.verification_status == VerificationStatus.APPROVED)
            .scalar()
            or 0
        )
        completed_sessions = self.db.query(func.count(Booking.id)).filter(Booking.status == BookingStatus.COMPLETED).scalar() or 0
        answered_questions = self.db.query(func.count(func.distinct(Question.id))).join(Question.answers).scalar() or 0

        return PlatformStatsOut(
            total_students=total_students,
            total_mentors=total_mentors,
            total_sessions_completed=completed_sessions,
            total_questions_answered=answered_questions,
        )

    def get_featured_mentors(self, limit: int = 6) -> list[FeaturedMentorOut]:
        mentors = (
            self.db.query(MentorProfile)
            .filter(MentorProfile.verification_status == VerificationStatus.APPROVED, MentorProfile.is_publicly_visible.is_(True))
            .order_by(MentorProfile.helpful_score.desc())
            .limit(limit)
            .all()
        )
        return [
            FeaturedMentorOut(
                id=m.id,
                full_name=m.user.full_name,
                profile_picture_url=m.user.profile_picture_url,
                biography=m.biography,
                helpful_score=m.helpful_score,
                average_rating=m.average_rating,
            )
            for m in mentors
        ]

    def get_popular_subjects(self, limit: int = 8) -> list[PopularSubjectOut]:
        from app.modules.universities.models import Subject

        rows = (
            self.db.query(Subject.id, Subject.name, func.count(Question.id).label("cnt"))
            .join(Question, Question.subject_id == Subject.id)
            .group_by(Subject.id, Subject.name)
            .order_by(func.count(Question.id).desc())
            .limit(limit)
            .all()
        )
        return [PopularSubjectOut(id=r.id, name=r.name, question_count=r.cnt) for r in rows]

    def get_latest_resources(self, limit: int = 8):
        from app.core.constants import ResourceApprovalStatus

        return (
            self.db.query(Resource)
            .filter(Resource.approval_status == ResourceApprovalStatus.APPROVED)
            .order_by(Resource.created_at.desc())
            .limit(limit)
            .all()
        )
