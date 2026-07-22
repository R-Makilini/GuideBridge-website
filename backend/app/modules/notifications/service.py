from sqlalchemy.orm import Session

from app.core.constants import NotificationType
from app.core.exceptions import NotFoundError
from app.core.pagination import PageMeta
from app.modules.notifications.models import Notification
from app.modules.notifications.repository import NotificationRepository


class NotificationService:
    """
    Central place to create in-app notifications. Other modules (bookings,
    payments, chat, questions, resources, admin) call `notify()` so that
    notification-creation logic and unread-count bookkeeping live in one spot.
    """

    def __init__(self, db: Session):
        self.db = db
        self.repo = NotificationRepository(db)

    def notify(
        self,
        user_id: str,
        type_: NotificationType,
        title: str,
        body: str | None = None,
        link_url: str | None = None,
        auto_commit: bool = True,
    ) -> Notification:
        notification = Notification(user_id=user_id, type=type_, title=title, body=body, link_url=link_url)
        self.repo.create(notification)
        if auto_commit:
            self.repo.commit()
        return notification

    def list_for_user(self, user_id: str, page: int, page_size: int, category: str | None = None):
        items, total = self.repo.list_for_user(user_id, page, page_size, category)
        total_pages = (total + page_size - 1) // page_size if total else 0
        meta = PageMeta(page=page, page_size=page_size, total_items=total, total_pages=total_pages)
        return items, meta

    def unread_count(self, user_id: str) -> int:
        return self.repo.unread_count(user_id)

    def mark_read(self, notification_id: str, user_id: str) -> Notification:
        notif = self.repo.mark_read(notification_id, user_id)
        if not notif:
            raise NotFoundError("Notification not found.")
        self.repo.commit()
        return notif

    def mark_all_read(self, user_id: str) -> None:
        self.repo.mark_all_read(user_id)
        self.repo.commit()
