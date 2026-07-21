from datetime import datetime

from pydantic import BaseModel

from app.core.constants import BookmarkTargetType


class BookmarkCreate(BaseModel):
    target_type: BookmarkTargetType
    target_id: str


class BookmarkOut(BaseModel):
    id: str
    target_type: BookmarkTargetType
    target_id: str
    created_at: datetime

    model_config = {"from_attributes": True}
