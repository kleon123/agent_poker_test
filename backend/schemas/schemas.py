from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field


# ── Agent schemas ──────────────────────────────────────────────────────────────

class AgentRegister(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class AgentResponse(BaseModel):
    id: int
    name: str
    total_chips: int
    games_played: int
    games_won: int
    created_at: datetime

    model_config = {"from_attributes": True}


class AgentRegisterResponse(AgentResponse):
    api_key: str


class AgentStats(BaseModel):
    id: int
    name: str
    total_chips: int
    games_played: int
    games_won: int
    win_rate: float
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Table schemas ──────────────────────────────────────────────────────────────

class TableCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    max_players: int = Field(default=6, ge=2, le=10)
    small_blind: int = Field(default=10, ge=1)
    big_blind: int = Field(default=20, ge=2)


class TableResponse(BaseModel):
    id: str
    name: str
    max_players: int
    small_blind: int
    big_blind: int
    status: str
    player_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Game schemas ───────────────────────────────────────────────────────────────

class CardSchema(BaseModel):
    rank: int
    suit: str
    display: str
    rank_name: str
    suit_symbol: str


class PlayerSchema(BaseModel):
    player_id: str
    name: str
    chips: int
    seat: int
    is_active: bool
    is_folded: bool
    is_all_in: bool
    current_bet: int
    total_bet_this_round: int
    hole_cards: List[Optional[CardSchema]]
    hole_cards_count: int


class PotSchema(BaseModel):
    amount: int
    eligible_players: List[str]


class GameStateResponse(BaseModel):
    table_id: str
    game_id: Optional[str]
    name: str
    state: str
    round: str
    community_cards: List[CardSchema]
    pots: List[PotSchema]
    total_pot: int
    players: dict
    current_player_id: Optional[str]
    dealer_seat: int
    small_blind: int
    big_blind: int
    current_raise: int
    min_raise: int
    winners: List[dict]
    game_log: List[str]
    max_players: int


# ── Action schemas ─────────────────────────────────────────────────────────────

class ActionRequest(BaseModel):
    action: str = Field(..., pattern="^(fold|check|call|raise|all_in)$")
    amount: int = Field(default=0, ge=0)


class ActionResponse(BaseModel):
    success: bool
    message: str
    game_state: Optional[dict] = None


# ── Join/Leave schemas ─────────────────────────────────────────────────────────

class JoinTableRequest(BaseModel):
    chips: Optional[int] = None


class JoinTableResponse(BaseModel):
    success: bool
    seat: int
    message: str


# ── Game history schemas ───────────────────────────────────────────────────────

class GameHistoryResponse(BaseModel):
    id: str
    table_id: str
    status: str
    pot: int
    community_cards: Optional[Any]
    created_at: datetime
    finished_at: Optional[datetime]

    model_config = {"from_attributes": True}


class GameActionResponse(BaseModel):
    id: int
    game_id: str
    agent_id: int
    round: str
    action_type: str
    amount: int
    created_at: datetime

    model_config = {"from_attributes": True}
