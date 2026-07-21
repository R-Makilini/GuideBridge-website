from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.pagination import PaginatedResponse
from app.database.session import get_db
from app.modules.mentors.schemas import PublicMentorProfileOut
from app.modules.search.schemas import MentorSearchParams
from app.modules.search.service import MentorSearchService

router = APIRouter(prefix="/search", tags=["Mentor Search"])


@router.get("/mentors", response_model=PaginatedResponse[PublicMentorProfileOut])
def search_mentors(params: MentorSearchParams = Depends(), db: Session = Depends(get_db)):
    items, meta = MentorSearchService(db).search(params)
    out_items = [
        PublicMentorProfileOut(
            id=m.id,
            full_name=m.user.full_name,
            profile_picture_url=m.user.profile_picture_url,
            university_id=m.university_id,
            faculty_id=m.faculty_id,
            degree_id=m.degree_id,
            academic_year=m.academic_year,
            biography=m.biography,
            skills=m.skills,
            achievements=m.achievements,
            helpful_score=m.helpful_score,
            completed_session_count=m.completed_session_count,
            average_rating=m.average_rating,
            is_verified=True,
        )
        for m in items
    ]
    return PaginatedResponse(items=out_items, meta=meta)
