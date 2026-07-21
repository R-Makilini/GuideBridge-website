from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.core.constants import PaymentStatus, RefundStatus


class InitiatePaymentRequest(BaseModel):
    booking_id: str


class PayHereCheckoutResponse(BaseModel):
    checkout_url: str
    payload: dict


class PaymentOut(BaseModel):
    id: str
    booking_id: str
    gateway_order_id: str
    amount: float
    currency: str
    platform_commission: float
    mentor_earnings: float
    status: PaymentStatus
    paid_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class RefundRequestCreate(BaseModel):
    payment_id: str
    reason: str


class RefundRequestOut(BaseModel):
    id: str
    payment_id: str
    reason: str
    status: RefundStatus
    admin_notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class RefundReviewRequest(BaseModel):
    status: RefundStatus
    admin_notes: Optional[str] = None


class InvoiceOut(BaseModel):
    invoice_number: str
    payment_id: str
    booking_id: str
    student_name: str
    mentor_name: str
    amount: float
    currency: str
    platform_commission: float
    mentor_earnings: float
    status: PaymentStatus
    issued_at: datetime
    paid_at: Optional[datetime] = None
