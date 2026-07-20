from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.constants import UserRole
from app.core.security import validate_password_strength


class RegisterStudentRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    password: str
    phone: Optional[str] = None
    school: Optional[str] = None
    grade: Optional[str] = None
    district: Optional[str] = None

    @field_validator("password")
    @classmethod
    def check_password(cls, v: str) -> str:
        error = validate_password_strength(v)
        if error:
            raise ValueError(error)
        return v
    
    
class RegisterMentorRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    password: str
    phone: Optional[str] = None
    university_id: Optional[str] = None

    @field_validator("password")
    @classmethod
    def check_password(cls, v: str) -> str:
        error = validate_password_strength(v)
        if error:
            raise ValueError(error)
        return v
   
   
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    device_info: Optional[str] = None

