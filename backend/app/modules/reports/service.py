from datetime import datetime, timezone
from app.core.datetime_utils import utcnow

from sqlalchemy.orm import Session

from app.core.constants import ReportStatus, UserStatus
from app.core.exceptions import NotFoundError
from app.modules.reports.models import Report
from app.modules.reports.repository import ReportRepository
from app.modules.reports.schemas import ReportCreate, ReportReviewRequest
from app.modules.users.models import User


class ReportService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ReportRepository(db)

    def create_report(self, reported_by_id: str, payload: ReportCreate) -> Report:
        report = Report(reported_by_id=reported_by_id, **payload.model_dump())
        self.repo.create(report)
        self.repo.commit()
        return report

    def list_reports(self, status=None):
        return self.repo.list_all(status)

    def review_report(self, report_id: str, payload: ReportReviewRequest) -> Report:
        report = self.repo.get(report_id)
        if not report:
            raise NotFoundError("Report not found.")

        report.status = payload.status
        report.investigation_notes = payload.investigation_notes
        if payload.status in (ReportStatus.RESOLVED, ReportStatus.DISMISSED):
            report.resolved_at = utcnow()

        if payload.status in (ReportStatus.SUSPENDED, ReportStatus.BANNED) and report.target_type.value == "USER":
            target_user = self.db.query(User).filter(User.id == report.target_id).first()
            if target_user:
                target_user.status = UserStatus.SUSPENDED if payload.status == ReportStatus.SUSPENDED else UserStatus.BANNED
                self.db.add(target_user)

        self.db.add(report)
        self.repo.commit()
        return report

    def block_user(self, blocker_id: str, blocked_id: str):
        result = self.repo.block(blocker_id, blocked_id)
        self.repo.commit()
        return result

    def unblock_user(self, blocker_id: str, blocked_id: str) -> None:
        self.repo.unblock(blocker_id, blocked_id)
        self.repo.commit()

    def list_blocked(self, blocker_id: str):
        return self.repo.list_blocked(blocker_id)
