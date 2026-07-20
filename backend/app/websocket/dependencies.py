from fastapi import WebSocket
from sqlalchemy.orm import Session

from app.core.security import TokenError, decode_token
from app.database.session import SessionLocal
from app.modules.users.models import User


async def authenticate_websocket(websocket: WebSocket) -> User | None:
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4401)
        return None
    try:
        payload = decode_token(token)
    except TokenError:
        await websocket.close(code=4401)
        return None
    if payload.get("type") != "access":
        await websocket.close(code=4401)
        return None

    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.id == payload.get("sub"), User.deleted_at.is_(None)).first()
        if not user:
            await websocket.close(code=4401)
            return None
        return user
    finally:
        db.close()
