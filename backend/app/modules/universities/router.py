from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError
from app.core.permissions import require_super_admin
from app.database.session import get_db
from app.modules.universities.models import Degree, Department, ExpertiseTag, Faculty, Stream, Subject, University
from app.modules.universities.repository import TaxonomyRepository
from app.modules.universities.schemas import (
    DegreeCreate,
    DegreeOut,
    DepartmentCreate,
    DepartmentOut,
    ExpertiseTagOut,
    FacultyCreate,
    FacultyOut,
    NamedEntityCreate,
    StreamOut,
    SubjectCreate,
    SubjectOut,
    UniversityCreate,
    UniversityOut,
)
from app.modules.users.models import User

router = APIRouter(prefix="/universities", tags=["Universities & Taxonomy"])
admin_router = APIRouter(prefix="/admin/taxonomy", tags=["Admin - Taxonomy"])



@router.get("", response_model=list[UniversityOut])
def list_universities(db: Session = Depends(get_db)):
    return TaxonomyRepository(db).list_universities()


@router.get("/faculties", response_model=list[FacultyOut])
def list_faculties(university_id: str | None = Query(None), db: Session = Depends(get_db)):
    return TaxonomyRepository(db).list_faculties(university_id)


@router.get("/departments", response_model=list[DepartmentOut])
def list_departments(faculty_id: str | None = Query(None), db: Session = Depends(get_db)):
    return TaxonomyRepository(db).list_departments(faculty_id)


@router.get("/degrees", response_model=list[DegreeOut])
def list_degrees(department_id: str | None = Query(None), db: Session = Depends(get_db)):
    return TaxonomyRepository(db).list_degrees(department_id)


@router.get("/streams", response_model=list[StreamOut])
def list_streams(db: Session = Depends(get_db)):
    return TaxonomyRepository(db).list_streams()


@router.get("/subjects", response_model=list[SubjectOut])
def list_subjects(stream_id: str | None = Query(None), db: Session = Depends(get_db)):
    return TaxonomyRepository(db).list_subjects(stream_id)


@router.get("/expertise-tags", response_model=list[ExpertiseTagOut])
def list_expertise_tags(db: Session = Depends(get_db)):
    return TaxonomyRepository(db).list_expertise_tags()




@admin_router.post("/universities", response_model=UniversityOut, status_code=201)
def create_university(
    payload: UniversityCreate, current_user: User = Depends(require_super_admin), db: Session = Depends(get_db)
):
    if db.query(University).filter(University.name == payload.name).first():
        raise ConflictError("University with this name already exists.")
    entity = University(**payload.model_dump())
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return entity


@admin_router.post("/faculties", response_model=FacultyOut, status_code=201)
def create_faculty(
    payload: FacultyCreate, current_user: User = Depends(require_super_admin), db: Session = Depends(get_db)
):
    entity = Faculty(**payload.model_dump())
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return entity


@admin_router.post("/departments", response_model=DepartmentOut, status_code=201)
def create_department(
    payload: DepartmentCreate, current_user: User = Depends(require_super_admin), db: Session = Depends(get_db)
):
    entity = Department(**payload.model_dump())
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return entity


@admin_router.post("/degrees", response_model=DegreeOut, status_code=201)
def create_degree(
    payload: DegreeCreate, current_user: User = Depends(require_super_admin), db: Session = Depends(get_db)
):
    entity = Degree(**payload.model_dump())
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return entity


@admin_router.post("/streams", response_model=StreamOut, status_code=201)
def create_stream(
    payload: NamedEntityCreate, current_user: User = Depends(require_super_admin), db: Session = Depends(get_db)
):
    entity = Stream(name=payload.name)
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return entity


@admin_router.post("/subjects", response_model=SubjectOut, status_code=201)
def create_subject(
    payload: SubjectCreate, current_user: User = Depends(require_super_admin), db: Session = Depends(get_db)
):
    entity = Subject(**payload.model_dump())
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return entity


@admin_router.post("/expertise-tags", response_model=ExpertiseTagOut, status_code=201)
def create_expertise_tag(
    payload: NamedEntityCreate, current_user: User = Depends(require_super_admin), db: Session = Depends(get_db)
):
    entity = ExpertiseTag(name=payload.name)
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return entity
