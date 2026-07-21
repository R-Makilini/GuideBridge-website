from sqlalchemy.orm import Session

from app.core.constants import BookmarkTargetType
from app.core.exceptions import ConflictError, NotFoundError
from app.modules.bookmarks.models import Bookmark
from app.modules.bookmarks.repository import BookmarkRepository
from app.modules.bookmarks.schemas import BookmarkCreate


class BookmarkService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = BookmarkRepository(db)

    def add_bookmark(self, user_id: str, payload: BookmarkCreate) -> Bookmark:
        existing = self.repo.get(user_id, payload.target_type, payload.target_id)
        if existing:
            raise ConflictError("This item is already bookmarked.")
        bookmark = self.repo.create(Bookmark(user_id=user_id, **payload.model_dump()))
        self.repo.commit()
        return bookmark

    def remove_bookmark(self, user_id: str, target_type: BookmarkTargetType, target_id: str) -> None:
        bookmark = self.repo.get(user_id, target_type, target_id)
        if not bookmark:
            raise NotFoundError("Bookmark not found.")
        self.repo.delete(bookmark)
        self.repo.commit()

    def list_bookmarks(self, user_id: str, target_type: BookmarkTargetType | None = None):
        return self.repo.list_for_user(user_id, target_type)
