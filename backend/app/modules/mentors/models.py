from sqlalchemy import Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import VerificationStatus
from app.database.base import Base
from app.database.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class MentorProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "mentor_profiles"

    user_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    university_id: Mapped[str | None] = mapped_column(
        CHAR(36), ForeignKey("universities.id", ondelete="SET NULL"), nullable=True
    )
    faculty_id: Mapped[str | None] = mapped_column(
        CHAR(36), ForeignKey("faculties.id", ondelete="SET NULL"), nullable=True
    )
    department_id: Mapped[str | None] = mapped_column(
        CHAR(36), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )
    degree_id: Mapped[str | None] = mapped_column(
        CHAR(36), ForeignKey("degrees.id", ondelete="SET NULL"), nullable=True
    )
    academic_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    biography: Mapped[str | None] = mapped_column(Text, nullable=True)
    skills: Mapped[str | None] = mapped_column(String(500), nullable=True)
    achievements: Mapped[str | None] = mapped_column(Text, nullable=True)
    certificates_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    verification_status: Mapped[VerificationStatus] = mapped_column(default=VerificationStatus.PENDING)
    is_publicly_visible: Mapped[bool] = mapped_column(default=False)
    helpful_score: Mapped[int] = mapped_column(Integer, default=0)
    completed_session_count: Mapped[int] = mapped_column(Integer, default=0)
    average_rating: Mapped[float] = mapped_column(Float, default=0.0)

    user = relationship("User", back_populates="mentor_profile")
    university = relationship("University")
    faculty = relationship("Faculty")
    department = relationship("Department")
    degree = relationship("Degree")
    subjects = relationship("MentorSubject", back_populates="mentor", cascade="all, delete-orphan")
    expertise_tags = relationship(
        "MentorExpertiseTag", back_populates="mentor", cascade="all, delete-orphan"
    )
    languages = relationship("MentorLanguage", back_populates="mentor", cascade="all, delete-orphan")
    verification_documents = relationship(
        "VerificationDocument", back_populates="mentor", cascade="all, delete-orphan"
    )

    @property
    def profile_completion_percentage(self) -> int:
        fields = [
            self.university_id,
            self.faculty_id,
            self.degree_id,
            self.academic_year,
            self.biography,
            self.skills,
        ]
        filled = sum(1 for f in fields if f)
        return int((filled / len(fields)) * 100)


class MentorSubject(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "mentor_subjects"
    __table_args__ = (UniqueConstraint("mentor_id", "subject_id", name="uq_mentor_subject"),)

    mentor_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("mentor_profiles.id", ondelete="CASCADE"))
    subject_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("subjects.id", ondelete="CASCADE"))

    mentor = relationship("MentorProfile", back_populates="subjects")
    subject = relationship("Subject")


class MentorExpertiseTag(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "mentor_expertise_tags"
    __table_args__ = (UniqueConstraint("mentor_id", "tag_id", name="uq_mentor_tag"),)

    mentor_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("mentor_profiles.id", ondelete="CASCADE"))
    tag_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("expertise_tags.id", ondelete="CASCADE"))

    mentor = relationship("MentorProfile", back_populates="expertise_tags")
    tag = relationship("ExpertiseTag")


class MentorLanguage(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "mentor_languages"
    __table_args__ = (UniqueConstraint("mentor_id", "language", name="uq_mentor_language"),)

    mentor_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("mentor_profiles.id", ondelete="CASCADE"))
    language: Mapped[str] = mapped_column(String(50), nullable=False)

    mentor = relationship("MentorProfile", back_populates="languages")


class MentorRegistrationProgress(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "mentor_registration_progress"

    mentor_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("mentor_profiles.id", ondelete="CASCADE"), unique=True)
    personal_info_completed: Mapped[bool] = mapped_column(default=False)
    university_info_completed: Mapped[bool] = mapped_column(default=False)
    documents_uploaded: Mapped[bool] = mapped_column(default=False)

    mentor = relationship("MentorProfile")

    @property
    def completion_percentage(self) -> int:
        steps = [self.personal_info_completed, self.university_info_completed, self.documents_uploaded]
        return int((sum(1 for s in steps if s) / len(steps)) * 100)
