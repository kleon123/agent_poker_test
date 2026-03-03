from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.game_engine.constants import GamePhase, PlayerAction
from app.game_engine.poker_game import PokerGame
from app.models.game import Game, GameAction, Table, TablePlayer
from app.models.player import Agent
from app.services.connection_manager import connection_manager


# In-memory game state: game_id -> PokerGame
active_games: Dict[str, PokerGame] = {}


class GameService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # Table helpers
    # ------------------------------------------------------------------

    async def get_table_players(self, table_id: str) -> List[dict]:
        result = await self.db.execute(
            select(TablePlayer, Agent)
            .join(Agent, Agent.id == TablePlayer.agent_id)
            .where(TablePlayer.table_id == table_id)
            .order_by(TablePlayer.seat_number)
        )
        rows = result.fetchall()
        players = []
        for tp, agent in rows:
            players.append({
                "seat_number": tp.seat_number,
                "agent_id": agent.id,
                "name": agent.name,
                "chips": tp.chips,
                "joined_at": tp.joined_at.isoformat() if tp.joined_at else None,
            })
        return players

    async def get_table_state(self, table_id: str) -> dict:
        result = await self.db.execute(select(Table).where(Table.id == table_id))
        table = result.scalar_one_or_none()
        if not table:
            raise ValueError(f"Table {table_id} not found")
        players = await self.get_table_players(table_id)
        return {
            "id": table.id,
            "name": table.name,
            "max_players": table.max_players,
            "min_players": table.min_players,
            "small_blind": table.small_blind,
            "big_blind": table.big_blind,
            "starting_chips": table.starting_chips,
            "status": table.status,
            "players": players,
        }

    # ------------------------------------------------------------------
    # Game creation
    # ------------------------------------------------------------------

    async def create_game(self, table_id: str) -> PokerGame:
        """Create a new PokerGame for the table and persist to DB."""
        result = await self.db.execute(select(Table).where(Table.id == table_id))
        table = result.scalar_one_or_none()
        if not table:
            raise ValueError(f"Table {table_id} not found")

        seat_result = await self.db.execute(
            select(TablePlayer, Agent)
            .join(Agent, Agent.id == TablePlayer.agent_id)
            .where(TablePlayer.table_id == table_id)
            .order_by(TablePlayer.seat_number)
        )
        rows = seat_result.fetchall()
        if len(rows) < table.min_players:
            raise ValueError(f"Need at least {table.min_players} players")

        player_ids = [agent.id for _, agent in rows]
        player_names = [agent.name for _, agent in rows]
        chip_map = {agent.id: tp.chips for tp, agent in rows}

        game_id = str(uuid.uuid4())
        poker_game = PokerGame(
            game_id=game_id,
            table_id=table_id,
            player_ids=player_ids,
            player_names=player_names,
            starting_chips=table.starting_chips,
            small_blind=table.small_blind,
            big_blind=table.big_blind,
        )

        # Override starting chips from table_players (in case of re-join)
        for pid, chips in chip_map.items():
            poker_game.players[pid].chips = chips

        db_game = Game(
            id=game_id,
            table_id=table_id,
            status="active",
            phase=GamePhase.WAITING.value,
            pot=0,
            community_cards=[],
        )
        self.db.add(db_game)

        # Update table status
        table.status = "playing"
        await self.db.commit()

        active_games[game_id] = poker_game
        return poker_game

    # ------------------------------------------------------------------
    # Game actions
    # ------------------------------------------------------------------

    async def start_hand(self, game_id: str) -> dict:
        """Deal cards and start the hand."""
        game = active_games.get(game_id)
        if game is None:
            raise ValueError(f"Game {game_id} not found in memory")
        state = game.start_hand()
        await self._persist_game_state(game_id, state)
        await self._broadcast_game_state(game_id, game)
        return game.get_state_for_observer()

    async def process_action(
        self,
        game_id: str,
        player_id: str,
        action: str,
        amount: Optional[int] = None,
    ) -> dict:
        game = active_games.get(game_id)
        if game is None:
            raise ValueError(f"Game {game_id} not found in memory")

        try:
            player_action = PlayerAction(action)
        except ValueError:
            raise ValueError(f"Invalid action: {action}")

        state = game.process_action(player_id, player_action, amount)

        # Persist action
        db_action = GameAction(
            id=str(uuid.uuid4()),
            game_id=game_id,
            player_id=player_id,
            action=action,
            amount=amount,
            phase=state.phase.value,
        )
        self.db.add(db_action)

        await self._persist_game_state(game_id, state)

        # Broadcast events
        table_id = game.table_id
        player_obj = game.players.get(player_id)
        await connection_manager.broadcast_to_table(table_id, {
            "type": "action",
            "data": {
                "player": {"id": player_id, "name": player_obj.name if player_obj else player_id},
                "action": action,
                "amount": amount,
                "pot": game.pot,
            },
        })

        if state.phase == GamePhase.FINISHED:
            await connection_manager.broadcast_to_table(table_id, {
                "type": "hand_result",
                "data": state.winner_info,
            })
            await self._finalize_game(game_id, state)
        else:
            await self._broadcast_game_state(game_id, game)

        return game.get_state_for_observer()

    async def get_game_state(
        self, game_id: str, player_id: Optional[str] = None
    ) -> dict:
        game = active_games.get(game_id)
        if game is None:
            # Try to load from DB (finished game)
            result = await self.db.execute(select(Game).where(Game.id == game_id))
            db_game = result.scalar_one_or_none()
            if not db_game:
                raise ValueError(f"Game {game_id} not found")
            return {
                "id": db_game.id,
                "table_id": db_game.table_id,
                "phase": db_game.phase,
                "status": db_game.status,
                "pot": db_game.pot,
                "community_cards": db_game.community_cards,
                "hand_number": db_game.hand_number,
                "winner_info": db_game.winner_info,
            }

        if player_id:
            return game.get_state_for_player(player_id)
        return game.get_state_for_observer()

    async def get_valid_actions(self, game_id: str, player_id: str) -> list:
        game = active_games.get(game_id)
        if game is None:
            raise ValueError(f"Game {game_id} not found")
        raw = game.get_valid_actions(player_id)
        return [
            {"action": a.value, "min_amount": mn, "max_amount": mx}
            for a, mn, mx in raw
        ]

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    async def _persist_game_state(self, game_id: str, state) -> None:
        result = await self.db.execute(select(Game).where(Game.id == game_id))
        db_game = result.scalar_one_or_none()
        if db_game is None:
            return
        db_game.phase = state.phase.value
        db_game.pot = state.pot
        db_game.hand_number = state.hand_number
        db_game.community_cards = [c.to_dict() for c in state.community_cards]
        if state.winner_info:
            db_game.winner_info = state.winner_info
        await self.db.commit()

    async def _finalize_game(self, game_id: str, state) -> None:
        result = await self.db.execute(select(Game).where(Game.id == game_id))
        db_game = result.scalar_one_or_none()
        if db_game:
            db_game.status = "finished"
            db_game.finished_at = datetime.now(timezone.utc)
            db_game.winner_info = state.winner_info

        # Update agent stats and table_player chips
        game = active_games.get(game_id)
        if game and state.winner_info:
            winner_ids = {w["player_id"] for w in state.winner_info.get("winners", [])}
            for pid, player in game.players.items():
                agent_result = await self.db.execute(select(Agent).where(Agent.id == pid))
                agent = agent_result.scalar_one_or_none()
                if agent:
                    agent.total_games += 1
                    if pid in winner_ids:
                        agent.wins += 1
                        won = sum(w["amount"] for w in state.winner_info["winners"] if w["player_id"] == pid)
                        agent.total_chips_won += won
                    else:
                        agent.losses += 1
                    agent.chips = player.chips
                    agent.last_active = datetime.now(timezone.utc)

                # Update table_player chips
                tp_result = await self.db.execute(
                    select(TablePlayer).where(
                        TablePlayer.table_id == game.table_id,
                        TablePlayer.agent_id == pid,
                    )
                )
                tp = tp_result.scalar_one_or_none()
                if tp:
                    tp.chips = player.chips

        await self.db.commit()

    async def _broadcast_game_state(self, game_id: str, game: PokerGame) -> None:
        table_id = game.table_id
        await connection_manager.broadcast_to_table(table_id, {
            "type": "game_state",
            "data": game.get_state_for_observer(),
        })
