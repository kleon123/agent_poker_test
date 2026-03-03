import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.game import Table, TablePlayer
from app.models.player import Agent
from app.schemas.game import TableCreate, TableDetailResponse, TableResponse
from app.services.connection_manager import connection_manager
from app.services.game_service import GameService

router = APIRouter(tags=["tables"])


async def _get_agent_by_key(api_key: str, db: AsyncSession) -> Agent:
    result = await db.execute(select(Agent).where(Agent.api_key == api_key))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return agent


@router.post("/tables", response_model=TableResponse, status_code=201)
async def create_table(body: TableCreate, db: AsyncSession = Depends(get_db)):
    table = Table(
        id=str(uuid.uuid4()),
        name=body.name,
        max_players=body.max_players,
        min_players=body.min_players,
        small_blind=body.small_blind,
        big_blind=body.big_blind,
        starting_chips=body.starting_chips,
        status="waiting",
    )
    db.add(table)
    await db.commit()
    await db.refresh(table)
    return table


@router.get("/tables", response_model=List[TableResponse])
async def list_tables(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Table).order_by(Table.created_at.desc()))
    return result.scalars().all()


@router.get("/tables/{table_id}", response_model=TableDetailResponse)
async def get_table(table_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Table).where(Table.id == table_id))
    table = result.scalar_one_or_none()
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")
    svc = GameService(db)
    players = await svc.get_table_players(table_id)
    return {**table.__dict__, "players": players}


@router.post("/tables/{table_id}/join")
async def join_table(
    table_id: str,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="X-API-Key header required")
    agent = await _get_agent_by_key(x_api_key, db)

    result = await db.execute(select(Table).where(Table.id == table_id))
    table = result.scalar_one_or_none()
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")
    if table.status == "playing":
        raise HTTPException(status_code=400, detail="Game already in progress")

    # Check if already seated
    existing = await db.execute(
        select(TablePlayer).where(
            TablePlayer.table_id == table_id,
            TablePlayer.agent_id == agent.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already at this table")

    # Count current players
    count_result = await db.execute(
        select(TablePlayer).where(TablePlayer.table_id == table_id)
    )
    current_players = count_result.scalars().all()
    if len(current_players) >= table.max_players:
        raise HTTPException(status_code=400, detail="Table is full")

    seat_numbers = {p.seat_number for p in current_players}
    seat = next(i for i in range(table.max_players) if i not in seat_numbers)

    tp = TablePlayer(
        id=str(uuid.uuid4()),
        table_id=table_id,
        agent_id=agent.id,
        seat_number=seat,
        chips=table.starting_chips,
    )
    db.add(tp)
    await db.commit()

    await connection_manager.broadcast_to_table(table_id, {
        "type": "player_joined",
        "data": {"agent_id": agent.id, "name": agent.name, "seat": seat},
    })

    return {"message": "Joined table", "seat_number": seat}


@router.post("/tables/{table_id}/leave")
async def leave_table(
    table_id: str,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="X-API-Key header required")
    agent = await _get_agent_by_key(x_api_key, db)

    tp_result = await db.execute(
        select(TablePlayer).where(
            TablePlayer.table_id == table_id,
            TablePlayer.agent_id == agent.id,
        )
    )
    tp = tp_result.scalar_one_or_none()
    if not tp:
        raise HTTPException(status_code=404, detail="Not at this table")

    await db.delete(tp)
    await db.commit()

    await connection_manager.broadcast_to_table(table_id, {
        "type": "player_left",
        "data": {"agent_id": agent.id, "name": agent.name},
    })

    return {"message": "Left table"}


@router.post("/tables/{table_id}/start")
async def start_game(
    table_id: str,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="X-API-Key header required")
    agent = await _get_agent_by_key(x_api_key, db)

    result = await db.execute(select(Table).where(Table.id == table_id))
    table = result.scalar_one_or_none()
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")
    if table.status == "playing":
        raise HTTPException(status_code=400, detail="Game already in progress")

    svc = GameService(db)
    try:
        game = await svc.create_game(table_id)
        state = await svc.start_hand(game.game_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"game_id": game.game_id, "state": state}
