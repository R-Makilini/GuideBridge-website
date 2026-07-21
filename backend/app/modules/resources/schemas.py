from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.core.constants import ResourceApprovalStatus, ResourceType


class ResourceCreate(BaseModel):
    title: str
    description: Optional[str] = None
    resource_type: ResourceType
    subject_id: Optional[str] = None
    is_premium: bool = False


class ResourceUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    subject_id: Optional[str] = None
    is_premium: Optional[bool] = None


class ResourceOut(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    resource_type: ResourceType
    file_url: str
    file_name: str
    mime_type: str
    is_premium: bool
    approval_status: ResourceApprovalStatus
    view_count: int
    download_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ResourceApprovalRequest(BaseModel):
    approval_status: ResourceApprovalStatus


class ResourcePreviewOut(BaseModel):
    """
    Secure preview metadata. The raw file_url is only ever exposed here after
    an authorization check (premium/ownership/approval) has already passed.
    """
    id: str
    title: str
    resource_type: ResourceType
    mime_type: str
    preview_kind: str  # pdf | image | video | unsupported
    preview_url: str
    is_premium: bool
    requires_purchase: bool
