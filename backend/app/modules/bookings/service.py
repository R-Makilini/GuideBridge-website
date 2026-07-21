from datetime import date, datetime, timezone
from app.core.datetime_utils import utcnow

from sqlalchemy.orm import Session

from app.core.constants import BookingStatus, NotificationType
from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.modules.bookings.models import Booking, BookingStatusHistory
from app.modules.bookings.repository import BookingRepository
from app.modules.bookings.schemas import BookingCreate
from app.modules.mentors.repository import MentorRepository
from app.modules.notifications.service import NotificationService

TERMINAL_STATUSES = {BookingStatus.CANCELLED, BookingStatus.COMPLETED, BookingStatus.REJECTED, BookingStatus.NO_SHOW}

VALID_TRANSITIONS: dict[BookingStatus, set[BookingStatus]] = {
    BookingStatus.PENDING: {BookingStatus.PAYMENT_PENDING, BookingStatus.CANCELLED, BookingStatus.REJECTED},
    BookingStatus.PAYMENT_PENDING: {BookingStatus.CONFIRMED, BookingStatus.CANCELLED},
    BookingStatus.CONFIRMED: {BookingStatus.ACCEPTED, BookingStatus.CANCELLED, BookingStatus.RESCHEDULED},
    BookingStatus.ACCEPTED: {
        BookingStatus.COMPLETED,
        BookingStatus.CANCELLED,
        BookingStatus.NO_SHOW,
        BookingStatus.RESCHEDULED,
    },
    BookingStatus.RESCHEDULED: {BookingStatus.CONFIRMED, BookingStatus.CANCELLED},
}


