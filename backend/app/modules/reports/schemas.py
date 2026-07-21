from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.core.constants import ReportStatus, ReportTargetType


class ReportCreate(BaseModel):
    target_type: ReportTargetType
    target_id: str
    reason: str
    description: Optional[str] = None


class ReportOut(BaseModel):
    id: str
    target_type: ReportTargetType
    target_id: str
    reason: str
    description: Optional[str] = None
    status: ReportStatus
    investigation_notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ReportReviewRequest(BaseModel):
    status: ReportStatus
    investigation_notes: Optional[str] = None


class BlockUserRequest(BaseModel):
    blocked_id: str
