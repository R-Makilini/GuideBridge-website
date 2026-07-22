from app.core.datetime_utils import utcnow
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.modules.chat.models import Conversation, ConversationMember, Message, MessageAttachment


class ChatRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_conversation(self, student_id: str, mentor_user_id: str) -> Conversation:
        convo = (
            self.db.query(Conversation)
            .filter(Conversation.student_id == student_id, Conversation.mentor_user_id == mentor_user_id)
            .first()
        )
        if convo:
            return convo

        convo = Conversation(student_id=student_id, mentor_user_id=mentor_user_id)
        self.db.add(convo)
        self.db.flush()
        self.db.add(ConversationMember(conversation_id=convo.id, user_id=student_id))
        self.db.add(ConversationMember(conversation_id=convo.id, user_id=mentor_user_id))
        self.db.flush()
        return convo

    def get_conversation(self, conversation_id: str) -> Conversation | None:
        return self.db.query(Conversation).filter(Conversation.id == conversation_id).first()

    def get_member(self, conversation_id: str, user_id: str) -> ConversationMember | None:
        return (
            self.db.query(ConversationMember)
            .filter(ConversationMember.conversation_id == conversation_id, ConversationMember.user_id == user_id)
            .first()
        )

    def list_conversations_for_user(self, user_id: str):
        return (
            self.db.query(Conversation)
            .filter(or_(Conversation.student_id == user_id, Conversation.mentor_user_id == user_id))
            .order_by(Conversation.last_message_at.desc().nullslast())
            .all()
        )

    def unread_count(self, conversation_id: str, user_id: str) -> int:
        member = self.get_member(conversation_id, user_id)
        query = self.db.query(func.count(Message.id)).filter(
            Message.conversation_id == conversation_id, Message.sender_id != user_id
        )
        if member and member.last_read_at:
            query = query.filter(Message.created_at > member.last_read_at)
        return query.scalar() or 0

    def count_student_messages_in_conversation(self, conversation_id: str, student_id: str) -> int:
        return (
            self.db.query(func.count(Message.id))
            .filter(Message.conversation_id == conversation_id, Message.sender_id == student_id)
            .scalar()
            or 0
        )

    def create_message(self, message: Message) -> Message:
        self.db.add(message)
        self.db.flush()
        return message

    def list_messages(self, conversation_id: str, page: int, page_size: int):
        query = self.db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at.desc())
        total = query.order_by(None).with_entities(func.count()).scalar() or 0
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return list(reversed(items)), total

    def search_messages(self, conversation_id: str, term: str):
        return (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id, Message.content.ilike(f"%{term}%"))
            .order_by(Message.created_at.desc())
            .all()
        )

    def mark_seen(self, conversation_id: str, user_id: str) -> None:
        from datetime import datetime, timezone

        member = self.get_member(conversation_id, user_id)
        if member:
            member.last_read_at = utcnow()
            self.db.add(member)
        self.db.query(Message).filter(
            Message.conversation_id == conversation_id, Message.sender_id != user_id, Message.is_seen.is_(False)
        ).update({"is_seen": True, "seen_at": utcnow()})

    def commit(self):
        self.db.commit()
