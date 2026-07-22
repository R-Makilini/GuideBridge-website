from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.pagination import PaginatedResponse, PageMeta
from app.database.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.notifications.schemas import NotificationOut, UnreadCountOut
from app.modules.notifications.service import NotificationService
from app.modules.users.models import User

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=PaginatedResponse[NotificationOut])
def list_notifications(
    category: str | None = Query(None, description="booking|payment|verification|message|system"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = NotificationService(db)
    items, meta = service.list_for_user(current_user.id, page, page_size, category)
    return PaginatedResponse(items=items, meta=meta)


@router.get("/unread-count", response_model=UnreadCountOut)
def unread_count(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    service = NotificationService(db)
    return UnreadCountOut(unread_count=service.unread_count(current_user.id))


@router.post("/{notification_id}/read", response_model=NotificationOut)
def mark_read(notification_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    service = NotificationService(db)
    return service.mark_read(notification_id, current_user.id)


@router.post("/mark-all-read", status_code=204)
def mark_all_read(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    service = NotificationService(db)
    service.mark_all_read(current_user.id)
