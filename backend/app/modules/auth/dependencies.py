from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.constants import UserStatus
from app.core.exceptions import UnauthorizedError
from app.core.security import TokenError, decode_token
from app.database.session import get_db
from app.modules.users.models import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise UnauthorizedError("Authentication credentials were not provided.")

    try:
        payload = decode_token(credentials.credentials)
    except TokenError as exc:
        raise UnauthorizedError("Invalid or expired access token.") from exc

    if payload.get("type") != "access":
        raise UnauthorizedError("Invalid token type.")

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
    if not user:
        raise UnauthorizedError("User not found.")

    if user.status == UserStatus.SUSPENDED:
        raise UnauthorizedError("Your account has been suspended.")
    if user.status == UserStatus.BANNED:
        raise UnauthorizedError("Your account has been banned.")

    return user


def get_current_access_token_payload(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    if credentials is None:
        raise UnauthorizedError("Authentication credentials were not provided.")
    try:
        payload = decode_token(credentials.credentials)
    except TokenError as exc:
        raise UnauthorizedError("Invalid or expired access token.") from exc
    return payload


def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    if credentials is None:
        return None
    try:
        return get_current_user(credentials, db)
    except UnauthorizedError:
        return None
