from sqlalchemy.orm import Session

from app.modules.students.models import StudentProfile


class StudentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user_id(self, user_id: str) -> StudentProfile | None:
        return self.db.query(StudentProfile).filter(StudentProfile.user_id == user_id).first()

    def commit(self):
        self.db.commit()
