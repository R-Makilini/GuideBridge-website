from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import DocumentType, VerificationStatus
from app.database.base import Base
from app.database.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class VerificationDocument(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "verification_documents"

    mentor_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("mentor_profiles.id", ondelete="CASCADE"),
    )
    document_type: Mapped[DocumentType] = mapped_column(nullable=False)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(nullable=False)

    mentor = relationship(
        "MentorProfile",
        back_populates="verification_documents",
    )


class VerificationReview(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "verification_reviews"

    mentor_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("mentor_profiles.id", ondelete="CASCADE"),
    )

    reviewed_by_id: Mapped[str | None] = mapped_column(
        CHAR(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    status: Mapped[VerificationStatus] = mapped_column(nullable=False)
    admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    mentor = relationship("MentorProfile")
    reviewed_by = relationship("User")