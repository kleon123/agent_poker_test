from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from backend.models.database import get_db
from backend.models.models import Agent, Table as TableModel, Game, GamePlayer, GameAction as GameActionModel, GameLog as GameLogModel
from backend.schemas.schemas import (
    AgentRegister, AgentRegisterResponse, AgentResponse, AgentStats,
    TableCreate, TableResponse,
    ActionRequest, ActionResponse,
    JoinTableRequest, JoinTableResponse,
    GameHistoryResponse, GameActionResponse,
)
from backend.auth.auth import generate_api_key, hash_api_key, get_current_agent
from backend.game.game_engine import get_table, create_table, list_tables
from backend.api.websocket_manager import manager

router = APIRouter()
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


# ── Auth dependency ────────────────────────────────────────────────────────────

async def auth_required(
    api_key: Optional[str] = Security(API_KEY_HEADER),
    db: AsyncSession = Depends(get_db),
) -> Agent:
    return await get_current_agent(api_key=api_key, db=db)


# ── Agent routes ───────────────────────────────────────────────────────────────

@router.post("/agents/register", response_model=AgentRegisterResponse, status_code=201)
async def register_agent(body: AgentRegister, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Agent).where(Agent.name == body.name))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Agent name already taken")

    raw_key = generate_api_key()
    hashed = hash_api_key(raw_key)
    agent = Agent(name=body.name, api_key=hashed)
    db.add(agent)
    await db.flush()
    await db.refresh(agent)
    return AgentRegisterResponse(
        id=agent.id,
        name=agent.name,
        total_chips=agent.total_chips,
        games_played=agent.games_played,
        games_won=agent.games_won,
        created_at=agent.created_at,
        api_key=raw_key,
    )


@router.get("/agents/me", response_model=AgentResponse)
async def get_me(agent: Agent = Depends(auth_required)):
    return agent


