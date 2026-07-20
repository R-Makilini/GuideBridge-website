from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.core.constants import UserRole
from app.core.security import validate_password_strength


class RegisterStudentRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    password: str
    confirm_password: str
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

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self


class RegisterMentorRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    password: str
    confirm_password: str
    phone: Optional[str] = None
    university_id: Optional[str] = None

    @field_validator("password")
    @classmethod
    def check_password(cls, v: str) -> str:
        error = validate_password_strength(v)
        if error:
            raise ValueError(error)
        return v

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self


   
   
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    device_info: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class VerifyEmailRequest(BaseModel):
    token: Optional[str] = None
    otp_code: Optional[str] = None
    email: Optional[EmailStr] = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
    confirm_password: str

    @field_validator("new_password")
    @classmethod
    def check_password(cls, v: str) -> str:
        error = validate_password_strength(v)
        if error:
            raise ValueError(error)
        return v

    @model_validator(mode="after")
    def passwords_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str

    @field_validator("new_password")
    @classmethod
    def check_password(cls, v: str) -> str:
        error = validate_password_strength(v)
        if error:
            raise ValueError(error)
        return v

    @model_validator(mode="after")
    def passwords_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self


class UserOut(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: UserRole
    status: str
    is_email_verified: bool
    profile_picture_url: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SessionOut(BaseModel):
    id: str
    device_info: Optional[str] = None
    ip_address: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
