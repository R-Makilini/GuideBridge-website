from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.constants import ReportStatus
from app.core.permissions import require_any_authenticated, require_super_admin
from app.database.session import get_db
from app.modules.reports.schemas import BlockUserRequest, ReportCreate, ReportOut, ReportReviewRequest
from app.modules.reports.service import ReportService
from app.modules.users.models import User

router = APIRouter(prefix="/reports", tags=["Reports & Safety"])


@router.post("", response_model=ReportOut, status_code=201)
def create_report(payload: ReportCreate, current_user: User = Depends(require_any_authenticated), db: Session = Depends(get_db)):
    return ReportService(db).create_report(current_user.id, payload)


@router.get("", response_model=list[ReportOut])
def list_reports(status: ReportStatus | None = Query(None), current_user: User = Depends(require_super_admin), db: Session = Depends(get_db)):
    return ReportService(db).list_reports(status)


@router.post("/{report_id}/review", response_model=ReportOut)
def review_report(report_id: str, payload: ReportReviewRequest, current_user: User = Depends(require_super_admin), db: Session = Depends(get_db)):
    return ReportService(db).review_report(report_id, payload)


@router.post("/block", status_code=201)
def block_user(payload: BlockUserRequest, current_user: User = Depends(require_any_authenticated), db: Session = Depends(get_db)):
    ReportService(db).block_user(current_user.id, payload.blocked_id)
    return {"blocked": True}


@router.post("/unblock", status_code=204)
def unblock_user(payload: BlockUserRequest, current_user: User = Depends(require_any_authenticated), db: Session = Depends(get_db)):
    ReportService(db).unblock_user(current_user.id, payload.blocked_id)
