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
    
    
    def _issue_email_verification(self, user: User) -> str:
        otp_code = generate_otp()
        raw_token = generate_url_safe_token()
        token_row = EmailVerificationToken(
            user_id=user.id,
            token_hash=hash_token(raw_token),
            otp_code=otp_code,
            expires_at=utcnow() + timedelta(minutes=EMAIL_TOKEN_TTL_MINUTES),
        )
        self.repo.create_email_verification_token(token_row)

        verify_link = f"{settings.FRONTEND_URL}/verify-email?token={raw_token}&email={user.email}"
        email_service.send(
            to_email=user.email,
            subject="Verify your GuideBridge account",
            html_body=verification_email_html(user.full_name, otp_code, verify_link),
        )
        return raw_token

    
    def verify_email(self, payload: VerifyEmailRequest) -> User:
        user: User | None = None

        if payload.otp_code and payload.email:
            user = self.repo.get_user_by_email(payload.email)
            if not user:
                raise NotFoundError("User not found.")
            token_row = self.repo.get_valid_email_token_by_otp(user.id, payload.otp_code)
            if not token_row:
                raise BadRequestError("Invalid or expired OTP code.")
        elif payload.token:
            # Token-based flow: search among unused, unexpired tokens for a hash match.
            candidates: list[EmailVerificationToken] = []
            if payload.email:
                user = self.repo.get_user_by_email(payload.email)
                if user:
                    candidates = self.repo.get_latest_email_tokens(user.id)
            token_row = None
            for candidate in candidates:
                if verify_token_hash(payload.token, candidate.token_hash):
                    token_row = candidate
                    break
            if not token_row:
                raise BadRequestError("Invalid or expired verification token.")
        else:
            raise BadRequestError("Either an OTP code or a token must be provided.")

        token_row.used_at = utcnow()
        user.is_email_verified = True
        user.status = UserStatus.ACTIVE
        self.db.add(token_row)
        self.db.add(user)
        self.repo.commit()
        logger.info("Email verified for user: %s", user.email)
        return user
