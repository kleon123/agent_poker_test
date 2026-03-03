from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from app.game_engine.card import Card, Deck
from app.game_engine.constants import (
    BIG_BLIND,
    SMALL_BLIND,
    STARTING_CHIPS,
    GamePhase,
    PlayerAction,
    PlayerStatus,
)
from app.game_engine.hand_evaluator import HandEvaluator


@dataclass
class Player:
    id: str
    name: str
    chips: int
    cards: List[Card] = field(default_factory=list)
    status: PlayerStatus = PlayerStatus.ACTIVE
    current_bet: int = 0
    total_bet_this_round: int = 0
    is_dealer: bool = False
    is_small_blind: bool = False
    is_big_blind: bool = False

    def to_dict(self, show_cards: bool = False) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "chips": self.chips,
            "cards": [c.to_dict() for c in self.cards] if show_cards else [None] * len(self.cards),
            "status": self.status.value,
            "current_bet": self.current_bet,
            "total_bet_this_round": self.total_bet_this_round,
            "is_dealer": self.is_dealer,
            "is_small_blind": self.is_small_blind,
            "is_big_blind": self.is_big_blind,
        }


@dataclass
class GameState:
    game_id: str
    table_id: str
    phase: GamePhase
    players: Dict[str, Player]
    community_cards: List[Card]
    pot: int
    current_bet: int
    current_player_id: Optional[str]
    dealer_id: str
    small_blind_id: str
    big_blind_id: str
    hand_number: int
    last_action: Optional[dict] = None
    winner_info: Optional[dict] = None


