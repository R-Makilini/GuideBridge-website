from fastapi import APIRouter, Depends, File, Query, UploadFile, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.file_validation import safe_file_key, validate_upload
from app.core.permissions import require_any_authenticated, require_student
from app.database.session import SessionLocal, get_db
from app.integrations.storage import get_storage_backend
from app.modules.chat.models import MessageAttachment
from app.modules.chat.schemas import ConversationCreate, ConversationOut, MessageOut, SendMessageRequest
from app.modules.chat.service import ChatService
from app.modules.users.models import User
from app.websocket.dependencies import authenticate_websocket
from app.websocket.manager import manager

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/conversations", response_model=ConversationOut, status_code=201)
def start_conversation(payload: ConversationCreate, current_user: User = Depends(require_student), db: Session = Depends(get_db)):
    convo = ChatService(db).start_conversation(current_user.id, payload.mentor_user_id)
    return ConversationOut(id=convo.id, student_id=convo.student_id, mentor_user_id=convo.mentor_user_id, last_message_at=convo.last_message_at)


@router.get("/conversations", response_model=list[ConversationOut])
def list_conversations(current_user: User = Depends(require_any_authenticated), db: Session = Depends(get_db)):
    rows = ChatService(db).list_conversations(current_user.id)
    return [
        ConversationOut(
            id=r["conversation"].id,
            student_id=r["conversation"].student_id,
            mentor_user_id=r["conversation"].mentor_user_id,
            last_message_at=r["conversation"].last_message_at,
            unread_count=r["unread_count"],
        )
        for r in rows
    ]


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageOut])
def list_messages(
    conversation_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    current_user: User = Depends(require_any_authenticated),
    db: Session = Depends(get_db),
):
    items, _ = ChatService(db).list_messages(conversation_id, current_user.id, page, page_size)
    return items


@router.post("/conversations/{conversation_id}/messages", response_model=MessageOut, status_code=201)
def send_message(
    conversation_id: str, payload: SendMessageRequest, current_user: User = Depends(require_any_authenticated), db: Session = Depends(get_db)
):
    message = ChatService(db).send_message(conversation_id, current_user.id, payload.content, current_user.role)
    return message


@router.post("/conversations/{conversation_id}/attachments")
def upload_attachment(
    conversation_id: str, file: UploadFile = File(...), current_user: User = Depends(require_any_authenticated), db: Session = Depends(get_db)
):
    validate_upload(file)
    ChatService(db)._assert_member(conversation_id, current_user.id)

    key, safe_name = safe_file_key(file.filename, folder=f"chat/{conversation_id}")
    url = get_storage_backend().upload(file.file, key, file.content_type)

    message = ChatService(db).send_message(conversation_id, current_user.id, None, current_user.role)
    attachment = MessageAttachment(
        message_id=message.id, file_url=url, file_name=safe_name, mime_type=file.content_type, file_size_bytes=0
    )
    db.add(attachment)
    db.commit()
    return {"message_id": message.id, "file_url": url}


@router.get("/conversations/{conversation_id}/search", response_model=list[MessageOut])
def search_messages(conversation_id: str, q: str = Query(..., min_length=1), current_user: User = Depends(require_any_authenticated), db: Session = Depends(get_db)):
    return ChatService(db).search_messages(conversation_id, current_user.id, q)


@router.post("/conversations/{conversation_id}/seen", status_code=204)
def mark_seen(conversation_id: str, current_user: User = Depends(require_any_authenticated), db: Session = Depends(get_db)):
    ChatService(db).mark_seen(conversation_id, current_user.id)


ws_router = APIRouter()


@ws_router.websocket("/ws/chat/{conversation_id}")
async def chat_websocket(websocket: WebSocket, conversation_id: str):
    user = await authenticate_websocket(websocket)
    if user is None:
        return

    db = SessionLocal()
    try:
        service = ChatService(db)
        service._assert_member(conversation_id, user.id)
    except Exception:
        await websocket.close(code=4403)
        db.close()
        return

    await manager.connect(conversation_id, user.id, websocket)
    await manager.broadcast(conversation_id, {"event": "presence", "user_id": user.id, "status": "online"})

    try:
        while True:
            raw = await websocket.receive_json()
            event = raw.get("event")

            if event == "message":
                message = service.send_message(conversation_id, user.id, raw.get("content"), user.role)
                await manager.broadcast(
                    conversation_id,
                    {
                        "event": "message",
                        "id": message.id,
                        "sender_id": user.id,
                        "content": message.content,
                        "created_at": message.created_at,
                    },
                )
            elif event == "typing":
                await manager.broadcast(conversation_id, {"event": "typing", "user_id": user.id})
            elif event == "seen":
                service.mark_seen(conversation_id, user.id)
                await manager.broadcast(conversation_id, {"event": "seen", "user_id": user.id})
    except WebSocketDisconnect:
        manager.disconnect(conversation_id, websocket)
        await manager.broadcast(conversation_id, {"event": "presence", "user_id": user.id, "status": "offline"})
    finally:
        db.close()
