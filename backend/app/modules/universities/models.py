from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.database.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class University(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "universities"

    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    short_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)

    faculties = relationship("Faculty", back_populates="university", cascade="all, delete-orphan")


class Faculty(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "faculties"
    __table_args__ = (UniqueConstraint("university_id", "name", name="uq_faculty_university_name"),)

    university_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("universities.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    university = relationship("University", back_populates="faculties")
    departments = relationship("Department", back_populates="faculty", cascade="all, delete-orphan")


class Department(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "departments"
    __table_args__ = (UniqueConstraint("faculty_id", "name", name="uq_department_faculty_name"),)

    faculty_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("faculties.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    faculty = relationship("Faculty", back_populates="departments")
    degrees = relationship("Degree", back_populates="department", cascade="all, delete-orphan")


class Degree(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "degrees"
    __table_args__ = (UniqueConstraint("department_id", "name", name="uq_degree_department_name"),)

    department_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("departments.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    department = relationship("Department", back_populates="degrees")


class Stream(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "streams"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)


class Subject(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "subjects"

    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    stream_id: Mapped[str | None] = mapped_column(
        CHAR(36), ForeignKey("streams.id", ondelete="SET NULL"), nullable=True
    )

    stream = relationship("Stream")


class ExpertiseTag(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "expertise_tags"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