@router.get("/agents/{agent_id}/stats", response_model=AgentStats)
async def get_agent_stats(agent_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    win_rate = agent.games_won / agent.games_played if agent.games_played > 0 else 0.0
    return AgentStats(
        id=agent.id,
        name=agent.name,
        total_chips=agent.total_chips,
        games_played=agent.games_played,
        games_won=agent.games_won,
        win_rate=win_rate,
        created_at=agent.created_at,
    )


# ── Table routes ───────────────────────────────────────────────────────────────

@router.get("/tables", response_model=list[TableResponse])
async def list_all_tables(db: AsyncSession = Depends(get_db)):
    in_memory = list_tables()
    tables_out = []
    for t in in_memory:
        tables_out.append(TableResponse(
            id=t.table_id,
            name=t.name,
            max_players=t.max_players,
            small_blind=t.small_blind,
            big_blind=t.big_blind,
            status=t.state.value,
            player_count=len(t.players),
            created_at=datetime.utcnow(),
        ))
    return tables_out


@router.post("/tables", response_model=TableResponse, status_code=201)
async def create_new_table(body: TableCreate, db: AsyncSession = Depends(get_db)):
    table = create_table(
        name=body.name,
        max_players=body.max_players,
        small_blind=body.small_blind,
        big_blind=body.big_blind,
    )
    db_table = TableModel(
        id=table.table_id,
        name=table.name,
        max_players=table.max_players,
        small_blind=table.small_blind,
        big_blind=table.big_blind,
        status="waiting",
    )
    db.add(db_table)
    return TableResponse(
        id=table.table_id,
        name=table.name,
        max_players=table.max_players,
        small_blind=table.small_blind,
        big_blind=table.big_blind,
        status=table.state.value,
        player_count=0,
        created_at=datetime.utcnow(),
    )


@router.get("/tables/{table_id}", response_model=TableResponse)
async def get_table_info(table_id: str):
    table = get_table(table_id)
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")
    return TableResponse(
        id=table.table_id,
        name=table.name,
        max_players=table.max_players,
        small_blind=table.small_blind,
        big_blind=table.big_blind,
        status=table.state.value,
        player_count=len(table.players),
        created_at=datetime.utcnow(),
    )


@router.post("/tables/{table_id}/join", response_model=JoinTableResponse)
async def join_table(
    table_id: str,
    body: JoinTableRequest = JoinTableRequest(),
    agent: Agent = Depends(auth_required),
):
    table = get_table(table_id)
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")
    try:
        seat = table.add_player(
            player_id=str(agent.id),
            name=agent.name,
            chips=body.chips,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    await manager.broadcast(table_id, {"type": "player_joined", "player": agent.name, "seat": seat, "game_state": table.to_dict()})
    return JoinTableResponse(success=True, seat=seat, message=f"Joined table at seat {seat}")


@router.post("/tables/{table_id}/leave")
async def leave_table(table_id: str, agent: Agent = Depends(auth_required)):
    table = get_table(table_id)
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")
    table.remove_player(str(agent.id))
    await manager.broadcast(table_id, {"type": "player_left", "player": agent.name, "game_state": table.to_dict()})
    return {"success": True, "message": "Left table"}


@router.get("/tables/{table_id}/game")
async def get_game_state(table_id: str, agent: Optional[Agent] = Depends(auth_required)):
    table = get_table(table_id)
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")
    viewer_id = str(agent.id) if agent else None
    return table.to_dict(viewer_id=viewer_id)


@router.post("/tables/{table_id}/start")
async def start_game(table_id: str, agent: Agent = Depends(auth_required), db: AsyncSession = Depends(get_db)):
    table = get_table(table_id)
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")
    if not table.can_start():
        raise HTTPException(status_code=400, detail="Cannot start game (need at least 2 players with chips, or game already running)")
    game_id = table.start_game()
    db_game = Game(id=game_id, table_id=table_id, status="active", pot=0)
    db.add(db_game)
    await manager.broadcast(table_id, {"type": "game_started", "game_id": game_id, "game_state": table.to_dict()})
    return {"success": True, "game_id": game_id}


@router.post("/tables/{table_id}/action", response_model=ActionResponse)
async def submit_action(
    table_id: str,
    body: ActionRequest,
    agent: Agent = Depends(auth_required),
    db: AsyncSession = Depends(get_db),
):
    table = get_table(table_id)
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")
    try:
        game_state = table.process_action(
            player_id=str(agent.id),
            action=body.action,
            amount=body.amount,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Persist action to DB
    if table.game_id:
        db_action = GameActionModel(
            game_id=table.game_id,
            agent_id=agent.id,
            round=table.round_name,
            action_type=body.action,
            amount=body.amount,
        )
        db.add(db_action)
        # Update game status if finished
        if table.state.value == "finished":
            await db.execute(
                update(Game).where(Game.id == table.game_id).values(
                    status="finished",
                    finished_at=datetime.utcnow(),
                    pot=sum(p.amount for p in table.pots),
                    community_cards=[c.to_dict() for c in table.community_cards],
                )
            )
            # Update agent stats for all players at the table
            winner_player_ids = {w["player_id"] for w in table.winners}
            for pid, player in table.players.items():
                if not player.is_active:
                    continue
                result_a = await db.execute(select(Agent).where(Agent.name == player.name))
                db_agent = result_a.scalar_one_or_none()
                if db_agent:
                    new_played = db_agent.games_played + 1
                    new_won = db_agent.games_won + (1 if pid in winner_player_ids else 0)
                    await db.execute(
                        update(Agent).where(Agent.id == db_agent.id).values(
                            games_played=new_played,
                            games_won=new_won,
                        )
                    )

    await manager.broadcast(table_id, {"type": "game_action", "action": body.action, "game_state": game_state})
    return ActionResponse(success=True, message=f"Action {body.action} processed", game_state=game_state)


@router.get("/tables/{table_id}/valid_actions")
async def get_valid_actions(table_id: str, agent: Agent = Depends(auth_required)):
    table = get_table(table_id)
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")
    return {"valid_actions": table.get_valid_actions(str(agent.id))}


# ── Game history routes ────────────────────────────────────────────────────────

@router.get("/games/{game_id}", response_model=GameHistoryResponse)
async def get_game_history(game_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Game).where(Game.id == game_id))
    game = result.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game


@router.get("/games/{game_id}/actions", response_model=list[GameActionResponse])
async def get_game_actions(game_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(GameActionModel).where(GameActionModel.game_id == game_id))
    return result.scalars().all()
