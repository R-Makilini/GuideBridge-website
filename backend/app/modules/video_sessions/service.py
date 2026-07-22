from datetime import datetime, timezone
from app.core.datetime_utils import utcnow

from sqlalchemy.orm import Session

from app.core.constants import BookingStatus, UserRole, VideoSessionStatus
from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.integrations.jitsi.service import build_join_url, generate_room_name
from app.modules.bookings.repository import BookingRepository
from app.modules.video_sessions.models import SessionAttendance, VideoSession
from app.modules.video_sessions.repository import VideoSessionRepository


class VideoSessionService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = VideoSessionRepository(db)
        self.booking_repo = BookingRepository(db)

    def _authorized_user_ids(self, booking) -> set[str]:
        return {booking.student_id, booking.mentor.user_id}

    def get_or_create_room(self, user_id: str, booking_id: str) -> VideoSession:
        booking = self.booking_repo.get(booking_id)
        if not booking:
            raise NotFoundError("Booking not found.")
        if user_id not in self._authorized_user_ids(booking):
            raise ForbiddenError("You are not authorized to join this session.")
        if booking.status != BookingStatus.ACCEPTED:
            raise ConflictError("Video sessions are only available for accepted bookings.")

        session = self.repo.get_by_booking(booking_id)
        if not session:
            session = VideoSession(booking_id=booking_id, room_name=generate_room_name(booking_id))
            self.repo.create(session)
            self.repo.commit()
        return session

    def get_join_details(self, user_id: str, display_name: str, booking_id: str) -> dict:
        session = self.get_or_create_room(user_id, booking_id)
        from app.core.config import settings

        return {
            "room_name": session.room_name,
            "join_url": build_join_url(session.room_name, display_name),
            "jitsi_domain": settings.JITSI_DOMAIN,
        }

    def start_session(self, user_id: str, booking_id: str) -> VideoSession:
        session = self.get_or_create_room(user_id, booking_id)
        if session.status == VideoSessionStatus.SCHEDULED:
            session.status = VideoSessionStatus.LIVE
            session.started_at = utcnow()
            self.db.add(session)
            self.repo.commit()

        existing = self.repo.get_attendance(session.id, user_id)
        if not existing:
            self.repo.add_attendance(SessionAttendance(video_session_id=session.id, user_id=user_id, joined_at=utcnow()))
        else:
            existing.joined_at = utcnow()
            self.db.add(existing)
        self.repo.commit()
        return session

    def end_session(self, user_id: str, booking_id: str, notes: str | None = None) -> VideoSession:
        booking = self.booking_repo.get(booking_id)
        if not booking or user_id not in self._authorized_user_ids(booking):
            raise ForbiddenError("You are not authorized to end this session.")

        session = self.repo.get_by_booking(booking_id)
        if not session:
            raise NotFoundError("Video session not found.")

        session.status = VideoSessionStatus.COMPLETED
        session.ended_at = utcnow()
        if notes:
            session.session_notes = notes
        self.db.add(session)

        attendance = self.repo.get_attendance(session.id, user_id)
        if attendance:
            attendance.left_at = utcnow()
            self.db.add(attendance)

        self.repo.commit()
        return session

    def history(self, user_id: str):
        return self.repo.list_for_user(user_id)
