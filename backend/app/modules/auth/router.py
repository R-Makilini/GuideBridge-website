from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.auth.dependencies import get_current_access_token_payload, get_current_user
from app.modules.auth.schemas import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterMentorRequest,
    RegisterStudentRequest,
    ResetPasswordRequest,
    SessionOut,
    TokenResponse,
    UserOut,
    VerifyEmailRequest,
)
from app.modules.auth.service import AuthService
from app.modules.users.models import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.post("/register/student", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_student(payload: RegisterStudentRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    user = service.register_student(payload)
    return user


@router.post("/register/mentor", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_mentor(payload: RegisterMentorRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    user = service.register_mentor(payload)
    return user


@router.post("/verify-email", response_model=UserOut)
def verify_email(payload: VerifyEmailRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    return service.verify_email(payload)