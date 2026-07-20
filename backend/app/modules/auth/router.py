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



@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    service = AuthService(db)
    _, tokens = service.login(payload, ip_address=_client_ip(request))
    return tokens


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    return service.refresh_access_token(payload.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout_current_device(
    token_payload: dict = Depends(get_current_access_token_payload),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    
    service = AuthService(db)
    service.logout_all_devices(current_user.id)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
def logout_all_devices(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    service = AuthService(db)
    service.logout_all_devices(current_user.id)


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AuthService(db)
    service.change_password(current_user, payload.current_password, payload.new_password)


@router.post("/forgot-password", status_code=status.HTTP_204_NO_CONTENT)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    service.forgot_password(payload)


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(payload: ResetPasswordRequest, email: str, db: Session = Depends(get_db)):
    service = AuthService(db)
    service.reset_password(payload, email)


@router.get("/sessions", response_model=list[SessionOut])
def list_sessions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from app.modules.auth.repository import AuthRepository

    repo = AuthRepository(db)
    return repo.get_active_sessions(current_user.id)
