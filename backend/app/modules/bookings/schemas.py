from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.core.constants import BookingStatus


class BookingCreate(BaseModel):
    slot_id: str
    topic: Optional[str] = None
    notes: Optional[str] = None


class BookingCancel(BaseModel):
    reason: Optional[str] = None


class BookingReschedule(BaseModel):
    new_slot_id: str


class BookingOut(BaseModel):
    id: str
    student_id: str
    mentor_id: str
    slot_id: str
    status: BookingStatus
    topic: Optional[str] = None
    notes: Optional[str] = None
    fee: float
    cancelled_reason: Optional[str] = None
    confirmed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class BookingStatusHistoryOut(BaseModel):
    id: str
    from_status: Optional[BookingStatus] = None
    to_status: BookingStatus
    reason: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
