from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.constants import ResourceApprovalStatus, ResourceType
from app.core.pagination import PaginatedResponse
from app.core.permissions import require_any_authenticated, require_super_admin
from app.database.session import get_db
from app.modules.auth.dependencies import get_optional_current_user
from app.modules.resources.schemas import (
    ResourceApprovalRequest,
    ResourceCreate,
    ResourceOut,
    ResourcePreviewOut,
    ResourceUpdate,
)
from app.modules.resources.service import ResourceService
from app.modules.users.models import User

router = APIRouter(prefix="/resources", tags=["Resources"])


@router.post("", response_model=ResourceOut, status_code=201)
def upload_resource(
    title: str = Form(...),
    description: str | None = Form(None),
    resource_type: ResourceType = Form(...),
    subject_id: str | None = Form(None),
    is_premium: bool = Form(False),
    file: UploadFile = File(...),
    current_user: User = Depends(require_any_authenticated),
    db: Session = Depends(get_db),
):
    payload = ResourceCreate(
        title=title, description=description, resource_type=resource_type, subject_id=subject_id, is_premium=is_premium
    )
    return ResourceService(db).upload_resource(current_user.id, payload, file)


@router.put("/{resource_id}", response_model=ResourceOut)
def update_resource(resource_id: str, payload: ResourceUpdate, current_user: User = Depends(require_any_authenticated), db: Session = Depends(get_db)):
    return ResourceService(db).update_resource(current_user.id, resource_id, payload)


@router.delete("/{resource_id}", status_code=204)
def delete_resource(resource_id: str, current_user: User = Depends(require_any_authenticated), db: Session = Depends(get_db)):
    ResourceService(db).delete_resource(current_user.id, resource_id)


@router.get("", response_model=PaginatedResponse[ResourceOut])
def list_resources(
    resource_type: ResourceType | None = Query(None),
    subject_id: str | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    items, meta = ResourceService(db).list_resources(page, page_size, resource_type, subject_id, search)
    return PaginatedResponse(items=items, meta=meta)


@router.get("/pending", response_model=list[ResourceOut])
def list_pending(current_user: User = Depends(require_super_admin), db: Session = Depends(get_db)):
    return ResourceService(db).list_pending()


@router.post("/{resource_id}/review", response_model=ResourceOut)
def review_resource(resource_id: str, payload: ResourceApprovalRequest, current_user: User = Depends(require_super_admin), db: Session = Depends(get_db)):
    return ResourceService(db).review_resource(current_user.id, resource_id, payload)


@router.get("/{resource_id}/preview", response_model=ResourcePreviewOut)
def preview_resource(resource_id: str, current_user: User | None = Depends(get_optional_current_user), db: Session = Depends(get_db)):
    return ResourceService(db).get_preview(resource_id, current_user.id if current_user else None)


@router.post("/{resource_id}/download", response_model=ResourceOut)
def download_resource(resource_id: str, current_user: User = Depends(require_any_authenticated), db: Session = Depends(get_db)):
    return ResourceService(db).download_resource(current_user.id, resource_id)
