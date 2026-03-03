from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class AgentCreate(BaseModel):
    name: str


class AgentResponse(BaseModel):
    id: str
    name: str
    chips: int
    total_games: int
    wins: int
    losses: int
    total_chips_won: int
    created_at: datetime
    last_active: datetime

    model_config = {"from_attributes": True}


class AgentRegisterResponse(AgentResponse):
    api_key: str
