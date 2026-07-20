from datetime import date

from sqlalchemy.orm import Session

from app.modules.availability.models import AvailabilitySlot


class AvailabilityRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, slot_id: str) -> AvailabilitySlot | None:
        return self.db.query(AvailabilitySlot).filter(AvailabilitySlot.id == slot_id).first()

    def get_overlapping(self, mentor_id: str, slot_date: date, start_time, end_time, exclude_id: str | None = None):
        query = self.db.query(AvailabilitySlot).filter(
            AvailabilitySlot.mentor_id == mentor_id,
            AvailabilitySlot.slot_date == slot_date,
            AvailabilitySlot.start_time < end_time,
            AvailabilitySlot.end_time > start_time,
        )
        if exclude_id:
            query = query.filter(AvailabilitySlot.id != exclude_id)
        return query.first()

    def list_for_mentor(self, mentor_id: str, from_date: date | None = None, only_available: bool = False):
        query = self.db.query(AvailabilitySlot).filter(AvailabilitySlot.mentor_id == mentor_id)
        if from_date:
            query = query.filter(AvailabilitySlot.slot_date >= from_date)
        if only_available:
            query = query.filter(
                AvailabilitySlot.is_available.is_(True), AvailabilitySlot.is_blocked.is_(False)
            )
        return query.order_by(AvailabilitySlot.slot_date, AvailabilitySlot.start_time).all()

    def create(self, slot: AvailabilitySlot) -> AvailabilitySlot:
        self.db.add(slot)
        self.db.flush()
        return slot

    def delete(self, slot: AvailabilitySlot) -> None:
        self.db.delete(slot)

    def commit(self):
        self.db.commit()
