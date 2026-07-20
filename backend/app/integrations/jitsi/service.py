import hashlib
import uuid

from app.core.config import settings


def generate_room_name(booking_id: str) -> str:
    salt = uuid.uuid4().hex[:8]
    digest = hashlib.sha256(f"{booking_id}-{salt}".encode()).hexdigest()[:16]
    return f"guidebridge-{digest}"


def build_join_url(room_name: str, display_name: str) -> str:
    from urllib.parse import quote

    return f"https://{settings.JITSI_DOMAIN}/{room_name}#userInfo.displayName=%22{quote(display_name)}%22"
