from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.core.constants import NotificationType


class NotificationOut(BaseModel):
    id: str
    type: NotificationType
    title: str
    body: Optional[str] = None
    link_url: Optional[str] = None
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UnreadCountOut(BaseModel):
    unread_count: int
