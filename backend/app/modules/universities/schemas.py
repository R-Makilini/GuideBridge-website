from typing import Optional

from pydantic import BaseModel


class NamedEntityCreate(BaseModel):
    name: str


class UniversityCreate(NamedEntityCreate):
    short_name: Optional[str] = None
    city: Optional[str] = None


class UniversityOut(BaseModel):
    id: str
    name: str
    short_name: Optional[str] = None
    city: Optional[str] = None
    is_active: bool

    model_config = {"from_attributes": True}


class FacultyCreate(NamedEntityCreate):
    university_id: str


class FacultyOut(BaseModel):
    id: str
    university_id: str
    name: str

    model_config = {"from_attributes": True}


class DepartmentCreate(NamedEntityCreate):
    faculty_id: str


class DepartmentOut(BaseModel):
    id: str
    faculty_id: str
    name: str

    model_config = {"from_attributes": True}


class DegreeCreate(NamedEntityCreate):
    department_id: str


class DegreeOut(BaseModel):
    id: str
    department_id: str
    name: str

    model_config = {"from_attributes": True}


class StreamOut(BaseModel):
    id: str
    name: str

    model_config = {"from_attributes": True}


class SubjectCreate(NamedEntityCreate):
    stream_id: Optional[str] = None


class SubjectOut(BaseModel):
    id: str
    name: str
    stream_id: Optional[str] = None

    model_config = {"from_attributes": True}


class ExpertiseTagOut(BaseModel):
    id: str
    name: str

    model_config = {"from_attributes": True}
