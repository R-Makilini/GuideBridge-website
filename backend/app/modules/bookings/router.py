from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.constants import BookingStatus, UserRole
from app.core.pagination import PaginatedResponse, PageMeta
from app.core.permissions import require_mentor, require_student, require_student_or_admin, require_roles
from app.database.session import get_db
from app.modules.bookings.schemas import (
    BookingCancel,
    BookingCreate,
    BookingOut,
    BookingReschedule,
    BookingStatusHistoryOut,
)
from app.modules.bookings.service import BookingService
from app.modules.users.models import User

router = APIRouter(prefix="/bookings", tags=["Bookings"])
require_student_or_mentor = require_roles(UserRole.STUDENT, UserRole.MENTOR)


@router.post("", response_model=BookingOut, status_code=201)
def create_booking(payload: BookingCreate, current_user: User = Depends(require_student), db: Session = Depends(get_db)):
    return BookingService(db).create_booking(current_user.id, payload)


@router.post("/{booking_id}/accept", response_model=BookingOut)
def accept_booking(booking_id: str, current_user: User = Depends(require_mentor), db: Session = Depends(get_db)):
    return BookingService(db).accept_booking(current_user.id, booking_id)


@router.post("/{booking_id}/reject", response_model=BookingOut)
def reject_booking(
    booking_id: str, payload: BookingCancel, current_user: User = Depends(require_mentor), db: Session = Depends(get_db)
):
    return BookingService(db).reject_booking(current_user.id, booking_id, payload.reason)


@router.post("/{booking_id}/cancel", response_model=BookingOut)
def cancel_booking(
    booking_id: str, payload: BookingCancel, current_user: User = Depends(require_student_or_mentor), db: Session = Depends(get_db)
):
    role = "student" if current_user.role == UserRole.STUDENT else "mentor"
    return BookingService(db).cancel_booking(current_user.id, role, booking_id, payload.reason)


@router.post("/{booking_id}/complete", response_model=BookingOut)
def complete_booking(booking_id: str, current_user: User = Depends(require_mentor), db: Session = Depends(get_db)):
    return BookingService(db).complete_booking(current_user.id, booking_id)


@router.post("/{booking_id}/no-show", response_model=BookingOut)
def mark_no_show(booking_id: str, current_user: User = Depends(require_mentor), db: Session = Depends(get_db)):
    return BookingService(db).mark_no_show(current_user.id, booking_id)


@router.post("/{booking_id}/reschedule", response_model=BookingOut)
def reschedule_booking(
    booking_id: str, payload: BookingReschedule, current_user: User = Depends(require_student_or_mentor), db: Session = Depends(get_db)
):
    role = "student" if current_user.role == UserRole.STUDENT else "mentor"
    return BookingService(db).reschedule_booking(current_user.id, role, booking_id, payload.new_slot_id)


@router.get("/{booking_id}", response_model=BookingOut)
def get_booking(booking_id: str, current_user: User = Depends(require_student_or_mentor), db: Session = Depends(get_db)):
    role = "student" if current_user.role == UserRole.STUDENT else "mentor"
    return BookingService(db).get_booking_detail(booking_id, current_user.id, role)


def _categorize(items, category: str | None):
    if not category:
        return items
    mapping = {
        "upcoming": {BookingStatus.CONFIRMED, BookingStatus.ACCEPTED, BookingStatus.PENDING, BookingStatus.PAYMENT_PENDING},
        "completed": {BookingStatus.COMPLETED},
        "cancelled": {BookingStatus.CANCELLED, BookingStatus.REJECTED, BookingStatus.NO_SHOW},
        "rescheduled": {BookingStatus.RESCHEDULED},
    }
    allowed = mapping.get(category)
    if not allowed:
        return items
    return [b for b in items if b.status in allowed]


@router.get("/history/me", response_model=PaginatedResponse[BookingOut])
def my_booking_history(
    category: str | None = Query(None, description="upcoming|completed|cancelled|rescheduled"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_student_or_mentor),
    db: Session = Depends(get_db),
):
    service = BookingService(db)
    if current_user.role == UserRole.STUDENT:
        items, total = service.list_for_student(current_user.id, page, page_size)
    else:
        items, total = service.list_for_mentor(current_user.id, page, page_size)

    items = _categorize(items, category)
    total = len(items) if category else total
    total_pages = (total + page_size - 1) // page_size if total else 0
    meta = PageMeta(page=page, page_size=page_size, total_items=total, total_pages=total_pages)
    return PaginatedResponse(items=items, meta=meta)
