from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class FeedbackCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None


class FeedbackOut(BaseModel):
    id: str
    booking_id: str
    author_id: str
    author_role: str
    rating: int
    comment: Optional[str] = None
    is_hidden: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class FeedbackModerationRequest(BaseModel):
    is_hidden: bool
