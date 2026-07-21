from sqlalchemy.orm import Session

from app.core.constants import BookmarkTargetType
from app.modules.bookmarks.models import Bookmark


class BookmarkRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, user_id: str, target_type: BookmarkTargetType, target_id: str) -> Bookmark | None:
        return (
            self.db.query(Bookmark)
            .filter(Bookmark.user_id == user_id, Bookmark.target_type == target_type, Bookmark.target_id == target_id)
            .first()
        )

    def create(self, bookmark: Bookmark) -> Bookmark:
        self.db.add(bookmark)
        self.db.flush()
        return bookmark

    def list_for_user(self, user_id: str, target_type: BookmarkTargetType | None = None):
        query = self.db.query(Bookmark).filter(Bookmark.user_id == user_id)
        if target_type:
            query = query.filter(Bookmark.target_type == target_type)
        return query.order_by(Bookmark.created_at.desc()).all()

    def delete(self, bookmark: Bookmark) -> None:
        self.db.delete(bookmark)

    def commit(self):
        self.db.commit()
