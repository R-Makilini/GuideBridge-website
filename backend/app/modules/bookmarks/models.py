from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import BookmarkTargetType
from app.database.base import Base
from app.database.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Bookmark(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "bookmarks"
    __table_args__ = (
        UniqueConstraint("user_id", "target_type", "target_id", name="uq_bookmark_user_target"),
    )

    user_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    target_type: Mapped[BookmarkTargetType] = mapped_column(nullable=False)
    target_id: Mapped[str] = mapped_column(CHAR(36), nullable=False)

    user = relationship("User")
