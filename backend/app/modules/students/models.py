from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.database.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class StudentProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "student_profiles"

    user_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    school: Mapped[str | None] = mapped_column(String(200), nullable=True)
    grade: Mapped[str | None] = mapped_column(String(20), nullable=True)
    stream_id: Mapped[str | None] = mapped_column(
        CHAR(36), ForeignKey("streams.id", ondelete="SET NULL"), nullable=True
    )
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    preferred_language: Mapped[str | None] = mapped_column(String(50), nullable=True, default="en")
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)

    user = relationship("User", back_populates="student_profile")
    stream = relationship("Stream")
