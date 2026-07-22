from sqlalchemy.orm import Session

from app.modules.reports.models import BlockedUser, Report, ReportEvidence


class ReportRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, report: Report) -> Report:
        self.db.add(report)
        self.db.flush()
        return report

    def get(self, report_id: str) -> Report | None:
        return self.db.query(Report).filter(Report.id == report_id).first()

    def list_all(self, status=None):
        query = self.db.query(Report)
        if status:
            query = query.filter(Report.status == status)
        return query.order_by(Report.created_at.desc()).all()

    def add_evidence(self, evidence: ReportEvidence) -> None:
        self.db.add(evidence)

    def block(self, blocker_id: str, blocked_id: str) -> BlockedUser:
        existing = (
            self.db.query(BlockedUser)
            .filter(BlockedUser.blocker_id == blocker_id, BlockedUser.blocked_id == blocked_id)
            .first()
        )
        if existing:
            return existing
        row = BlockedUser(blocker_id=blocker_id, blocked_id=blocked_id)
        self.db.add(row)
        self.db.flush()
        return row

    def unblock(self, blocker_id: str, blocked_id: str) -> None:
        self.db.query(BlockedUser).filter(
            BlockedUser.blocker_id == blocker_id, BlockedUser.blocked_id == blocked_id
        ).delete()

    def list_blocked(self, blocker_id: str):
        return self.db.query(BlockedUser).filter(BlockedUser.blocker_id == blocker_id).all()

    def commit(self):
        self.db.commit()