class PokerGame:
    def __init__(
        self,
        game_id: str,
        table_id: str,
        player_ids: List[str],
        player_names: List[str],
        starting_chips: int = STARTING_CHIPS,
        small_blind: int = SMALL_BLIND,
        big_blind: int = BIG_BLIND,
    ):
        self.game_id = game_id
        self.table_id = table_id
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.hand_number = 0
        self.phase = GamePhase.WAITING
        self.community_cards: List[Card] = []
        self.pot = 0
        self.current_bet = 0
        self.current_player_id: Optional[str] = None
        self.dealer_id: Optional[str] = None
        self.small_blind_id: Optional[str] = None
        self.big_blind_id: Optional[str] = None
        self.last_action: Optional[dict] = None
        self.winner_info: Optional[dict] = None
        self.deck = Deck()
        self._side_pots: List[dict] = []
        self._players_acted_this_round: set = set()
        self._last_aggressor: Optional[str] = None

        # Ordered list of player ids (seat order)
        self._player_order: List[str] = list(player_ids)
        self.players: Dict[str, Player] = {
            pid: Player(id=pid, name=player_names[i], chips=starting_chips)
            for i, pid in enumerate(player_ids)
        }

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def start_hand(self) -> GameState:
        """Deal cards and post blinds for a new hand."""
        self.hand_number += 1
        self.phase = GamePhase.PRE_FLOP
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.last_action = None
        self.winner_info = None
        self._side_pots = []
        self._players_acted_this_round = set()
        self._last_aggressor = None

        # Reset per-player hand state
        active_player_ids = [
            pid for pid in self._player_order if self.players[pid].chips > 0
        ]
        if len(active_player_ids) < 2:
            raise ValueError("Need at least 2 players with chips to start a hand")

        for pid in self._player_order:
            p = self.players[pid]
            p.cards = []
            p.current_bet = 0
            p.total_bet_this_round = 0
            p.is_dealer = False
            p.is_small_blind = False
            p.is_big_blind = False
            if p.chips > 0:
                p.status = PlayerStatus.ACTIVE
            else:
                p.status = PlayerStatus.OUT

        # Rotate dealer
        self._assign_positions(active_player_ids)

        # Deal hole cards
        self.deck = Deck()
        self.deck.shuffle()
        for _ in range(2):
            for pid in active_player_ids:
                self.players[pid].cards.append(self.deck.deal())

        # Post blinds
        self._post_blind(self.small_blind_id, self.small_blind)  # type: ignore[arg-type]
        self._post_blind(self.big_blind_id, self.big_blind)  # type: ignore[arg-type]
        self.current_bet = self.big_blind

        # First to act pre-flop is after big blind
        self.current_player_id = self._next_active_player(self.big_blind_id)  # type: ignore[arg-type]
        self._last_aggressor = self.big_blind_id

        return self.get_state()

    def process_action(
        self, player_id: str, action: PlayerAction, amount: Optional[int] = None
    ) -> GameState:
        """Process a player action and advance game state."""
        if self.phase in (GamePhase.WAITING, GamePhase.FINISHED):
            raise ValueError(f"No action possible in phase {self.phase}")
        if self.current_player_id != player_id:
            raise ValueError(f"It is not player {player_id}'s turn")

        player = self.players[player_id]
        valid = {a for a, _, _ in self.get_valid_actions(player_id)}
        if action not in valid:
            raise ValueError(f"Action {action} is not valid for player {player_id}")

        if action == PlayerAction.FOLD:
            player.status = PlayerStatus.FOLDED

        elif action == PlayerAction.CHECK:
            pass  # no chips moved

        elif action == PlayerAction.CALL:
            call_amount = min(self.current_bet - player.current_bet, player.chips)
            self._place_bet(player, call_amount)
            if player.chips == 0:
                player.status = PlayerStatus.ALL_IN

        elif action == PlayerAction.BET:
            if amount is None or amount <= 0:
                raise ValueError("Bet amount required")
            bet_amount = min(amount, player.chips)
            self._place_bet(player, bet_amount)
            self.current_bet = player.current_bet
            self._last_aggressor = player_id
            self._players_acted_this_round = {player_id}
            if player.chips == 0:
                player.status = PlayerStatus.ALL_IN

        elif action == PlayerAction.RAISE:
            if amount is None or amount <= 0:
                raise ValueError("Raise amount required")
            # amount = total bet player wants to put in
            raise_to = min(amount, player.chips + player.current_bet)
            additional = raise_to - player.current_bet
            self._place_bet(player, additional)
            self.current_bet = player.current_bet
            self._last_aggressor = player_id
            self._players_acted_this_round = {player_id}
            if player.chips == 0:
                player.status = PlayerStatus.ALL_IN

        elif action == PlayerAction.ALL_IN:
            all_in_amount = player.chips
            self._place_bet(player, all_in_amount)
            if player.current_bet > self.current_bet:
                self.current_bet = player.current_bet
                self._last_aggressor = player_id
                self._players_acted_this_round = {player_id}
            player.status = PlayerStatus.ALL_IN

        self.last_action = {
            "player_id": player_id,
            "action": action.value,
            "amount": amount,
        }
        self._players_acted_this_round.add(player_id)

        # Advance turn
        self._advance(player_id)
        return self.get_state()

    def get_valid_actions(self, player_id: str) -> List[Tuple[PlayerAction, Optional[int], Optional[int]]]:
        """Returns list of (action, min_amount, max_amount). Amounts are None when N/A."""
        if self.current_player_id != player_id:
            return []
        player = self.players[player_id]
        if player.status in (PlayerStatus.FOLDED, PlayerStatus.ALL_IN, PlayerStatus.OUT):
            return []

        actions = []
        call_amount = self.current_bet - player.current_bet

        actions.append((PlayerAction.FOLD, None, None))

        if call_amount == 0:
            actions.append((PlayerAction.CHECK, None, None))
        else:
            actual_call = min(call_amount, player.chips)
            actions.append((PlayerAction.CALL, actual_call, actual_call))

        # Bet or raise
        if self.current_bet == 0:
            # Can bet
            min_bet = self.big_blind
            if player.chips >= min_bet:
                actions.append((PlayerAction.BET, min_bet, player.chips))
        else:
            # Can raise: total must be at least current_bet * 2
            min_raise_to = self.current_bet + self.big_blind
            if player.chips + player.current_bet >= min_raise_to:
                actions.append((PlayerAction.RAISE, min_raise_to, player.chips + player.current_bet))

        # All-in is always available if player has chips
        if player.chips > 0:
            actions.append((PlayerAction.ALL_IN, player.chips, player.chips))

        return actions

    def get_state(self) -> GameState:
        return GameState(
            game_id=self.game_id,
            table_id=self.table_id,
            phase=self.phase,
            players=self.players,
            community_cards=self.community_cards,
            pot=self.pot,
            current_bet=self.current_bet,
            current_player_id=self.current_player_id,
            dealer_id=self.dealer_id,  # type: ignore[arg-type]
            small_blind_id=self.small_blind_id,  # type: ignore[arg-type]
            big_blind_id=self.big_blind_id,  # type: ignore[arg-type]
            hand_number=self.hand_number,
            last_action=self.last_action,
            winner_info=self.winner_info,
        )

    def get_state_for_observer(self) -> dict:
        """All cards visible (for spectators after showdown or for debugging)."""
        state = self._state_to_dict()
        for pid, player in self.players.items():
            state["players"][pid] = player.to_dict(show_cards=True)
        return state

    def get_state_for_player(self, player_id: str) -> dict:
        """Player sees own cards, others' cards hidden (unless showdown)."""
        state = self._state_to_dict()
        show_all = self.phase in (GamePhase.SHOWDOWN, GamePhase.FINISHED)
        for pid, player in self.players.items():
            show = (pid == player_id) or show_all
            state["players"][pid] = player.to_dict(show_cards=show)
        return state

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _state_to_dict(self) -> dict:
        return {
            "game_id": self.game_id,
            "table_id": self.table_id,
            "phase": self.phase.value,
            "community_cards": [c.to_dict() for c in self.community_cards],
            "pot": self.pot,
            "current_bet": self.current_bet,
            "current_player_id": self.current_player_id,
            "dealer_id": self.dealer_id,
            "small_blind_id": self.small_blind_id,
            "big_blind_id": self.big_blind_id,
            "hand_number": self.hand_number,
            "last_action": self.last_action,
            "winner_info": self.winner_info,
            "players": {},  # populated by caller
        }

    def _assign_positions(self, active_ids: List[str]) -> None:
        n = len(active_ids)
        if self.dealer_id is None or self.dealer_id not in active_ids:
            dealer_idx = 0
        else:
            old_idx = active_ids.index(self.dealer_id)
            dealer_idx = (old_idx + 1) % n

        self.dealer_id = active_ids[dealer_idx]
        self.players[self.dealer_id].is_dealer = True

        if n == 2:
            # Heads-up: dealer is small blind
            sb_idx = dealer_idx
            bb_idx = (dealer_idx + 1) % n
        else:
            sb_idx = (dealer_idx + 1) % n
            bb_idx = (dealer_idx + 2) % n

        self.small_blind_id = active_ids[sb_idx]
        self.big_blind_id = active_ids[bb_idx]
        self.players[self.small_blind_id].is_small_blind = True
        self.players[self.big_blind_id].is_big_blind = True

    def _post_blind(self, player_id: str, amount: int) -> None:
        player = self.players[player_id]
        actual = min(amount, player.chips)
        player.chips -= actual
        player.current_bet += actual
        player.total_bet_this_round += actual
        self.pot += actual
        if player.chips == 0:
            player.status = PlayerStatus.ALL_IN

    def _place_bet(self, player: Player, amount: int) -> None:
        actual = min(amount, player.chips)
        player.chips -= actual
        player.current_bet += actual
        player.total_bet_this_round += actual
        self.pot += actual

    def _next_active_player(self, after_id: str) -> Optional[str]:
        """Return next player who can act (ACTIVE status) after given id."""
        try:
            start = self._player_order.index(after_id)
        except ValueError:
            return None
        n = len(self._player_order)
        for i in range(1, n + 1):
            pid = self._player_order[(start + i) % n]
            if self.players[pid].status == PlayerStatus.ACTIVE:
                return pid
        return None

    def _active_players(self) -> List[str]:
        return [
            pid for pid in self._player_order
            if self.players[pid].status == PlayerStatus.ACTIVE
        ]

    def _players_in_hand(self) -> List[str]:
        """Players still in the hand (not folded, not out)."""
        return [
            pid for pid in self._player_order
            if self.players[pid].status in (PlayerStatus.ACTIVE, PlayerStatus.ALL_IN)
        ]

    def _betting_complete(self) -> bool:
        """Check if the current betting round is over."""
        active = self._active_players()
        if len(active) == 0:
            return True
        if len(self._players_in_hand()) == 1:
            return True
        # All active players must have acted and matched the current bet
        for pid in active:
            player = self.players[pid]
            if pid not in self._players_acted_this_round:
                return False
            if player.current_bet < self.current_bet and player.chips > 0:
                return False
        return True

    def _advance(self, last_actor_id: str) -> None:
        """Move to next player or next phase."""
        # Check for single player remaining in hand
        in_hand = self._players_in_hand()
        if len(in_hand) == 1:
            self._award_pot_uncontested(in_hand[0])
            return

        if self._betting_complete():
            self._move_to_next_phase()
        else:
            self.current_player_id = self._next_active_player(last_actor_id)

    def _move_to_next_phase(self) -> None:
        """Advance to the next game phase."""
        # Reset per-round bets
        for p in self.players.values():
            p.current_bet = 0
        self.current_bet = 0
        self._players_acted_this_round = set()
        self._last_aggressor = None

        phase_order = [GamePhase.PRE_FLOP, GamePhase.FLOP, GamePhase.TURN, GamePhase.RIVER, GamePhase.SHOWDOWN]
        try:
            idx = phase_order.index(self.phase)
        except ValueError:
            return

        next_phase = phase_order[idx + 1] if idx + 1 < len(phase_order) else GamePhase.SHOWDOWN

        # If only all-in players remain (no one can bet), run out the board
        if len(self._active_players()) == 0 and next_phase != GamePhase.SHOWDOWN:
            self._run_out_board()
            return

        self.phase = next_phase

        if self.phase == GamePhase.FLOP:
            self.community_cards.append(self.deck.deal())
            self.community_cards.append(self.deck.deal())
            self.community_cards.append(self.deck.deal())
            self.current_player_id = self._first_active_after_dealer()

        elif self.phase == GamePhase.TURN:
            self.community_cards.append(self.deck.deal())
            self.current_player_id = self._first_active_after_dealer()

        elif self.phase == GamePhase.RIVER:
            self.community_cards.append(self.deck.deal())
            self.current_player_id = self._first_active_after_dealer()

        elif self.phase == GamePhase.SHOWDOWN:
            self._showdown()

    def _run_out_board(self) -> None:
        """Deal remaining community cards without betting (all players all-in)."""
        while len(self.community_cards) < 5:
            self.community_cards.append(self.deck.deal())
        self.phase = GamePhase.SHOWDOWN
        self._showdown()

    def _first_active_after_dealer(self) -> Optional[str]:
        return self._next_active_player(self.dealer_id)  # type: ignore[arg-type]

    def _award_pot_uncontested(self, winner_id: str) -> None:
        """Award entire pot to the sole remaining player."""
        winner = self.players[winner_id]
        winner.chips += self.pot
        self.winner_info = {
            "winners": [{"player_id": winner_id, "player_name": winner.name, "amount": self.pot}],
            "pot": self.pot,
            "hand": None,
        }
        self.pot = 0
        self.phase = GamePhase.FINISHED
        self.current_player_id = None

    def _showdown(self) -> None:
        """Evaluate hands and distribute pot(s)."""
        self.phase = GamePhase.SHOWDOWN
        self.current_player_id = None

        in_hand = self._players_in_hand()
        if not in_hand:
            self.phase = GamePhase.FINISHED
            return

        # Calculate side pots
        pots = self._calculate_side_pots()
        all_winners: list[dict] = []

        for pot_info in pots:
            eligible = pot_info["eligible"]
            pot_amount = pot_info["amount"]
            if not eligible:
                continue
            if len(eligible) == 1:
                winner_id = eligible[0]
                self.players[winner_id].chips += pot_amount
                all_winners.append({
                    "player_id": winner_id,
                    "player_name": self.players[winner_id].name,
                    "amount": pot_amount,
                    "hand": None,
                })
                continue

            # Evaluate hands for eligible players
            hand_results = {}
            for pid in eligible:
                available = self.players[pid].cards + self.community_cards
                hand_results[pid] = HandEvaluator.evaluate(available)

            # Find best hand(s)
            best_score = max(hand_results[pid].score for pid in eligible)
            winners = [pid for pid in eligible if hand_results[pid].score == best_score]

            split = pot_amount // len(winners)
            remainder = pot_amount % len(winners)

            for i, wid in enumerate(winners):
                award = split + (1 if i == 0 else 0) * remainder
                self.players[wid].chips += award
                all_winners.append({
                    "player_id": wid,
                    "player_name": self.players[wid].name,
                    "amount": award,
                    "hand": hand_results[wid].description,
                    "hand_rank": hand_results[wid].rank.value,
                })

        self.winner_info = {"winners": all_winners, "pot": sum(p["amount"] for p in all_winners)}
        self.pot = 0
        self.phase = GamePhase.FINISHED

    def _calculate_side_pots(self) -> List[dict]:
        """Calculate side pots based on all-in amounts."""
        in_hand = self._players_in_hand()
        # Collect total contributions per player across the entire hand
        contributions: Dict[str, int] = {
            pid: self.players[pid].total_bet_this_round
            for pid in self._player_order
            if self.players[pid].status != PlayerStatus.OUT
               or self.players[pid].total_bet_this_round > 0
        }

        # Gather all unique contribution levels
        levels = sorted(set(contributions.values()))
        pots: List[dict] = []
        prev_level = 0

        for level in levels:
            if level == 0:
                continue
            increment = level - prev_level
            contributors = [pid for pid, amt in contributions.items() if amt >= level]
            pot_amount = increment * len(contributors)
            eligible = [pid for pid in contributors if pid in in_hand]
            if pot_amount > 0:
                pots.append({"amount": pot_amount, "eligible": eligible})
            prev_level = level

        if not pots:
            pots.append({"amount": self.pot, "eligible": in_hand})

        return pots
