from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import BookingStatus
from app.database.base import Base
from app.database.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Booking(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "bookings"
    __table_args__ = (UniqueConstraint("slot_id", name="uq_booking_slot"),)

    student_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    mentor_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("mentor_profiles.id", ondelete="CASCADE"), index=True
    )
    slot_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("availability_slots.id", ondelete="RESTRICT"))
    status: Mapped[BookingStatus] = mapped_column(default=BookingStatus.PENDING, index=True)
    topic: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    fee: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    cancelled_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    student = relationship("User", foreign_keys=[student_id])
    mentor = relationship("MentorProfile")
    slot = relationship("AvailabilitySlot", back_populates="booking")
    status_history = relationship(
        "BookingStatusHistory", back_populates="booking", cascade="all, delete-orphan"
    )
    payment = relationship("Payment", back_populates="booking", uselist=False)


class BookingStatusHistory(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "booking_status_history"

    booking_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("bookings.id", ondelete="CASCADE"))
    from_status: Mapped[BookingStatus | None] = mapped_column(nullable=True)
    to_status: Mapped[BookingStatus] = mapped_column(nullable=False)
    changed_by_id: Mapped[str | None] = mapped_column(CHAR(36), ForeignKey("users.id", ondelete="SET NULL"))
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    booking = relationship("Booking", back_populates="status_history")
    changed_by = relationship("User")
