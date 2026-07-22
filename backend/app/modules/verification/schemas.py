from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.core.constants import DocumentType, VerificationStatus


class VerificationDocumentOut(BaseModel):
    id: str
    document_type: DocumentType
    file_url: str
    file_name: str
    mime_type: str
    file_size_bytes: int
    created_at: datetime

    model_config = {"from_attributes": True}


class VerificationReviewRequest(BaseModel):
    status: VerificationStatus
    admin_notes: Optional[str] = None


class VerificationReviewOut(BaseModel):
    id: str
    mentor_id: str
    status: VerificationStatus
    admin_notes: Optional[str] = None
    reviewed_at: datetime

    model_config = {"from_attributes": True}


class PendingMentorOut(BaseModel):
    mentor_id: str
    full_name: str
    email: str
    verification_status: VerificationStatus
    documents: list[VerificationDocumentOut]

    model_config = {"from_attributes": True}
