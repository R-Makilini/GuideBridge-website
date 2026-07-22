from sqlalchemy.orm import Session

from app.modules.video_sessions.models import SessionAttendance, VideoSession


class VideoSessionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_booking(self, booking_id: str) -> VideoSession | None:
        return self.db.query(VideoSession).filter(VideoSession.booking_id == booking_id).first()

    def get(self, session_id: str) -> VideoSession | None:
        return self.db.query(VideoSession).filter(VideoSession.id == session_id).first()

    def create(self, session: VideoSession) -> VideoSession:
        self.db.add(session)
        self.db.flush()
        return session

    def get_attendance(self, session_id: str, user_id: str) -> SessionAttendance | None:
        return (
            self.db.query(SessionAttendance)
            .filter(SessionAttendance.video_session_id == session_id, SessionAttendance.user_id == user_id)
            .first()
        )

    def add_attendance(self, attendance: SessionAttendance) -> None:
        self.db.add(attendance)

    def list_for_user(self, user_id: str):
        return (
            self.db.query(VideoSession)
            .join(SessionAttendance)
            .filter(SessionAttendance.user_id == user_id)
            .order_by(VideoSession.created_at.desc())
            .all()
        )

    def commit(self):
        self.db.commit()
