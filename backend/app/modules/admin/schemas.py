from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.core.constants import UserStatus


class AdminDashboardOut(BaseModel):
    total_students: int
    total_mentors: int
    pending_mentors: int
    approved_mentors: int
    suspended_users: int
    total_bookings: int
    completed_sessions: int
    payment_count: int
    platform_revenue: float
    mentor_earnings_total: float
    total_questions: int
    total_resources: int
    open_reports: int


class UserStatusUpdateRequest(BaseModel):
    status: UserStatus
    reason: Optional[str] = None


class AdminUserOut(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    status: str
    is_email_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SystemSettingUpdate(BaseModel):
    key: str
    value: str
    description: Optional[str] = None


class SystemSettingOut(BaseModel):
    id: str
    key: str
    value: str
    description: Optional[str] = None

    model_config = {"from_attributes": True}


class AuditLogOut(BaseModel):
    id: str
    actor_id: Optional[str] = None
    event: str
    metadata_json: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
