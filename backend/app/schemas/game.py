from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class TableCreate(BaseModel):
    name: str
    max_players: int = 6
    min_players: int = 2
    small_blind: int = 10
    big_blind: int = 20
    starting_chips: int = 1000


class TableResponse(BaseModel):
    id: str
    name: str
    max_players: int
    min_players: int
    small_blind: int
    big_blind: int
    starting_chips: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TableDetailResponse(TableResponse):
    players: List[Dict[str, Any]] = []


class GameActionRequest(BaseModel):
    action: str
    amount: Optional[int] = None


class GameResponse(BaseModel):
    id: str
    table_id: str
    hand_number: int
    phase: str
    status: str
    pot: int
    community_cards: List[Any]
    started_at: datetime
    finished_at: Optional[datetime] = None
    winner_info: Optional[Any] = None

    model_config = {"from_attributes": True}


class ValidActionsResponse(BaseModel):
    player_id: str
    actions: List[Dict[str, Any]]


class StatsResponse(BaseModel):
    total_agents: int
    total_tables: int
    total_games: int
    active_games: int
