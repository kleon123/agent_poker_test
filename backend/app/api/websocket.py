from typing import Optional

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal, get_db
from app.models.player import Agent
from app.services.connection_manager import connection_manager
from app.services.game_service import GameService

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/observer/{table_id}")
async def observer_websocket(websocket: WebSocket, table_id: str):
    import uuid
    client_id = str(uuid.uuid4())
    await connection_manager.connect(websocket, client_id, table_id)
    try:
        # Send current game state on connect
        async with AsyncSessionLocal() as db:
            svc = GameService(db)
            try:
                state = await svc.get_table_state(table_id)
                await websocket.send_json({"type": "game_state", "data": state})
            except Exception:
                await websocket.send_json({"type": "error", "data": {"message": "Table not found"}})

        # Keep connection alive, listen for pings
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket, table_id)


@router.websocket("/ws/player/{table_id}")
async def player_websocket(
    websocket: WebSocket,
    table_id: str,
    api_key: Optional[str] = Query(None),
):
    if not api_key:
        await websocket.accept()
        await websocket.send_json({"type": "error", "data": {"message": "api_key query param required"}})
        await websocket.close()
        return

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Agent).where(Agent.api_key == api_key))
        agent = result.scalar_one_or_none()

    if not agent:
        await websocket.accept()
        await websocket.send_json({"type": "error", "data": {"message": "Invalid API key"}})
        await websocket.close()
        return

    player_id = agent.id
    await connection_manager.connect_player(websocket, player_id, table_id)

    try:
        # Send initial state
        async with AsyncSessionLocal() as db:
            svc = GameService(db)
            try:
                state = await svc.get_table_state(table_id)
                await websocket.send_json({"type": "game_state", "data": state})
            except Exception:
                await websocket.send_json({"type": "error", "data": {"message": "Table not found"}})

        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connection_manager.disconnect_player(websocket, player_id, table_id)
