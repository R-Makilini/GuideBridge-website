import json

from fastapi import WebSocket


class ConnectionManager:
    """Tracks active WebSocket connections per conversation for real-time chat."""

    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}
        self.user_conversations: dict[str, set[str]] = {}

    async def connect(self, conversation_id: str, user_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.setdefault(conversation_id, []).append(websocket)
        self.user_conversations.setdefault(user_id, set()).add(conversation_id)

    def disconnect(self, conversation_id: str, websocket: WebSocket) -> None:
        connections = self.active_connections.get(conversation_id, [])
        if websocket in connections:
            connections.remove(websocket)
        if not connections and conversation_id in self.active_connections:
            del self.active_connections[conversation_id]

    async def broadcast(self, conversation_id: str, message: dict) -> None:
        for connection in self.active_connections.get(conversation_id, []):
            try:
                await connection.send_text(json.dumps(message, default=str))
            except Exception:  # noqa: BLE001
                pass


manager = ConnectionManager()
