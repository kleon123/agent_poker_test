from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey, JSON, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    api_key: Mapped[str] = mapped_column(String(256), unique=True, index=True)
    total_chips: Mapped[int] = mapped_column(Integer, default=0)
    games_played: Mapped[int] = mapped_column(Integer, default=0)
    games_won: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.utcnow())

    game_players: Mapped[list["GamePlayer"]] = relationship("GamePlayer", back_populates="agent")
    actions: Mapped[list["GameAction"]] = relationship("GameAction", back_populates="agent")


class Table(Base):
    __tablename__ = "tables"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    max_players: Mapped[int] = mapped_column(Integer, default=6)
    small_blind: Mapped[int] = mapped_column(Integer, default=10)
    big_blind: Mapped[int] = mapped_column(Integer, default=20)
    status: Mapped[str] = mapped_column(String(20), default="waiting")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.utcnow())

    games: Mapped[list["Game"]] = relationship("Game", back_populates="table")


class Game(Base):
    __tablename__ = "games"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    table_id: Mapped[str] = mapped_column(String(36), ForeignKey("tables.id"))
    status: Mapped[str] = mapped_column(String(20), default="active")
    community_cards: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    pot: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.utcnow())
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    table: Mapped["Table"] = relationship("Table", back_populates="games")
    players: Mapped[list["GamePlayer"]] = relationship("GamePlayer", back_populates="game")
    actions: Mapped[list["GameAction"]] = relationship("GameAction", back_populates="game")
    logs: Mapped[list["GameLog"]] = relationship("GameLog", back_populates="game")


class GamePlayer(Base):
    __tablename__ = "game_players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    game_id: Mapped[str] = mapped_column(String(36), ForeignKey("games.id"))
    agent_id: Mapped[int] = mapped_column(Integer, ForeignKey("agents.id"))
    seat_number: Mapped[int] = mapped_column(Integer)
    chips_start: Mapped[int] = mapped_column(Integer)
    chips_end: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    position: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_winner: Mapped[bool] = mapped_column(Boolean, default=False)

    game: Mapped["Game"] = relationship("Game", back_populates="players")
    agent: Mapped["Agent"] = relationship("Agent", back_populates="game_players")


class GameAction(Base):
    __tablename__ = "game_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    game_id: Mapped[str] = mapped_column(String(36), ForeignKey("games.id"))
    agent_id: Mapped[int] = mapped_column(Integer, ForeignKey("agents.id"))
    round: Mapped[str] = mapped_column(String(20))
    action_type: Mapped[str] = mapped_column(String(20))
    amount: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.utcnow())

    game: Mapped["Game"] = relationship("Game", back_populates="actions")
    agent: Mapped["Agent"] = relationship("Agent", back_populates="actions")


class GameLog(Base):
    __tablename__ = "game_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    game_id: Mapped[str] = mapped_column(String(36), ForeignKey("games.id"))
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.utcnow())

    game: Mapped["Game"] = relationship("Game", back_populates="logs")
