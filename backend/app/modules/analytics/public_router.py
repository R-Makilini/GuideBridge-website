from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.analytics.schemas import FeaturedMentorOut, PlatformStatsOut, PopularSubjectOut
from app.modules.analytics.service import AnalyticsService
from app.modules.resources.schemas import ResourceOut

router = APIRouter(prefix="/public", tags=["Public Landing Page"])


@router.get("/stats", response_model=PlatformStatsOut)
def platform_stats(db: Session = Depends(get_db)):
    return AnalyticsService(db).get_platform_stats()


@router.get("/featured-mentors", response_model=list[FeaturedMentorOut])
def featured_mentors(db: Session = Depends(get_db)):
    return AnalyticsService(db).get_featured_mentors()


@router.get("/popular-subjects", response_model=list[PopularSubjectOut])
def popular_subjects(db: Session = Depends(get_db)):
    return AnalyticsService(db).get_popular_subjects()


@router.get("/latest-resources", response_model=list[ResourceOut])
def latest_resources(db: Session = Depends(get_db)):
    return AnalyticsService(db).get_latest_resources()
