from datetime import date, time

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, Time, UniqueConstraint
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.database.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class AvailabilitySlot(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "availability_slots"
    __table_args__ = (
        UniqueConstraint(
            "mentor_id", "slot_date", "start_time", name="uq_mentor_slot_date_start"
        ),
    )

    mentor_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("mentor_profiles.id", ondelete="CASCADE"))
    slot_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(nullable=False)
    session_fee: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)

    mentor = relationship("MentorProfile")
    booking = relationship("Booking", back_populates="slot", uselist=False)
