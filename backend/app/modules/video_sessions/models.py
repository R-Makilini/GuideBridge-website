from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import VideoSessionStatus
from app.database.base import Base
from app.database.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class VideoSession(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "video_sessions"
    __table_args__ = (UniqueConstraint("booking_id", name="uq_video_session_booking"),)

    booking_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("bookings.id", ondelete="CASCADE"))
    room_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    status: Mapped[VideoSessionStatus] = mapped_column(default=VideoSessionStatus.SCHEDULED)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    session_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    booking = relationship("Booking")
    attendance = relationship("SessionAttendance", back_populates="video_session", cascade="all, delete-orphan")


class SessionAttendance(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "session_attendance"
    __table_args__ = (UniqueConstraint("video_session_id", "user_id", name="uq_attendance_session_user"),)

    video_session_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("video_sessions.id", ondelete="CASCADE"))
    user_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("users.id", ondelete="CASCADE"))
    joined_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    left_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    video_session = relationship("VideoSession", back_populates="attendance")
    user = relationship("User")
