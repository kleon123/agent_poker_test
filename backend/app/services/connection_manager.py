from typing import Dict, Optional, Set
from fastapi import WebSocket
import asyncio
import json


class ConnectionManager:
    def __init__(self):
        # table_id -> set of (websocket, client_id)
        self._table_observers: Dict[str, Set[WebSocket]] = {}
        # player_id -> websocket
        self._player_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, table_id: str) -> None:
        await websocket.accept()
        if table_id not in self._table_observers:
            self._table_observers[table_id] = set()
        self._table_observers[table_id].add(websocket)

    async def connect_player(self, websocket: WebSocket, player_id: str, table_id: str) -> None:
        await websocket.accept()
        self._player_connections[player_id] = websocket
        if table_id not in self._table_observers:
            self._table_observers[table_id] = set()
        self._table_observers[table_id].add(websocket)

    def disconnect(self, websocket: WebSocket, table_id: str) -> None:
        if table_id in self._table_observers:
            self._table_observers[table_id].discard(websocket)

    def disconnect_player(self, websocket: WebSocket, player_id: str, table_id: str) -> None:
        self._player_connections.pop(player_id, None)
        if table_id in self._table_observers:
            self._table_observers[table_id].discard(websocket)

    async def broadcast_to_table(self, table_id: str, message: dict) -> None:
        if table_id not in self._table_observers:
            return
        dead: list[WebSocket] = []
        payload = json.dumps(message)
        for ws in list(self._table_observers[table_id]):
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._table_observers[table_id].discard(ws)

    async def send_to_player(self, player_id: str, message: dict) -> None:
        ws = self._player_connections.get(player_id)
        if ws is None:
            return
        try:
            await ws.send_text(json.dumps(message))
        except Exception:
            self._player_connections.pop(player_id, None)


connection_manager = ConnectionManager()
