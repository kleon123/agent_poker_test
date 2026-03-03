"""Initial schema

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "agents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("api_key", sa.String(256), nullable=False),
        sa.Column("total_chips", sa.Integer(), default=0),
        sa.Column("games_played", sa.Integer(), default=0),
        sa.Column("games_won", sa.Integer(), default=0),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("api_key"),
    )
    op.create_index("ix_agents_id", "agents", ["id"])
    op.create_index("ix_agents_name", "agents", ["name"])
    op.create_index("ix_agents_api_key", "agents", ["api_key"])

    op.create_table(
        "tables",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("max_players", sa.Integer(), default=6),
        sa.Column("small_blind", sa.Integer(), default=10),
        sa.Column("big_blind", sa.Integer(), default=20),
        sa.Column("status", sa.String(20), default="waiting"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "games",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("table_id", sa.String(36), sa.ForeignKey("tables.id"), nullable=True),
        sa.Column("status", sa.String(20), default="active"),
        sa.Column("community_cards", sa.JSON(), nullable=True),
        sa.Column("pot", sa.Integer(), default=0),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "game_players",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("game_id", sa.String(36), sa.ForeignKey("games.id"), nullable=True),
        sa.Column("agent_id", sa.Integer(), sa.ForeignKey("agents.id"), nullable=True),
        sa.Column("seat_number", sa.Integer(), nullable=False),
        sa.Column("chips_start", sa.Integer(), nullable=False),
        sa.Column("chips_end", sa.Integer(), nullable=True),
        sa.Column("position", sa.String(20), nullable=True),
        sa.Column("is_winner", sa.Boolean(), default=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_game_players_id", "game_players", ["id"])

    op.create_table(
        "game_actions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("game_id", sa.String(36), sa.ForeignKey("games.id"), nullable=True),
        sa.Column("agent_id", sa.Integer(), sa.ForeignKey("agents.id"), nullable=True),
        sa.Column("round", sa.String(20), nullable=False),
        sa.Column("action_type", sa.String(20), nullable=False),
        sa.Column("amount", sa.Integer(), default=0),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_game_actions_id", "game_actions", ["id"])

    op.create_table(
        "game_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("game_id", sa.String(36), sa.ForeignKey("games.id"), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_game_logs_id", "game_logs", ["id"])


def downgrade() -> None:
    op.drop_table("game_logs")
    op.drop_table("game_actions")
    op.drop_table("game_players")
    op.drop_table("games")
    op.drop_table("tables")
    op.drop_table("agents")
