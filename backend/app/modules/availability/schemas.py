from datetime import date, time

from pydantic import BaseModel, model_validator


class AvailabilitySlotCreate(BaseModel):
    slot_date: date
    start_time: time
    end_time: time
    session_fee: float

    @model_validator(mode="after")
    def validate_times(self):
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class AvailabilitySlotUpdate(BaseModel):
    start_time: time | None = None
    end_time: time | None = None
    session_fee: float | None = None
    is_available: bool | None = None
    is_blocked: bool | None = None


class AvailabilitySlotOut(BaseModel):
    id: str
    mentor_id: str
    slot_date: date
    start_time: time
    end_time: time
    duration_minutes: int
    session_fee: float
    is_available: bool
    is_blocked: bool

    model_config = {"from_attributes": True}
