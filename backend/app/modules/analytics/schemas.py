from pydantic import BaseModel


class MonthlyPoint(BaseModel):
    month: str  
    value: float


class AnalyticsSeriesOut(BaseModel):
    user_growth: list[MonthlyPoint]
    mentor_growth: list[MonthlyPoint]
    booking_counts: list[MonthlyPoint]
    revenue: list[MonthlyPoint]
    mentor_earnings: list[MonthlyPoint]


class PlatformStatsOut(BaseModel):
    total_students: int
    total_mentors: int
    total_sessions_completed: int
    total_questions_answered: int


class FeaturedMentorOut(BaseModel):
    id: str
    full_name: str
    profile_picture_url: str | None = None
    biography: str | None = None
    helpful_score: int
    average_rating: float


class PopularSubjectOut(BaseModel):
    id: str
    name: str
    question_count: int


class LatestResourceOut(BaseModel):
    id: str
    title: str
    resource_type: str
    created_at: str
