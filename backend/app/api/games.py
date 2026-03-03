from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.game import Game
from app.models.player import Agent
from app.schemas.game import GameActionRequest, GameResponse, StatsResponse, ValidActionsResponse
from app.services.game_service import GameService

router = APIRouter(tags=["games"])


async def _get_agent_by_key(api_key: str, db: AsyncSession) -> Agent:
    result = await db.execute(select(Agent).where(Agent.api_key == api_key))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return agent


@router.get("/games/history")
async def game_history(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Game).where(Game.status == "finished").order_by(Game.finished_at.desc()).limit(50)
    )
    games = result.scalars().all()
    return [
        {
            "id": g.id,
            "table_id": g.table_id,
            "hand_number": g.hand_number,
            "phase": g.phase,
            "status": g.status,
            "pot": g.pot,
            "started_at": g.started_at.isoformat() if g.started_at else None,
            "finished_at": g.finished_at.isoformat() if g.finished_at else None,
            "winner_info": g.winner_info,
        }
        for g in games
    ]


@router.get("/stats", response_model=StatsResponse)
async def get_stats(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import func
    from app.models.game import Table
    from app.services.game_service import active_games

    agents_count = (await db.execute(select(func.count()).select_from(Agent))).scalar_one()
    tables_count = (await db.execute(select(func.count()).select_from(Table))).scalar_one()
    games_count = (await db.execute(select(func.count()).select_from(Game))).scalar_one()

    return {
        "total_agents": agents_count,
        "total_tables": tables_count,
        "total_games": games_count,
        "active_games": len(active_games),
    }


@router.get("/games/{game_id}")
async def get_game(
    game_id: str,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
):
    svc = GameService(db)
    player_id = None
    if x_api_key:
        result = await db.execute(select(Agent).where(Agent.api_key == x_api_key))
        agent = result.scalar_one_or_none()
        if agent:
            player_id = agent.id
    try:
        return await svc.get_game_state(game_id, player_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/games/{game_id}/action")
async def submit_action(
    game_id: str,
    body: GameActionRequest,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="X-API-Key header required")
    agent = await _get_agent_by_key(x_api_key, db)
    svc = GameService(db)
    try:
        state = await svc.process_action(game_id, agent.id, body.action, body.amount)
        return state
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/games/{game_id}/valid-actions", response_model=ValidActionsResponse)
async def get_valid_actions(
    game_id: str,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="X-API-Key header required")
    agent = await _get_agent_by_key(x_api_key, db)
    svc = GameService(db)
    try:
        actions = await svc.get_valid_actions(game_id, agent.id)
        return {"player_id": agent.id, "actions": actions}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
