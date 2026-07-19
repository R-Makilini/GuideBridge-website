from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import ReportStatus, ReportTargetType
from app.database.base import Base
from app.database.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Report(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "reports"

    reported_by_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("users.id", ondelete="CASCADE"))
    target_type: Mapped[ReportTargetType] = mapped_column(nullable=False)
    target_id: Mapped[str] = mapped_column(CHAR(36), nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ReportStatus] = mapped_column(default=ReportStatus.OPEN, index=True)
    investigation_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    reported_by = relationship("User", foreign_keys=[reported_by_id])
    evidence = relationship("ReportEvidence", back_populates="report", cascade="all, delete-orphan")


class ReportEvidence(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "report_evidence"

    report_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("reports.id", ondelete="CASCADE"))
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)

    report = relationship("Report", back_populates="evidence")


class BlockedUser(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "blocked_users"

    blocker_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("users.id", ondelete="CASCADE"))
    blocked_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("users.id", ondelete="CASCADE"))

    __table_args__ = ()
