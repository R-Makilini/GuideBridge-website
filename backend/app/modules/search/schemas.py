from typing import Optional

from pydantic import BaseModel

from app.modules.mentors.schemas import PublicMentorProfileOut


class MentorSearchParams(BaseModel):
    name: Optional[str] = None
    university_id: Optional[str] = None
    faculty_id: Optional[str] = None
    degree_id: Optional[str] = None
    stream_id: Optional[str] = None
    subject_id: Optional[str] = None
    expertise_tag_id: Optional[str] = None
    language: Optional[str] = None
    sort_by: str = "helpful"  # helpful | experienced | newest
    page: int = 1
    page_size: int = 20
