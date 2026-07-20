from typing import Optional

from pydantic import BaseModel


class MentorProfileUpdate(BaseModel):
    university_id: Optional[str] = None
    faculty_id: Optional[str] = None
    department_id: Optional[str] = None
    degree_id: Optional[str] = None
    academic_year: Optional[int] = None
    biography: Optional[str] = None
    skills: Optional[str] = None
    achievements: Optional[str] = None
    subject_ids: Optional[list[str]] = None
    expertise_tag_ids: Optional[list[str]] = None
    languages: Optional[list[str]] = None


class MentorProfileOut(BaseModel):
    id: str
    user_id: str
    university_id: Optional[str] = None
    faculty_id: Optional[str] = None
    department_id: Optional[str] = None
    degree_id: Optional[str] = None
    academic_year: Optional[int] = None
    biography: Optional[str] = None
    skills: Optional[str] = None
    achievements: Optional[str] = None
    verification_status: str
    is_publicly_visible: bool
    helpful_score: int
    completed_session_count: int
    average_rating: float
    profile_completion_percentage: int

    model_config = {"from_attributes": True}


class PublicMentorProfileOut(BaseModel):
    id: str
    full_name: str
    profile_picture_url: Optional[str] = None
    university_id: Optional[str] = None
    faculty_id: Optional[str] = None
    degree_id: Optional[str] = None
    academic_year: Optional[int] = None
    biography: Optional[str] = None
    skills: Optional[str] = None
    achievements: Optional[str] = None
    helpful_score: int
    completed_session_count: int
    average_rating: float
    is_verified: bool

    model_config = {"from_attributes": True}


class RegistrationProgressUpdate(BaseModel):
    personal_info_completed: Optional[bool] = None
    university_info_completed: Optional[bool] = None
    documents_uploaded: Optional[bool] = None


class RegistrationProgressOut(BaseModel):
    mentor_id: str
    personal_info_completed: bool
    university_info_completed: bool
    documents_uploaded: bool
    completion_percentage: int

    model_config = {"from_attributes": True}


class MentorDashboardOut(BaseModel):
    total_bookings: int
    upcoming_bookings: int
    completed_sessions: int
    total_answers_given: int
    helpful_score: int
    average_rating: float
    profile_completion_percentage: int
    verification_status: str


class MentorEarningsSummaryOut(BaseModel):
    total_earnings: float
    pending_earnings: float
    completed_payment_count: int
    last_payout_amount: float | None = None
