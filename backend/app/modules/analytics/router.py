from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.permissions import require_super_admin
from app.database.session import get_db
from app.modules.analytics.schemas import AnalyticsSeriesOut
from app.modules.analytics.service import AnalyticsService
from app.modules.users.models import User

router = APIRouter(prefix="/admin/analytics", tags=["Admin - Analytics"])


@router.get("/series", response_model=AnalyticsSeriesOut)
def analytics_series(current_user: User = Depends(require_super_admin), db: Session = Depends(get_db)):
    return AnalyticsService(db).get_series()
