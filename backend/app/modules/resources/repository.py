from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.constants import ResourceApprovalStatus
from app.modules.resources.models import Resource, ResourceDownload


class ResourceRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, resource: Resource) -> Resource:
        self.db.add(resource)
        self.db.flush()
        return resource

    def get(self, resource_id: str) -> Resource | None:
        return self.db.query(Resource).filter(Resource.id == resource_id).first()

    def list_approved(self, page: int, page_size: int, resource_type=None, subject_id=None, search=None):
        query = self.db.query(Resource).filter(Resource.approval_status == ResourceApprovalStatus.APPROVED)
        if resource_type:
            query = query.filter(Resource.resource_type == resource_type)
        if subject_id:
            query = query.filter(Resource.subject_id == subject_id)
        if search:
            query = query.filter(or_(Resource.title.ilike(f"%{search}%"), Resource.description.ilike(f"%{search}%")))
        query = query.order_by(Resource.created_at.desc())
        total = query.order_by(None).with_entities(func.count()).scalar() or 0
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def list_pending(self):
        return self.db.query(Resource).filter(Resource.approval_status == ResourceApprovalStatus.PENDING).all()

    def add_download(self, download: ResourceDownload) -> None:
        self.db.add(download)

    def commit(self):
        self.db.commit()