class BookingService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = BookingRepository(db)
        self.mentor_repo = MentorRepository(db)
        self.notifications = NotificationService(db)

    def _transition(self, booking: Booking, to_status: BookingStatus, changed_by_id: str, reason: str | None = None):
        allowed = VALID_TRANSITIONS.get(booking.status, set())
        if to_status not in allowed:
            raise ConflictError(f"Cannot move booking from {booking.status.value} to {to_status.value}.")

        history = BookingStatusHistory(
            booking_id=booking.id,
            from_status=booking.status,
            to_status=to_status,
            changed_by_id=changed_by_id,
            reason=reason,
        )
        self.repo.add_status_history(history)
        booking.status = to_status
        self.db.add(booking)

    def create_booking(self, student_id: str, payload: BookingCreate) -> Booking:
        slot = self.repo.get_slot_for_update(payload.slot_id)
        if not slot:
            raise NotFoundError("Availability slot not found.")

        mentor = self.mentor_repo.get_by_id(slot.mentor_id)
        if not mentor:
            raise NotFoundError("Mentor not found.")

        if mentor.user_id == student_id:
            raise BadRequestError("Mentors cannot book their own sessions.")

        if slot.slot_date < date.today():
            raise BadRequestError("Cannot book a slot in the past.")

        if not slot.is_available or slot.is_blocked:
            raise ConflictError("This slot is not available for booking.")

        if slot.booking is not None:
            raise ConflictError("This slot has already been booked.")

        booking = Booking(
            student_id=student_id,
            mentor_id=mentor.id,
            slot_id=slot.id,
            status=BookingStatus.PENDING,
            topic=payload.topic,
            notes=payload.notes,
            fee=slot.session_fee,
        )
        self.repo.create(booking)

        slot.is_available = False
        self.db.add(slot)

        history = BookingStatusHistory(
            booking_id=booking.id, from_status=None, to_status=BookingStatus.PENDING, changed_by_id=student_id
        )
        self.repo.add_status_history(history)

        self.notifications.notify(
            user_id=mentor.user_id,
            type_=NotificationType.BOOKING_CREATED,
            title="New Booking Request",
            body=f"You have a new booking request for {slot.slot_date}.",
            auto_commit=False,
        )

        try:
            self.repo.commit()
        except Exception:
            self.repo.rollback()
            raise

        return booking

    def _get_owned_booking(self, booking_id: str, user_id: str, role: str) -> Booking:
        booking = self.repo.get_for_update(booking_id)
        if not booking:
            raise NotFoundError("Booking not found.")
        if role == "student" and booking.student_id != user_id:
            raise ForbiddenError("This booking does not belong to you.")
        if role == "mentor":
            mentor = self.mentor_repo.get_by_user_id(user_id)
            if not mentor or booking.mentor_id != mentor.id:
                raise ForbiddenError("This booking does not belong to you.")
        return booking

    def accept_booking(self, mentor_user_id: str, booking_id: str) -> Booking:
        booking = self._get_owned_booking(booking_id, mentor_user_id, "mentor")
        if booking.status != BookingStatus.CONFIRMED:
            raise ConflictError("Only confirmed (paid) bookings can be accepted by the mentor.")
        self._transition(booking, BookingStatus.ACCEPTED, mentor_user_id)
        booking.confirmed_at = utcnow()
        self.notifications.notify(
            booking.student_id, NotificationType.BOOKING_ACCEPTED, "Booking Accepted",
            "Your mentor has accepted your booking.", auto_commit=False,
        )
        self.repo.commit()
        return booking

    def reject_booking(self, mentor_user_id: str, booking_id: str, reason: str | None) -> Booking:
        booking = self._get_owned_booking(booking_id, mentor_user_id, "mentor")
        self._transition(booking, BookingStatus.REJECTED, mentor_user_id, reason)
        booking.cancelled_reason = reason
        self._release_slot(booking)
        self.notifications.notify(
            booking.student_id, NotificationType.BOOKING_REJECTED, "Booking Rejected",
            reason or "Your mentor rejected the booking.", auto_commit=False,
        )
        self.repo.commit()
        return booking

    def cancel_booking(self, user_id: str, role: str, booking_id: str, reason: str | None) -> Booking:
        booking = self._get_owned_booking(booking_id, user_id, role)
        if booking.status in TERMINAL_STATUSES:
            raise ConflictError("This booking is already in a terminal state and cannot be cancelled.")
        self._transition(booking, BookingStatus.CANCELLED, user_id, reason)
        booking.cancelled_reason = reason
        self._release_slot(booking)

        notify_user = booking.mentor.user_id if role == "student" else booking.student_id
        self.notifications.notify(
            notify_user, NotificationType.BOOKING_CANCELLED, "Booking Cancelled",
            reason or "A booking was cancelled.", auto_commit=False,
        )
        self.repo.commit()
        return booking

    def complete_booking(self, mentor_user_id: str, booking_id: str) -> Booking:
        booking = self._get_owned_booking(booking_id, mentor_user_id, "mentor")
        if booking.status != BookingStatus.ACCEPTED:
            raise ConflictError("Only accepted bookings can be marked as completed.")
        self._transition(booking, BookingStatus.COMPLETED, mentor_user_id)
        booking.completed_at = utcnow()

        mentor = self.mentor_repo.get_by_id(booking.mentor_id)
        mentor.completed_session_count += 1
        self.db.add(mentor)

        self.repo.commit()
        return booking

    def mark_no_show(self, mentor_user_id: str, booking_id: str) -> Booking:
        booking = self._get_owned_booking(booking_id, mentor_user_id, "mentor")
        if booking.status != BookingStatus.ACCEPTED:
            raise ConflictError("Only accepted bookings can be marked as no-show.")
        self._transition(booking, BookingStatus.NO_SHOW, mentor_user_id)
        self.repo.commit()
        return booking

    def reschedule_booking(self, user_id: str, role: str, booking_id: str, new_slot_id: str) -> Booking:
        booking = self._get_owned_booking(booking_id, user_id, role)
        if booking.status not in (BookingStatus.CONFIRMED, BookingStatus.ACCEPTED):
            raise ConflictError("Only confirmed or accepted bookings can be rescheduled.")

        new_slot = self.repo.get_slot_for_update(new_slot_id)
        if not new_slot or new_slot.mentor_id != booking.mentor_id:
            raise NotFoundError("New slot not found for this mentor.")
        if not new_slot.is_available or new_slot.is_blocked or new_slot.booking is not None:
            raise ConflictError("The selected new slot is not available.")

        old_slot = booking.slot
        old_slot.is_available = True
        self.db.add(old_slot)

        booking.slot_id = new_slot.id
        new_slot.is_available = False
        self.db.add(new_slot)

        self._transition(booking, BookingStatus.RESCHEDULED, user_id)
        self.notifications.notify(
            booking.mentor.user_id if role == "student" else booking.student_id,
            NotificationType.BOOKING_RESCHEDULED, "Booking Rescheduled",
            "A booking has been rescheduled.", auto_commit=False,
        )
        self.repo.commit()
        return booking

    def _release_slot(self, booking: Booking) -> None:
        slot = booking.slot
        if slot:
            slot.is_available = True
            self.db.add(slot)

    def list_for_student(self, student_id: str, page: int, page_size: int):
        return self.repo.list_for_student(student_id, page, page_size)

    def list_for_mentor(self, mentor_user_id: str, page: int, page_size: int):
        mentor = self.mentor_repo.get_by_user_id(mentor_user_id)
        if not mentor:
            raise NotFoundError("Mentor profile not found.")
        return self.repo.list_for_mentor(mentor.id, page, page_size)

    def get_booking_detail(self, booking_id: str, user_id: str, role: str) -> Booking:
        return self._get_owned_booking(booking_id, user_id, role)
