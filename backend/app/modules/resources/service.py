from sqlalchemy.orm import Session

from app.core.constants import NotificationType, ResourceApprovalStatus
from app.core.exceptions import ForbiddenError, NotFoundError, PaymentRequiredError
from app.core.file_validation import safe_file_key, validate_upload
from app.core.pagination import PageMeta
from app.integrations.storage import get_storage_backend
from app.modules.notifications.service import NotificationService
from app.modules.resources.models import Resource, ResourceDownload
from app.modules.resources.repository import ResourceRepository
from app.modules.resources.schemas import ResourceApprovalRequest, ResourceCreate, ResourcePreviewOut, ResourceUpdate

PREVIEWABLE_MIME = {
    "application/pdf": "pdf",
    "image/jpeg": "image",
    "image/png": "image",
}


class ResourceService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ResourceRepository(db)
        self.notifications = NotificationService(db)

    def upload_resource(self, uploaded_by_id: str, payload: ResourceCreate, file) -> Resource:
        validate_upload(file)
        key, safe_name = safe_file_key(file.filename, folder="resources")
        url = get_storage_backend().upload(file.file, key, file.content_type)

        file.file.seek(0, 2)
        size = file.file.tell()
        file.file.seek(0)

        resource = Resource(
            uploaded_by_id=uploaded_by_id,
            subject_id=payload.subject_id,
            title=payload.title,
            description=payload.description,
            resource_type=payload.resource_type,
            file_url=url,
            file_name=safe_name,
            mime_type=file.content_type,
            file_size_bytes=size,
            is_premium=payload.is_premium,
        )
        self.repo.create(resource)
        self.repo.commit()
        return resource

    def update_resource(self, user_id: str, resource_id: str, payload: ResourceUpdate) -> Resource:
        resource = self.repo.get(resource_id)
        if not resource:
            raise NotFoundError("Resource not found.")
        if resource.uploaded_by_id != user_id:
            raise ForbiddenError("You can only edit your own resources.")
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(resource, field, value)
        self.db.add(resource)
        self.repo.commit()
        return resource

    def delete_resource(self, user_id: str, resource_id: str) -> None:
        resource = self.repo.get(resource_id)
        if not resource:
            raise NotFoundError("Resource not found.")
        if resource.uploaded_by_id != user_id:
            raise ForbiddenError("You can only delete your own resources.")
        self.db.delete(resource)
        self.repo.commit()

    def list_resources(self, page: int, page_size: int, resource_type=None, subject_id=None, search=None):
        items, total = self.repo.list_approved(page, page_size, resource_type, subject_id, search)
        total_pages = (total + page_size - 1) // page_size if total else 0
        meta = PageMeta(page=page, page_size=page_size, total_items=total, total_pages=total_pages)
        return items, meta

    def list_pending(self):
        return self.repo.list_pending()

    def review_resource(self, admin_id: str, resource_id: str, payload: ResourceApprovalRequest) -> Resource:
        resource = self.repo.get(resource_id)
        if not resource:
            raise NotFoundError("Resource not found.")
        resource.approval_status = payload.approval_status
        self.db.add(resource)

        self.notifications.notify(
            resource.uploaded_by_id, NotificationType.RESOURCE_APPROVAL, "Resource Review Update",
            f"Your resource '{resource.title}' was marked as {payload.approval_status.value}.", auto_commit=False,
        )
        self.repo.commit()
        return resource

    def get_preview(self, resource_id: str, requesting_user_id: str | None) -> ResourcePreviewOut:
        resource = self.repo.get(resource_id)
        if not resource or resource.approval_status != ResourceApprovalStatus.APPROVED:
            raise NotFoundError("Resource not found.")

        requires_purchase = resource.is_premium and requesting_user_id is None
        kind = PREVIEWABLE_MIME.get(resource.mime_type, "video" if resource.resource_type.value == "VIDEO" else "unsupported")

        resource.view_count += 1
        self.db.add(resource)
        self.repo.commit()

        return ResourcePreviewOut(
            id=resource.id,
            title=resource.title,
            resource_type=resource.resource_type,
            mime_type=resource.mime_type,
            preview_kind=kind,
            preview_url=resource.file_url if not requires_purchase else "",
            is_premium=resource.is_premium,
            requires_purchase=requires_purchase,
        )

    def download_resource(self, user_id: str, resource_id: str) -> Resource:
        resource = self.repo.get(resource_id)
        if not resource or resource.approval_status != ResourceApprovalStatus.APPROVED:
            raise NotFoundError("Resource not found.")
        if resource.is_premium:
            # Premium gating placeholder: real implementation would check a purchase/subscription record.
            raise PaymentRequiredError("This is a premium resource. Upgrade your plan to download it.")

        self.repo.add_download(ResourceDownload(resource_id=resource.id, user_id=user_id))
        resource.download_count += 1
        self.db.add(resource)
        self.repo.commit()
        return resource
