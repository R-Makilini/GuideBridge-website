from sqlalchemy.orm import Session

from app.modules.availability.models import AvailabilitySlot
from app.modules.bookings.models import Booking, BookingStatusHistory


class BookingRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_slot_for_update(self, slot_id: str) -> AvailabilitySlot | None:
        """Row-lock the slot to prevent concurrent double-booking."""
        return (
            self.db.query(AvailabilitySlot)
            .filter(AvailabilitySlot.id == slot_id)
            .with_for_update()
            .first()
        )

    def get(self, booking_id: str) -> Booking | None:
        return self.db.query(Booking).filter(Booking.id == booking_id).first()

    def get_for_update(self, booking_id: str) -> Booking | None:
        return self.db.query(Booking).filter(Booking.id == booking_id).with_for_update().first()

    def create(self, booking: Booking) -> Booking:
        self.db.add(booking)
        self.db.flush()
        return booking

    def add_status_history(self, history: BookingStatusHistory) -> None:
        self.db.add(history)

    def list_for_student(self, student_id: str, page: int, page_size: int):
        from sqlalchemy import func

        query = self.db.query(Booking).filter(Booking.student_id == student_id).order_by(Booking.created_at.desc())
        total = query.order_by(None).with_entities(func.count()).scalar() or 0
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def list_for_mentor(self, mentor_id: str, page: int, page_size: int):
        from sqlalchemy import func

        query = self.db.query(Booking).filter(Booking.mentor_id == mentor_id).order_by(Booking.created_at.desc())
        total = query.order_by(None).with_entities(func.count()).scalar() or 0
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def commit(self):
        self.db.commit()

    def rollback(self):
        self.db.rollback()
