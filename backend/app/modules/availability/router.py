from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.permissions import require_mentor
from app.database.session import get_db
from app.modules.availability.schemas import AvailabilitySlotCreate, AvailabilitySlotOut, AvailabilitySlotUpdate
from app.modules.availability.service import AvailabilityService
from app.modules.users.models import User

router = APIRouter(prefix="/availability", tags=["Availability"])


@router.post("", response_model=AvailabilitySlotOut, status_code=201)
def create_slot(payload: AvailabilitySlotCreate, current_user: User = Depends(require_mentor), db: Session = Depends(get_db)):
    return AvailabilityService(db).create_slot(current_user.id, payload)


@router.get("/me", response_model=list[AvailabilitySlotOut])
def my_slots(current_user: User = Depends(require_mentor), db: Session = Depends(get_db)):
    return AvailabilityService(db).list_my_slots(current_user.id)


@router.put("/{slot_id}", response_model=AvailabilitySlotOut)
def update_slot(
    slot_id: str, payload: AvailabilitySlotUpdate, current_user: User = Depends(require_mentor), db: Session = Depends(get_db)
):
    return AvailabilityService(db).update_slot(current_user.id, slot_id, payload)


@router.delete("/{slot_id}", status_code=204)
def delete_slot(slot_id: str, current_user: User = Depends(require_mentor), db: Session = Depends(get_db)):
    AvailabilityService(db).delete_slot(current_user.id, slot_id)


@router.get("/mentor/{mentor_id}", response_model=list[AvailabilitySlotOut])
def mentor_calendar(mentor_id: str, db: Session = Depends(get_db)):
    return AvailabilityService(db).list_mentor_slots(mentor_id)
