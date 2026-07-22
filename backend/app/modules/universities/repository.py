from sqlalchemy.orm import Session

from app.modules.universities.models import Degree, Department, ExpertiseTag, Faculty, Stream, Subject, University


class TaxonomyRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_universities(self):
        return self.db.query(University).filter(University.is_active.is_(True)).all()

    def list_faculties(self, university_id: str | None = None):
        q = self.db.query(Faculty)
        if university_id:
            q = q.filter(Faculty.university_id == university_id)
        return q.all()

    def list_departments(self, faculty_id: str | None = None):
        q = self.db.query(Department)
        if faculty_id:
            q = q.filter(Department.faculty_id == faculty_id)
        return q.all()

    def list_degrees(self, department_id: str | None = None):
        q = self.db.query(Degree)
        if department_id:
            q = q.filter(Degree.department_id == department_id)
        return q.all()

    def list_streams(self):
        return self.db.query(Stream).all()

    def list_subjects(self, stream_id: str | None = None):
        q = self.db.query(Subject)
        if stream_id:
            q = q.filter(Subject.stream_id == stream_id)
        return q.all()

    def list_expertise_tags(self):
        return self.db.query(ExpertiseTag).all()

    def commit(self):
        self.db.commit()
