import asyncio
import json
from typing import Dict, List, Optional, Set
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # table_id -> set of WebSocket connections
        self._connections: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, table_id: str, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            if table_id not in self._connections:
                self._connections[table_id] = set()
            self._connections[table_id].add(websocket)

    async def disconnect(self, table_id: str, websocket: WebSocket):
        async with self._lock:
            if table_id in self._connections:
                self._connections[table_id].discard(websocket)
                if not self._connections[table_id]:
                    del self._connections[table_id]

    async def broadcast(self, table_id: str, data: dict):
        if table_id not in self._connections:
            return
        message = json.dumps(data)
        dead: List[WebSocket] = []
        for ws in list(self._connections.get(table_id, [])):
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.disconnect(table_id, ws)

    async def send_personal(self, websocket: WebSocket, data: dict):
        try:
            await websocket.send_text(json.dumps(data))
        except Exception:
            pass

    def connection_count(self, table_id: str) -> int:
        return len(self._connections.get(table_id, set()))


manager = ConnectionManager()
