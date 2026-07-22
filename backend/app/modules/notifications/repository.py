from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.notifications.models import Notification


class NotificationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, notification: Notification) -> Notification:
        self.db.add(notification)
        self.db.flush()
        return notification

    CATEGORY_TYPE_MAP = {
        "booking": ["BOOKING_CREATED", "BOOKING_ACCEPTED", "BOOKING_REJECTED", "BOOKING_CANCELLED", "BOOKING_RESCHEDULED", "SESSION_REMINDER"],
        "payment": ["PAYMENT_SUCCESS", "PAYMENT_FAILURE"],
        "verification": ["MENTOR_VERIFICATION", "EMAIL_VERIFICATION"],
        "message": ["NEW_MESSAGE"],
        "system": ["REGISTRATION", "ADMIN_ANNOUNCEMENT", "NEW_ANSWER", "HELPFUL_VOTE", "RESOURCE_APPROVAL"],
    }

    def list_for_user(self, user_id: str, page: int, page_size: int, category: str | None = None):
        query = (
            self.db.query(Notification)
            .filter(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
        )
        if category and category in self.CATEGORY_TYPE_MAP:
            query = query.filter(Notification.type.in_(self.CATEGORY_TYPE_MAP[category]))
        total = query.order_by(None).with_entities(func.count()).scalar() or 0
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def unread_count(self, user_id: str) -> int:
        return (
            self.db.query(func.count(Notification.id))
            .filter(Notification.user_id == user_id, Notification.is_read.is_(False))
            .scalar()
            or 0
        )

    def mark_read(self, notification_id: str, user_id: str) -> Notification | None:
        notif = (
            self.db.query(Notification)
            .filter(Notification.id == notification_id, Notification.user_id == user_id)
            .first()
        )
        if notif:
            notif.is_read = True
            self.db.add(notif)
        return notif

    def mark_all_read(self, user_id: str) -> None:
        self.db.query(Notification).filter(
            Notification.user_id == user_id, Notification.is_read.is_(False)
        ).update({"is_read": True})

    def commit(self):
        self.db.commit()
