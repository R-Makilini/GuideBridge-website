from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.core.constants import VideoSessionStatus


class VideoSessionOut(BaseModel):
    id: str
    booking_id: str
    room_name: str
    status: VideoSessionStatus
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    session_notes: Optional[str] = None

    model_config = {"from_attributes": True}


class JoinDetailsOut(BaseModel):
    room_name: str
    join_url: str
    jitsi_domain: str


class SessionNotesUpdate(BaseModel):
    session_notes: str
