from datetime import datetime, timezone
from app.core.datetime_utils import utcnow

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.constants import NotificationType, UserRole
from app.core.exceptions import ForbiddenError, NotFoundError, PaymentRequiredError
from app.modules.admin.models import SystemSetting
from app.modules.chat.models import Conversation, Message
from app.modules.chat.repository import ChatRepository
from app.modules.notifications.service import NotificationService


class ChatService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ChatRepository(db)
        self.notifications = NotificationService(db)

    def _free_chat_limit(self) -> int:
        setting = self.db.query(SystemSetting).filter(SystemSetting.key == "free_chat_limit").first()
        if setting:
            try:
                return int(setting.value)
            except ValueError:
                pass
        return settings.DEFAULT_FREE_CHAT_LIMIT

    def start_conversation(self, student_id: str, mentor_user_id: str) -> Conversation:
        return self.repo.get_or_create_conversation(student_id, mentor_user_id)

    def list_conversations(self, user_id: str):
        conversations = self.repo.list_conversations_for_user(user_id)
        result = []
        for c in conversations:
            unread = self.repo.unread_count(c.id, user_id)
            result.append({"conversation": c, "unread_count": unread})
        return result

    def _assert_member(self, conversation_id: str, user_id: str) -> Conversation:
        conversation = self.repo.get_conversation(conversation_id)
        if not conversation:
            raise NotFoundError("Conversation not found.")
        if user_id not in (conversation.student_id, conversation.mentor_user_id):
            raise ForbiddenError("You are not a member of this conversation.")
        return conversation

    def send_message(self, conversation_id: str, sender_id: str, content: str | None, role: UserRole) -> Message:
        conversation = self._assert_member(conversation_id, sender_id)

        if role == UserRole.STUDENT:
            sent_count = self.repo.count_student_messages_in_conversation(conversation_id, sender_id)
            limit = self._free_chat_limit()
            if sent_count >= limit:
                raise PaymentRequiredError(
                    "You have reached the free chat limit for this conversation. Please upgrade or book a paid session to continue messaging."
                )

        message = Message(conversation_id=conversation_id, sender_id=sender_id, content=content)
        self.repo.create_message(message)

        conversation.last_message_at = utcnow()
        self.db.add(conversation)

        recipient_id = conversation.mentor_user_id if sender_id == conversation.student_id else conversation.student_id
        self.notifications.notify(
            recipient_id, NotificationType.NEW_MESSAGE, "New Message", "You have a new chat message.", auto_commit=False
        )

        self.repo.commit()
        return message

    def list_messages(self, conversation_id: str, user_id: str, page: int, page_size: int):
        self._assert_member(conversation_id, user_id)
        return self.repo.list_messages(conversation_id, page, page_size)

    def search_messages(self, conversation_id: str, user_id: str, term: str):
        self._assert_member(conversation_id, user_id)
        return self.repo.search_messages(conversation_id, term)

    def mark_seen(self, conversation_id: str, user_id: str) -> None:
        self._assert_member(conversation_id, user_id)
        self.repo.mark_seen(conversation_id, user_id)
        self.repo.commit()
