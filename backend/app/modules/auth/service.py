from datetime import datetime, timedelta, timezone
from app.core.datetime_utils import utcnow

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.constants import AuthProvider, UserRole, UserStatus
from app.core.exceptions import BadRequestError, ConflictError, NotFoundError, UnauthorizedError
from app.core.logging import get_logger
from app.core.security import (
    TokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_otp,
    generate_url_safe_token,
    hash_password,
    hash_token,
    verify_password,
    verify_token_hash,
)
from app.integrations.email.service import email_service
from app.integrations.email.templates import password_reset_email_html, verification_email_html
from app.modules.auth.repository import AuthRepository
from app.modules.auth.schemas import (
    ForgotPasswordRequest,
    LoginRequest,
    RegisterMentorRequest,
    RegisterStudentRequest,
    ResetPasswordRequest,
    TokenResponse,
    VerifyEmailRequest,
)
from app.modules.mentors.models import MentorProfile
from app.modules.students.models import StudentProfile
from app.modules.users.models import EmailVerificationToken, PasswordResetToken, RefreshToken, User, UserSession

logger = get_logger("auth_service")

EMAIL_TOKEN_TTL_MINUTES = 30
PASSWORD_RESET_TTL_MINUTES = 60


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AuthRepository(db)


    def register_student(self, payload: RegisterStudentRequest) -> User:
        if self.repo.get_user_by_email(payload.email):
            raise ConflictError("An account with this email already exists.")

        user = User(
            email=payload.email,
            phone=payload.phone,
            full_name=payload.full_name,
            hashed_password=hash_password(payload.password),
            role=UserRole.STUDENT,
            status=UserStatus.PENDING,
            auth_provider=AuthProvider.LOCAL,
        )
        self.repo.create_user(user)

        profile = StudentProfile(
            user_id=user.id,
            school=payload.school,
            grade=payload.grade,
            district=payload.district,
        )
        self.db.add(profile)

        self._issue_email_verification(user)
        self.repo.commit()
        logger.info("Student registered: %s", user.email)
        return user
    
    
    def register_mentor(self, payload: RegisterMentorRequest) -> User:
        if self.repo.get_user_by_email(payload.email):
            raise ConflictError("An account with this email already exists.")

        user = User(
            email=payload.email,
            phone=payload.phone,
            full_name=payload.full_name,
            hashed_password=hash_password(payload.password),
            role=UserRole.MENTOR,
            status=UserStatus.PENDING,
            auth_provider=AuthProvider.LOCAL,
        )
        self.repo.create_user(user)

        profile = MentorProfile(user_id=user.id, university_id=payload.university_id)
        self.db.add(profile)

        self._issue_email_verification(user)
        self.repo.commit()
        logger.info("Mentor registered: %s", user.email)
        return user