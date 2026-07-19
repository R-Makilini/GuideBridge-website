from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import PaymentStatus, RefundStatus
from app.database.base import Base
from app.database.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Payment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "payments"
    __table_args__ = (UniqueConstraint("booking_id", name="uq_payment_booking"),)

    booking_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("bookings.id", ondelete="CASCADE"))
    student_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("users.id", ondelete="CASCADE"))
    gateway_order_id: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    gateway_payment_id: Mapped[str | None] = mapped_column(String(150), nullable=True)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="LKR")
    platform_commission: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    mentor_earnings: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    status: Mapped[PaymentStatus] = mapped_column(default=PaymentStatus.PENDING, index=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    booking = relationship("Booking", back_populates="payment")
    student = relationship("User")
    events = relationship("PaymentEvent", back_populates="payment", cascade="all, delete-orphan")
    refund_requests = relationship("RefundRequest", back_populates="payment", cascade="all, delete-orphan")


class PaymentEvent(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "payment_events"

    payment_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("payments.id", ondelete="CASCADE"))
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    raw_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    signature_valid: Mapped[bool] = mapped_column(default=False)

    payment = relationship("Payment", back_populates="events")


class RefundRequest(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "refund_requests"

    payment_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("payments.id", ondelete="CASCADE"))
    requested_by_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("users.id", ondelete="CASCADE"))
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[RefundStatus] = mapped_column(default=RefundStatus.REQUESTED)
    admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    payment = relationship("Payment", back_populates="refund_requests")
    requested_by = relationship("User")
