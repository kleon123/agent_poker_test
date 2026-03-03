from typing import Optional

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.game import Game
from app.models.player import Agent
from app.services.connection_manager import connection_manager
from app.services.game_service import GameService, active_games

router = APIRouter(tags=["websocket"])


async def _send_initial_state(websocket: WebSocket, svc: GameService, table_id: str) -> None:
    """Send the most relevant initial state to a newly connected WebSocket client."""
    try:
        table_state = await svc.get_table_state(table_id)
        # If a game is actively running for this table, send its game state instead
        if table_state.get("status") == "playing":
            # Find the active game in memory
            for game_id, game in active_games.items():
                if game.table_id == table_id:
                    await websocket.send_json(
                        {"type": "game_state", "data": game.get_state_for_observer()}
                    )
                    return
            # Fall back to DB lookup for recently finished games
            result = await svc.db.execute(
                select(Game)
                .where(Game.table_id == table_id, Game.status == "active")
                .order_by(Game.started_at.desc())
                .limit(1)
            )
            db_game = result.scalar_one_or_none()
            if db_game:
                await websocket.send_json(
                    {"type": "game_state", "data": {"game_id": db_game.id, "phase": db_game.phase}}
                )
                return
        # Waiting/finished table: send table info
        await websocket.send_json({"type": "table_state", "data": table_state})
    except Exception:
        await websocket.send_json({"type": "error", "data": {"message": "Table not found"}})


@router.websocket("/ws/observer/{table_id}")
async def observer_websocket(websocket: WebSocket, table_id: str):
    await connection_manager.connect(websocket, table_id)
    try:
        async with AsyncSessionLocal() as db:
            svc = GameService(db)
            await _send_initial_state(websocket, svc, table_id)

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
        async with AsyncSessionLocal() as db:
            svc = GameService(db)
            await _send_initial_state(websocket, svc, table_id)

        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connection_manager.disconnect_player(websocket, player_id, table_id)
