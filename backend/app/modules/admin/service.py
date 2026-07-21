from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.constants import (
    BookingStatus,
    PaymentStatus,
    ReportStatus,
    UserRole,
    UserStatus,
    VerificationStatus,
)
from app.core.exceptions import NotFoundError
from app.modules.admin.models import AdminAction, AuditLog, SystemSetting
from app.modules.admin.schemas import AdminDashboardOut, SystemSettingUpdate
from app.modules.bookings.models import Booking
from app.modules.mentors.models import MentorProfile
from app.modules.payments.models import Payment
from app.modules.questions.models import Question
from app.modules.reports.models import Report
from app.modules.resources.models import Resource
from app.modules.users.models import User


class AdminService:
    def __init__(self, db: Session):
        self.db = db

    def log_action(self, admin_id: str, action_type: str, target_type: str | None = None, target_id: str | None = None, details: str | None = None) -> None:
        self.db.add(
            AdminAction(admin_id=admin_id, action_type=action_type, target_type=target_type, target_id=target_id, details=details)
        )
        self.db.add(AuditLog(actor_id=admin_id, event=action_type, metadata_json=details))
        self.db.commit()

    def dashboard(self) -> AdminDashboardOut:
        total_students = self.db.query(func.count(User.id)).filter(User.role == UserRole.STUDENT).scalar() or 0
        total_mentors = self.db.query(func.count(User.id)).filter(User.role == UserRole.MENTOR).scalar() or 0
        pending_mentors = (
            self.db.query(func.count(MentorProfile.id))
            .filter(MentorProfile.verification_status == VerificationStatus.PENDING)
            .scalar()
            or 0
        )
        approved_mentors = (
            self.db.query(func.count(MentorProfile.id))
            .filter(MentorProfile.verification_status == VerificationStatus.APPROVED)
            .scalar()
            or 0
        )
        suspended_users = (
            self.db.query(func.count(User.id))
            .filter(User.status.in_([UserStatus.SUSPENDED, UserStatus.BANNED]))
            .scalar()
            or 0
        )
        total_bookings = self.db.query(func.count(Booking.id)).scalar() or 0
        completed_sessions = (
            self.db.query(func.count(Booking.id)).filter(Booking.status == BookingStatus.COMPLETED).scalar() or 0
        )
        payment_count = self.db.query(func.count(Payment.id)).filter(Payment.status == PaymentStatus.PAID).scalar() or 0
        platform_revenue = (
            self.db.query(func.coalesce(func.sum(Payment.platform_commission), 0))
            .filter(Payment.status == PaymentStatus.PAID)
            .scalar()
            or 0
        )
        mentor_earnings_total = (
            self.db.query(func.coalesce(func.sum(Payment.mentor_earnings), 0))
            .filter(Payment.status == PaymentStatus.PAID)
            .scalar()
            or 0
        )
        total_questions = self.db.query(func.count(Question.id)).scalar() or 0
        total_resources = self.db.query(func.count(Resource.id)).scalar() or 0
        open_reports = self.db.query(func.count(Report.id)).filter(Report.status == ReportStatus.OPEN).scalar() or 0

        return AdminDashboardOut(
            total_students=total_students,
            total_mentors=total_mentors,
            pending_mentors=pending_mentors,
            approved_mentors=approved_mentors,
            suspended_users=suspended_users,
            total_bookings=total_bookings,
            completed_sessions=completed_sessions,
            payment_count=payment_count,
            platform_revenue=float(platform_revenue),
            mentor_earnings_total=float(mentor_earnings_total),
            total_questions=total_questions,
            total_resources=total_resources,
            open_reports=open_reports,
        )

    def list_students(self):
        return self.db.query(User).filter(User.role == UserRole.STUDENT).order_by(User.created_at.desc()).all()

    def list_mentors(self):
        return self.db.query(User).filter(User.role == UserRole.MENTOR).order_by(User.created_at.desc()).all()

    def update_user_status(self, admin_id: str, user_id: str, status: UserStatus, reason: str | None) -> User:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("User not found.")
        user.status = status
        self.db.add(user)
        self.db.commit()
        self.log_action(admin_id, f"user_status_{status.value.lower()}", "user", user_id, reason)
        return user

    def get_setting(self, key: str) -> SystemSetting | None:
        return self.db.query(SystemSetting).filter(SystemSetting.key == key).first()

    def list_settings(self):
        return self.db.query(SystemSetting).all()

    def upsert_setting(self, payload: SystemSettingUpdate) -> SystemSetting:
        setting = self.get_setting(payload.key)
        if setting:
            setting.value = payload.value
            if payload.description:
                setting.description = payload.description
        else:
            setting = SystemSetting(key=payload.key, value=payload.value, description=payload.description)
        self.db.add(setting)
        self.db.commit()
        return setting

    def list_audit_logs(self, limit: int = 100):
        return self.db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
