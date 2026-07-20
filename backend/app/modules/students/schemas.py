from typing import Optional

from pydantic import BaseModel


class StudentProfileUpdate(BaseModel):
    school: Optional[str] = None
    grade: Optional[str] = None
    stream_id: Optional[str] = None
    district: Optional[str] = None
    preferred_language: Optional[str] = None
    bio: Optional[str] = None


class StudentProfileOut(BaseModel):
    id: str
    user_id: str
    school: Optional[str] = None
    grade: Optional[str] = None
    stream_id: Optional[str] = None
    district: Optional[str] = None
    preferred_language: Optional[str] = None
    bio: Optional[str] = None

    model_config = {"from_attributes": True}


class StudentDashboardOut(BaseModel):
    total_bookings: int
    upcoming_bookings: int
    completed_sessions: int
    total_questions_asked: int
    saved_mentors: int
    total_payments: int
    saved_resources_count: int
    recent_questions: list[dict] = []
    upcoming_sessions: list[dict] = []
    recent_chats: list[dict] = []
