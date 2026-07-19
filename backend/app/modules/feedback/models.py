from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.database.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class SessionFeedback(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "session_feedback"
    __table_args__ = (UniqueConstraint("booking_id", "author_id", name="uq_feedback_booking_author"),)

    booking_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("bookings.id", ondelete="CASCADE"), index=True)
    author_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("users.id", ondelete="CASCADE"))
    author_role: Mapped[str] = mapped_column(String(20), nullable=False)  # STUDENT | MENTOR
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_flagged: Mapped[bool] = mapped_column(Boolean, default=False)
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False)

    booking = relationship("Booking")
    author = relationship("User")
