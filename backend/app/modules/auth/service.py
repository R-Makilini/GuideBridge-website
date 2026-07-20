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


    def login(self, payload: LoginRequest, ip_address: str | None = None) -> tuple[User, TokenResponse]:
        user = self.repo.get_user_by_email(payload.email)
        if not user or not user.hashed_password or not verify_password(payload.password, user.hashed_password):
            raise UnauthorizedError("Invalid email or password.")

        if user.status == UserStatus.SUSPENDED:
            raise UnauthorizedError("Your account has been suspended. Contact support.")
        if user.status == UserStatus.BANNED:
            raise UnauthorizedError("Your account has been banned.")

        tokens = self._issue_tokens(user, payload.device_info, ip_address)
        user.last_login_at = utcnow()
        self.db.add(user)
        self.repo.commit()
        return user, tokens


    def _issue_tokens(self, user: User, device_info: str | None, ip_address: str | None) -> TokenResponse:
        session = UserSession(user_id=user.id, device_info=device_info, ip_address=ip_address)
        self.repo.create_session(session)

        access_token = create_access_token(subject=user.id, role=user.role.value)
        raw_refresh, expires_at = create_refresh_token(subject=user.id, session_id=session.id)

        refresh_row = RefreshToken(
            session_id=session.id,
            user_id=user.id,
            token_hash=hash_token(raw_refresh),
            expires_at=expires_at,
        )
        self.repo.create_refresh_token(refresh_row)

        return TokenResponse(access_token=access_token, refresh_token=raw_refresh)


    def refresh_access_token(self, raw_refresh_token: str) -> TokenResponse:
        try:
            payload = decode_token(raw_refresh_token)
        except TokenError as exc:
            raise UnauthorizedError("Invalid or expired refresh token.") from exc

        if payload.get("type") != "refresh":
            raise UnauthorizedError("Invalid token type.")

        session_id = payload.get("sid")
        user_id = payload.get("sub")
        session = self.repo.get_session(session_id) if session_id else None
        if not session or not session.is_active:
            raise UnauthorizedError("Session is no longer active.")

        candidates = self.repo.get_refresh_tokens_for_session(session_id)
        matched: RefreshToken | None = None
        for candidate in candidates:
            if verify_token_hash(raw_refresh_token, candidate.token_hash):
                matched = candidate
                break

        if not matched or matched.expires_at < utcnow():
            
        
            self.repo.revoke_session(session)
            self.repo.commit()
            raise UnauthorizedError("Refresh token is invalid, expired, or already used.")

        user = self.repo.get_user_by_id(user_id)
        if not user:
            raise UnauthorizedError("User not found.")

        
    
        access_token = create_access_token(subject=user.id, role=user.role.value)
        new_raw_refresh, expires_at = create_refresh_token(subject=user.id, session_id=session.id)
        new_token_row = RefreshToken(
            session_id=session.id,
            user_id=user.id,
            token_hash=hash_token(new_raw_refresh),
            expires_at=expires_at,
        )
        self.repo.create_refresh_token(new_token_row)
        self.repo.revoke_refresh_token(matched, replaced_by_id=new_token_row.id)
        self.repo.commit()

        return TokenResponse(access_token=access_token, refresh_token=new_raw_refresh)

    def logout_current_device(self, user_id: str, session_id: str) -> None:
        session = self.repo.get_session(session_id)
        if session and session.user_id == user_id:
            self.repo.revoke_session(session)
            self.repo.commit()

    def logout_all_devices(self, user_id: str) -> None:
        for session in self.repo.get_active_sessions(user_id):
            self.repo.revoke_session(session)
        self.repo.commit()

    def forgot_password(self, payload: ForgotPasswordRequest) -> None:
        user = self.repo.get_user_by_email(payload.email)
        if not user:
            
            logger.info("Password reset requested for unknown email: %s", payload.email)
            return

        raw_token = generate_url_safe_token()
        token_row = PasswordResetToken(
            user_id=user.id,
            token_hash=hash_token(raw_token),
            expires_at=utcnow() + timedelta(minutes=PASSWORD_RESET_TTL_MINUTES),
        )
        self.repo.create_password_reset_token(token_row)
        self.repo.commit()

        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={raw_token}&email={user.email}"
        email_service.send(
            to_email=user.email,
            subject="Reset your GuideBridge password",
            html_body=password_reset_email_html(user.full_name, reset_link),
        )

    def reset_password(self, payload: ResetPasswordRequest, email: str) -> None:
        user = self.repo.get_user_by_email(email)
        if not user:
            raise NotFoundError("User not found.")

        candidates = self.repo.get_active_password_reset_tokens(user.id)
        matched: PasswordResetToken | None = None
        for candidate in candidates:
            if verify_token_hash(payload.token, candidate.token_hash):
                matched = candidate
                break

        if not matched:
            raise BadRequestError("Invalid or expired reset token.")

        user.hashed_password = hash_password(payload.new_password)
        matched.used_at = utcnow()
        self.db.add(user)
        self.db.add(matched)

        
        for session in self.repo.get_active_sessions(user.id):
            self.repo.revoke_session(session)

        self.repo.commit()
        logger.info("Password reset for user: %s", user.email)

    def change_password(self, user: User, current_password: str, new_password: str) -> None:
        if not user.hashed_password or not verify_password(current_password, user.hashed_password):
            raise UnauthorizedError("Current password is incorrect.")
        user.hashed_password = hash_password(new_password)
        self.db.add(user)
        self.repo.commit()
        return TokenResponse(access_token=access_token, refresh_token=new_raw_refresh)
