from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.constants import UserRole
from app.core.permissions import require_roles, require_super_admin
from app.database.session import get_db
from app.modules.feedback.schemas import FeedbackCreate, FeedbackModerationRequest, FeedbackOut
from app.modules.feedback.service import FeedbackService
from app.modules.users.models import User

router = APIRouter(prefix="/feedback", tags=["Session Feedback"])
require_student_or_mentor = require_roles(UserRole.STUDENT, UserRole.MENTOR)


@router.post("/bookings/{booking_id}", response_model=FeedbackOut, status_code=201)
def submit_feedback(booking_id: str, payload: FeedbackCreate, current_user: User = Depends(require_student_or_mentor), db: Session = Depends(get_db)):
    return FeedbackService(db).submit_feedback(current_user.id, current_user.role, booking_id, payload)


@router.get("/bookings/{booking_id}", response_model=list[FeedbackOut])
def list_feedback(booking_id: str, db: Session = Depends(get_db)):
    return FeedbackService(db).list_for_booking(booking_id)


@router.get("/flagged", response_model=list[FeedbackOut])
def list_flagged(current_user: User = Depends(require_super_admin), db: Session = Depends(get_db)):
    return FeedbackService(db).list_flagged()


@router.post("/{feedback_id}/moderate", response_model=FeedbackOut)
def moderate(feedback_id: str, payload: FeedbackModerationRequest, current_user: User = Depends(require_super_admin), db: Session = Depends(get_db)):
    return FeedbackService(db).moderate(feedback_id, payload)
