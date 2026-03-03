import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.sqlite import JSON

from app.database import Base


class Table(Base):
    __tablename__ = "tables"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    max_players = Column(Integer, default=6)
    min_players = Column(Integer, default=2)
    small_blind = Column(Integer, default=10)
    big_blind = Column(Integer, default=20)
    starting_chips = Column(Integer, default=1000)
    status = Column(String, default="waiting")  # waiting, playing, finished
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Game(Base):
    __tablename__ = "games"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    table_id = Column(String, ForeignKey("tables.id"), nullable=False)
    hand_number = Column(Integer, default=0)
    phase = Column(String, default="waiting")
    status = Column(String, default="active")  # active, finished
    pot = Column(Integer, default=0)
    community_cards = Column(JSON, default=list)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    finished_at = Column(DateTime, nullable=True)
    winner_info = Column(JSON, nullable=True)


class GameAction(Base):
    __tablename__ = "game_actions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    game_id = Column(String, ForeignKey("games.id"), nullable=False)
    player_id = Column(String, nullable=False)
    action = Column(String, nullable=False)
    amount = Column(Integer, nullable=True)
    phase = Column(String, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class TablePlayer(Base):
    __tablename__ = "table_players"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    table_id = Column(String, ForeignKey("tables.id"), nullable=False)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False)
    seat_number = Column(Integer, nullable=False)
    chips = Column(Integer, nullable=False)
    joined_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
