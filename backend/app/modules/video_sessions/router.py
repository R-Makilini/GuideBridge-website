from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.constants import UserRole
from app.core.permissions import require_roles
from app.database.session import get_db
from app.modules.video_sessions.schemas import JoinDetailsOut, SessionNotesUpdate, VideoSessionOut
from app.modules.video_sessions.service import VideoSessionService
from app.modules.users.models import User

router = APIRouter(prefix="/video-sessions", tags=["Video Sessions"])
require_student_or_mentor = require_roles(UserRole.STUDENT, UserRole.MENTOR)


@router.get("/{booking_id}/join", response_model=JoinDetailsOut)
def join_session(booking_id: str, current_user: User = Depends(require_student_or_mentor), db: Session = Depends(get_db)):
    return VideoSessionService(db).get_join_details(current_user.id, current_user.full_name, booking_id)


@router.post("/{booking_id}/start", response_model=VideoSessionOut)
def start_session(booking_id: str, current_user: User = Depends(require_student_or_mentor), db: Session = Depends(get_db)):
    return VideoSessionService(db).start_session(current_user.id, booking_id)


@router.post("/{booking_id}/end", response_model=VideoSessionOut)
def end_session(booking_id: str, payload: SessionNotesUpdate | None = None, current_user: User = Depends(require_student_or_mentor), db: Session = Depends(get_db)):
    notes = payload.session_notes if payload else None
    return VideoSessionService(db).end_session(current_user.id, booking_id, notes)


@router.get("/history/me", response_model=list[VideoSessionOut])
def my_session_history(current_user: User = Depends(require_student_or_mentor), db: Session = Depends(get_db)):
    return VideoSessionService(db).history(current_user.id)
