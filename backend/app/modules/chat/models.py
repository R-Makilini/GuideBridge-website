from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.database.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Conversation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "conversations"

    student_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("users.id", ondelete="CASCADE"))
    mentor_user_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("users.id", ondelete="CASCADE"))
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    __table_args__ = (UniqueConstraint("student_id", "mentor_user_id", name="uq_conversation_pair"),)

    members = relationship("ConversationMember", back_populates="conversation", cascade="all, delete-orphan")
    messages = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at"
    )


class ConversationMember(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "conversation_members"
    __table_args__ = (UniqueConstraint("conversation_id", "user_id", name="uq_conv_member"),)

    conversation_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("conversations.id", ondelete="CASCADE"))
    user_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("users.id", ondelete="CASCADE"))
    last_read_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_online: Mapped[bool] = mapped_column(Boolean, default=False)

    conversation = relationship("Conversation", back_populates="members")
    user = relationship("User")


class Message(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "messages"

    conversation_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("conversations.id", ondelete="CASCADE"))
    sender_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("users.id", ondelete="CASCADE"))
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_seen: Mapped[bool] = mapped_column(Boolean, default=False)
    seen_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("User")
    attachments = relationship(
        "MessageAttachment", back_populates="message", cascade="all, delete-orphan"
    )


class MessageAttachment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "message_attachments"

    message_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("messages.id", ondelete="CASCADE"))
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(nullable=False)

    message = relationship("Message", back_populates="attachments")
