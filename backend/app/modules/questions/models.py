from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import QuestionVisibility
from app.database.base import Base
from app.database.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Question(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "questions"

    student_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    subject_id: Mapped[str | None] = mapped_column(
        CHAR(36), ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    visibility: Mapped[QuestionVisibility] = mapped_column(default=QuestionVisibility.PUBLIC)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    view_count: Mapped[int] = mapped_column(Integer, default=0)

    student = relationship("User")
    subject = relationship("Subject")
    attachments = relationship(
        "QuestionAttachment", back_populates="question", cascade="all, delete-orphan"
    )
    answers = relationship("Answer", back_populates="question", cascade="all, delete-orphan")

    def public_author_name(self) -> str:
        if self.visibility == QuestionVisibility.ANONYMOUS:
            return "Anonymous Student"
        return self.student.full_name if self.student else "Unknown"


class QuestionAttachment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "question_attachments"

    question_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("questions.id", ondelete="CASCADE"))
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)

    question = relationship("Question", back_populates="attachments")


class Answer(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "answers"

    question_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("questions.id", ondelete="CASCADE"))
    mentor_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("users.id", ondelete="CASCADE"))
    body: Mapped[str] = mapped_column(Text, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    helpful_count: Mapped[int] = mapped_column(Integer, default=0)

    question = relationship("Question", back_populates="answers")
    mentor = relationship("User")


class HelpfulVote(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "helpful_votes"
    __table_args__ = (UniqueConstraint("answer_id", "user_id", name="uq_helpful_vote_user_answer"),)

    answer_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("answers.id", ondelete="CASCADE"))
    user_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("users.id", ondelete="CASCADE"))

    answer = relationship("Answer")
    user = relationship("User")
