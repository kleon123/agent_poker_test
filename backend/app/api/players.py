import secrets
import uuid
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.player import Agent
from app.schemas.game import StatsResponse
from app.schemas.player import AgentCreate, AgentRegisterResponse, AgentResponse

router = APIRouter(tags=["agents"])


@router.post("/agents/register", response_model=AgentRegisterResponse, status_code=201)
async def register_agent(body: AgentCreate, db: AsyncSession = Depends(get_db)):
    # Check name uniqueness
    result = await db.execute(select(Agent).where(Agent.name == body.name))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Agent name already taken")

    api_key = secrets.token_hex(32)
    agent = Agent(
        id=str(uuid.uuid4()),
        name=body.name,
        api_key=api_key,
        chips=1000,
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return agent


@router.get("/agents", response_model=List[AgentResponse])
async def list_agents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Agent).order_by(Agent.total_chips_won.desc()))
    return result.scalars().all()


@router.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent
