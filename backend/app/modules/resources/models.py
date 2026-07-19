from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import ResourceApprovalStatus, ResourceType
from app.database.base import Base
from app.database.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Resource(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "resources"

    uploaded_by_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("users.id", ondelete="CASCADE"))
    subject_id: Mapped[str | None] = mapped_column(
        CHAR(36), ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    resource_type: Mapped[ResourceType] = mapped_column(nullable=False)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(nullable=False)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    approval_status: Mapped[ResourceApprovalStatus] = mapped_column(default=ResourceApprovalStatus.PENDING)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    download_count: Mapped[int] = mapped_column(Integer, default=0)

    uploaded_by = relationship("User")
    subject = relationship("Subject")
    downloads = relationship("ResourceDownload", back_populates="resource", cascade="all, delete-orphan")


class ResourceDownload(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "resource_downloads"

    resource_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("resources.id", ondelete="CASCADE"))
    user_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("users.id", ondelete="CASCADE"))

    resource = relationship("Resource", back_populates="downloads")
    user = relationship("User")
