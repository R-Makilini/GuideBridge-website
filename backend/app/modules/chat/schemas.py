from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ConversationCreate(BaseModel):
    mentor_user_id: str


class ConversationOut(BaseModel):
    id: str
    student_id: str
    mentor_user_id: str
    last_message_at: Optional[datetime] = None
    unread_count: int = 0

    model_config = {"from_attributes": True}


class MessageAttachmentOut(BaseModel):
    id: str
    file_url: str
    file_name: str
    mime_type: str

    model_config = {"from_attributes": True}


class MessageOut(BaseModel):
    id: str
    conversation_id: str
    sender_id: str
    content: Optional[str] = None
    is_seen: bool
    attachments: list[MessageAttachmentOut] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class SendMessageRequest(BaseModel):
    content: Optional[str] = None


class WebSocketIncoming(BaseModel):
    event: str  # message | typing | seen
    content: Optional[str] = None
