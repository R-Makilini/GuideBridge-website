from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.modules.availability.models import AvailabilitySlot
from app.modules.availability.repository import AvailabilityRepository
from app.modules.availability.schemas import AvailabilitySlotCreate, AvailabilitySlotUpdate
from app.modules.mentors.repository import MentorRepository


class AvailabilityService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AvailabilityRepository(db)
        self.mentor_repo = MentorRepository(db)

    def _get_mentor_or_403(self, user_id: str):
        mentor = self.mentor_repo.get_by_user_id(user_id)
        if not mentor:
            raise NotFoundError("Mentor profile not found.")
        return mentor

    def create_slot(self, user_id: str, payload: AvailabilitySlotCreate) -> AvailabilitySlot:
        mentor = self._get_mentor_or_403(user_id)

        if payload.slot_date < date.today():
            raise BadRequestError("Cannot create availability for a past date.")

        overlap = self.repo.get_overlapping(mentor.id, payload.slot_date, payload.start_time, payload.end_time)
        if overlap:
            raise ConflictError("This slot overlaps with an existing availability slot.")

        duration = (
            payload.end_time.hour * 60 + payload.end_time.minute
        ) - (payload.start_time.hour * 60 + payload.start_time.minute)

        slot = AvailabilitySlot(
            mentor_id=mentor.id,
            slot_date=payload.slot_date,
            start_time=payload.start_time,
            end_time=payload.end_time,
            duration_minutes=duration,
            session_fee=payload.session_fee,
        )
        self.repo.create(slot)
        self.repo.commit()
        return slot

    def update_slot(self, user_id: str, slot_id: str, payload: AvailabilitySlotUpdate) -> AvailabilitySlot:
        mentor = self._get_mentor_or_403(user_id)
        slot = self.repo.get(slot_id)
        if not slot or slot.mentor_id != mentor.id:
            raise NotFoundError("Availability slot not found.")

        data = payload.model_dump(exclude_unset=True)
        new_start = data.get("start_time", slot.start_time)
        new_end = data.get("end_time", slot.end_time)

        if new_end <= new_start:
            raise BadRequestError("end_time must be after start_time")

        if "start_time" in data or "end_time" in data:
            overlap = self.repo.get_overlapping(mentor.id, slot.slot_date, new_start, new_end, exclude_id=slot.id)
            if overlap:
                raise ConflictError("This slot overlaps with an existing availability slot.")
            slot.duration_minutes = (new_end.hour * 60 + new_end.minute) - (new_start.hour * 60 + new_start.minute)

        for field, value in data.items():
            setattr(slot, field, value)

        self.db.add(slot)
        self.repo.commit()
        return slot

    def delete_slot(self, user_id: str, slot_id: str) -> None:
        mentor = self._get_mentor_or_403(user_id)
        slot = self.repo.get(slot_id)
        if not slot or slot.mentor_id != mentor.id:
            raise NotFoundError("Availability slot not found.")
        if slot.booking is not None:
            raise ConflictError("Cannot delete a slot that already has a booking. Cancel the booking first.")
        self.repo.delete(slot)
        self.repo.commit()

    def list_mentor_slots(self, mentor_id: str, only_available: bool = True):
        return self.repo.list_for_mentor(mentor_id, from_date=date.today(), only_available=only_available)

    def list_my_slots(self, user_id: str):
        mentor = self._get_mentor_or_403(user_id)
        return self.repo.list_for_mentor(mentor.id)
