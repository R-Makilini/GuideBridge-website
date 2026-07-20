from datetime import datetime, timezone
from app.core.datetime_utils import utcnow
from typing import Optional

from sqlalchemy.orm import Session

from app.modules.users.models import (
    EmailVerificationToken,
    PasswordResetToken,
    RefreshToken,
    User,
    UserSession,
)


class AuthRepository:
    def __init__(self, db: Session):
        self.db = db

    
    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email, User.deleted_at.is_(None)).first()

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()

    def create_user(self, user: User) -> User:
        self.db.add(user)
        self.db.flush()
        return user

    
    def create_session(self, session: UserSession) -> UserSession:
        self.db.add(session)
        self.db.flush()
        return session

    def get_session(self, session_id: str) -> Optional[UserSession]:
        return self.db.query(UserSession).filter(UserSession.id == session_id).first()

    def get_active_sessions(self, user_id: str) -> list[UserSession]:
        return (
            self.db.query(UserSession)
            .filter(UserSession.user_id == user_id, UserSession.is_active.is_(True))
            .all()
        )

    def revoke_session(self, session: UserSession) -> None:
        session.is_active = False
        session.revoked_at = utcnow()
        self.db.add(session)

    
    def create_refresh_token(self, token: RefreshToken) -> RefreshToken:
        self.db.add(token)
        self.db.flush()
        return token

    def get_refresh_tokens_for_session(self, session_id: str) -> list[RefreshToken]:
        return (
            self.db.query(RefreshToken)
            .filter(RefreshToken.session_id == session_id, RefreshToken.revoked_at.is_(None))
            .all()
        )

    def revoke_refresh_token(self, token: RefreshToken, replaced_by_id: Optional[str] = None) -> None:
        token.revoked_at = utcnow()
        if replaced_by_id:
            token.replaced_by_id = replaced_by_id
        self.db.add(token)
        
        
    def create_email_verification_token(self, token: EmailVerificationToken) -> EmailVerificationToken:
        self.db.add(token)
        self.db.flush()
        return token

    def get_valid_email_token_by_otp(self, user_id: str, otp_code: str) -> Optional[EmailVerificationToken]:
        return (
            self.db.query(EmailVerificationToken)
            .filter(
                EmailVerificationToken.user_id == user_id,
                EmailVerificationToken.otp_code == otp_code,
                EmailVerificationToken.used_at.is_(None),
                EmailVerificationToken.expires_at > utcnow(),
            )
            .order_by(EmailVerificationToken.created_at.desc())
            .first()
        )

    def get_latest_email_tokens(self, user_id: str) -> list[EmailVerificationToken]:
        return (
            self.db.query(EmailVerificationToken)
            .filter(
                EmailVerificationToken.user_id == user_id,
                EmailVerificationToken.used_at.is_(None),
                EmailVerificationToken.expires_at > utcnow(),
            )
            .all()
        )
