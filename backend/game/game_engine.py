import uuid
from enum import Enum
from typing import List, Optional, Dict, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime

from .card import Card, Deck
from .hand_evaluator import HandEvaluator


class GameState(str, Enum):
    WAITING = "waiting"
    PRE_FLOP = "pre_flop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"
    SHOWDOWN = "showdown"
    FINISHED = "finished"


class ActionType(str, Enum):
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    RAISE = "raise"
    ALL_IN = "all_in"
    BLIND = "blind"


@dataclass
class PlayerStats:
    games_played: int = 0
    games_won: int = 0
    total_winnings: int = 0
    hands_won: int = 0
    biggest_pot: int = 0


@dataclass
class Player:
    player_id: str
    name: str
    chips: int
    seat: int
    is_active: bool = True
    is_folded: bool = False
    is_all_in: bool = False
    hole_cards: List[Card] = field(default_factory=list)
    current_bet: int = 0
    total_bet_this_round: int = 0
    stats: PlayerStats = field(default_factory=PlayerStats)

    def to_dict(self, show_cards: bool = False) -> dict:
        return {
            "player_id": self.player_id,
            "name": self.name,
            "chips": self.chips,
            "seat": self.seat,
            "is_active": self.is_active,
            "is_folded": self.is_folded,
            "is_all_in": self.is_all_in,
            "current_bet": self.current_bet,
            "total_bet_this_round": self.total_bet_this_round,
            "hole_cards": [c.to_dict() for c in self.hole_cards] if show_cards else [None] * len(self.hole_cards),
            "hole_cards_count": len(self.hole_cards),
        }

    def reset_for_round(self):
        self.hole_cards = []
        self.current_bet = 0
        self.total_bet_this_round = 0
        self.is_folded = False
        self.is_all_in = False


@dataclass
class Pot:
    amount: int = 0
    eligible_players: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"amount": self.amount, "eligible_players": self.eligible_players}


@dataclass
class GameAction:
    player_id: str
    player_name: str
    action: ActionType
    amount: int
    round: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return {
            "player_id": self.player_id,
            "player_name": self.player_name,
            "action": self.action.value,
            "amount": self.amount,
            "round": self.round,
            "timestamp": self.timestamp,
        }


class Table:
    def __init__(
        self,
        table_id: str,
        name: str,
        max_players: int = 6,
        small_blind: int = 10,
        big_blind: int = 20,
        starting_chips: int = 1000,
    ):
        self.table_id = table_id
        self.name = name
        self.max_players = max_players
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.starting_chips = starting_chips

        self.players: Dict[str, Player] = {}  # player_id -> Player
        self.seat_map: Dict[int, Optional[str]] = {i: None for i in range(max_players)}

        self.state = GameState.WAITING
        self.deck = Deck()
        self.community_cards: List[Card] = []
        self.pots: List[Pot] = [Pot()]
        self.dealer_seat: int = 0
        self.current_player_idx: int = 0
        self.active_order: List[str] = []  # player_ids in betting order
        self.current_raise: int = big_blind
        self.last_raiser: Optional[str] = None
        self.actions_this_round: List[GameAction] = []
        self.all_actions: List[GameAction] = []
        self.game_log: List[str] = []
        self.game_id: Optional[str] = None
        self.round_name: str = ""
        self.winners: List[dict] = []
        self.min_raise: int = big_blind

    # ── Seat management ────────────────────────────────────────────────────────

    def add_player(self, player_id: str, name: str, chips: Optional[int] = None) -> int:
        if player_id in self.players:
            return self.players[player_id].seat
        if len(self.players) >= self.max_players:
            raise ValueError("Table is full")
        chips = chips if chips is not None else self.starting_chips
        seat = next(s for s, pid in self.seat_map.items() if pid is None)
        player = Player(player_id=player_id, name=name, chips=chips, seat=seat)
        self.players[player_id] = player
        self.seat_map[seat] = player_id
        self._log(f"{name} joined seat {seat}")
        return seat

    def remove_player(self, player_id: str):
        if player_id not in self.players:
            return
        player = self.players[player_id]
        self.seat_map[player.seat] = None
        del self.players[player_id]
        self._log(f"{player.name} left the table")

    # ── Game flow ──────────────────────────────────────────────────────────────

    def can_start(self) -> bool:
        active = [p for p in self.players.values() if p.chips > 0]
        return len(active) >= 2 and self.state in (GameState.WAITING, GameState.FINISHED)

    def start_game(self) -> str:
        if not self.can_start():
            raise ValueError("Cannot start game")
        self.game_id = str(uuid.uuid4())
        self.winners = []
        self._start_hand()
        return self.game_id

    def _start_hand(self):
        self.state = GameState.PRE_FLOP
        self.community_cards = []
        self.pots = [Pot()]
        self.actions_this_round = []
        self.round_name = "pre_flop"
        self.last_raiser = None

        # Reset players
        for p in self.players.values():
            if p.chips > 0:
                p.reset_for_round()
                p.is_active = True
            else:
                p.is_active = False

        # Build ordered seat list of active players
        seated = sorted(
            [p for p in self.players.values() if p.is_active],
            key=lambda p: p.seat,
        )
        if len(seated) < 2:
            self.state = GameState.WAITING
            return

        # Rotate dealer
        self._advance_dealer(seated)

        # Deal hole cards
        self.deck.reset()
        self.deck.shuffle()
        for _ in range(2):
            for p in self._players_from_dealer(seated):
                p.hole_cards.append(self.deck.deal_one())

        # Post blinds
        order = self._players_from_dealer(seated)
        if len(order) == 2:
            sb_player = order[0]  # dealer posts SB heads-up
            bb_player = order[1]
        else:
            sb_player = order[1]
            bb_player = order[2] if len(order) > 2 else order[0]

        self._post_blind(sb_player, self.small_blind, "small blind")
        self._post_blind(bb_player, self.big_blind, "big blind")

        self.current_raise = self.big_blind
        self.min_raise = self.big_blind

        # Build active_order for pre-flop (UTG acts first)
        self.active_order = [p.player_id for p in order]

        # Pre-flop: action starts after BB
        bb_idx = self.active_order.index(bb_player.player_id)
        self.current_player_idx = (bb_idx + 1) % len(self.active_order)
        self.last_raiser = bb_player.player_id  # BB is considered the "raiser" for call purposes

        self._log(f"New hand started. Dealer: seat {self.dealer_seat}")

    def _advance_dealer(self, seated: List[Player]):
        if not seated:
            return
        seats = [p.seat for p in seated]
        if self.dealer_seat not in seats:
            self.dealer_seat = seats[0]
        else:
            idx = seats.index(self.dealer_seat)
            self.dealer_seat = seats[(idx + 1) % len(seats)]

    def _players_from_dealer(self, seated: List[Player]) -> List[Player]:
        """Return players in order starting from dealer."""
        seats = [p.seat for p in seated]
        if self.dealer_seat not in seats:
            return seated
        start = seats.index(self.dealer_seat)
        return seated[start:] + seated[:start]

    def _post_blind(self, player: Player, amount: int, blind_name: str):
        actual = min(amount, player.chips)
        player.chips -= actual
        player.current_bet = actual
        player.total_bet_this_round = actual
        self.pots[0].amount += actual
        if player.chips == 0:
            player.is_all_in = True
        action = GameAction(
            player_id=player.player_id,
            player_name=player.name,
            action=ActionType.BLIND,
            amount=actual,
            round=self.round_name,
        )
        self.actions_this_round.append(action)
        self.all_actions.append(action)
        self._log(f"{player.name} posts {blind_name}: {actual}")

    # ── Actions ────────────────────────────────────────────────────────────────

    def get_current_player_id(self) -> Optional[str]:
        if self.state in (GameState.WAITING, GameState.SHOWDOWN, GameState.FINISHED):
            return None
        active = self._betting_eligible()
        if not active:
            return None
        return active[self.current_player_idx % len(active)]

    def _betting_eligible(self) -> List[str]:
        """Players who can still act (not folded, not all-in, active)."""
        return [
            pid for pid in self.active_order
            if pid in self.players
            and self.players[pid].is_active
            and not self.players[pid].is_folded
            and not self.players[pid].is_all_in
        ]

    def _call_amount(self, player: Player) -> int:
        max_bet = max(p.current_bet for p in self.players.values() if p.is_active)
        return min(max_bet - player.current_bet, player.chips)

    def process_action(self, player_id: str, action: str, amount: int = 0, viewer_id: Optional[str] = None) -> dict:
        if self.state in (GameState.WAITING, GameState.SHOWDOWN, GameState.FINISHED):
            raise ValueError(f"Cannot act in state {self.state}")
        current = self.get_current_player_id()
        if current != player_id:
            raise ValueError(f"Not your turn. Current player: {current}")

        player = self.players[player_id]
        action_type = ActionType(action)
        actual_amount = 0

        if action_type == ActionType.FOLD:
            player.is_folded = True
            self._log(f"{player.name} folds")

        elif action_type == ActionType.CHECK:
            call_amt = self._call_amount(player)
            if call_amt > 0:
                raise ValueError(f"Cannot check, must call {call_amt}")
            self._log(f"{player.name} checks")

        elif action_type == ActionType.CALL:
            call_amt = self._call_amount(player)
            if call_amt == 0:
                self._log(f"{player.name} checks (call 0)")
                action_type = ActionType.CHECK
            else:
                actual_amount = call_amt
                player.chips -= actual_amount
                player.current_bet += actual_amount
                player.total_bet_this_round += actual_amount
                self.pots[0].amount += actual_amount
                if player.chips == 0:
                    player.is_all_in = True
                    action_type = ActionType.ALL_IN
                self._log(f"{player.name} calls {actual_amount}")

        elif action_type == ActionType.RAISE:
            call_amt = self._call_amount(player)
            raise_extra = max(amount, self.min_raise)
            total_needed = call_amt + raise_extra
            if total_needed > player.chips:
                # treat as all-in
                action_type = ActionType.ALL_IN
                actual_amount = player.chips
            else:
                actual_amount = total_needed
            player.chips -= actual_amount
            player.current_bet += actual_amount
            player.total_bet_this_round += actual_amount
            self.pots[0].amount += actual_amount
            self.min_raise = raise_extra
            self.current_raise = player.current_bet
            self.last_raiser = player_id
            if player.chips == 0:
                player.is_all_in = True
                action_type = ActionType.ALL_IN
            self._log(f"{player.name} raises to {player.current_bet}")

        elif action_type == ActionType.ALL_IN:
            actual_amount = player.chips
            player.chips = 0
            player.current_bet += actual_amount
            player.total_bet_this_round += actual_amount
            self.pots[0].amount += actual_amount
            player.is_all_in = True
            if player.current_bet > self.current_raise:
                self.current_raise = player.current_bet
                self.last_raiser = player_id
            self._log(f"{player.name} goes all-in for {actual_amount}")

        game_action = GameAction(
            player_id=player_id,
            player_name=player.name,
            action=action_type,
            amount=actual_amount,
            round=self.round_name,
        )
        self.actions_this_round.append(game_action)
        self.all_actions.append(game_action)

        self._advance_action()

        return self.to_dict(viewer_id=viewer_id if viewer_id else player_id)

    def _advance_action(self):
        eligible = self._betting_eligible()
        active_non_folded = [
            p for p in self.players.values()
            if p.is_active and not p.is_folded
        ]

        # Only one player left
        if len(active_non_folded) <= 1:
            self._end_hand()
            return

        if self._betting_complete(eligible):
            self._next_round()
        else:
            # Move to next eligible player
            if not eligible:
                self._next_round()
                return
            # Find current position in active_order and advance
            current = self.get_current_player_id()
            # Move index forward
            all_order = self.active_order
            if current in all_order:
                idx = all_order.index(current)
            else:
                idx = self.current_player_idx

            # Find next eligible
            n = len(all_order)
            for i in range(1, n + 1):
                next_pid = all_order[(idx + i) % n]
                if next_pid in eligible:
                    self.current_player_idx = (idx + i) % n
                    return
            self._next_round()

    def _betting_complete(self, eligible: List[str]) -> bool:
        if not eligible:
            return True
        max_bet = max(
            p.current_bet for p in self.players.values()
            if p.is_active and not p.is_folded
        )
        # All eligible players have matched the bet and everyone has acted
        for pid in eligible:
            p = self.players[pid]
            if p.current_bet < max_bet:
                return False
        # If last raiser is None (no raise), everyone checked
        # Check that every eligible player has acted at least once this phase
        acted = {a.player_id for a in self.actions_this_round}
        for pid in eligible:
            if pid not in acted:
                return False
        # If there was a raise, players who haven't re-acted need to
        if self.last_raiser is not None:
            # All eligible must have acted AFTER the last raise
            last_raise_idx = None
            for i, a in enumerate(self.actions_this_round):
                if a.player_id == self.last_raiser and a.action in (ActionType.RAISE, ActionType.ALL_IN, ActionType.BLIND):
                    last_raise_idx = i
            if last_raise_idx is not None:
                post_raise_actors = {a.player_id for a in self.actions_this_round[last_raise_idx + 1:]}
                for pid in eligible:
                    if pid != self.last_raiser and pid not in post_raise_actors:
                        return False
        return True

    def _next_round(self):
        self._build_side_pots()
        # Reset bets for new round
        for p in self.players.values():
            p.current_bet = 0

        active_non_folded = [
            p for p in self.players.values()
            if p.is_active and not p.is_folded
        ]
        if len(active_non_folded) <= 1:
            self._end_hand()
            return

        self.actions_this_round = []
        self.last_raiser = None
        self.min_raise = self.big_blind

        if self.state == GameState.PRE_FLOP:
            self.state = GameState.FLOP
            self.round_name = "flop"
            self.community_cards.extend(self.deck.deal(3))
            self._log(f"Flop: {' '.join(str(c) for c in self.community_cards)}")
            self._set_postflop_order()

        elif self.state == GameState.FLOP:
            self.state = GameState.TURN
            self.round_name = "turn"
            self.community_cards.extend(self.deck.deal(1))
            self._log(f"Turn: {self.community_cards[-1]}")
            self._set_postflop_order()

        elif self.state == GameState.TURN:
            self.state = GameState.RIVER
            self.round_name = "river"
            self.community_cards.extend(self.deck.deal(1))
            self._log(f"River: {self.community_cards[-1]}")
            self._set_postflop_order()

        elif self.state == GameState.RIVER:
            self._end_hand()
            return

        # Check if everyone is all-in (skip to showdown)
        eligible = self._betting_eligible()
        if not eligible:
            self._run_out_cards_and_showdown()

    def _set_postflop_order(self):
        """Post-flop: action starts from first active player left of dealer."""
        seated = sorted(
            [p for p in self.players.values() if p.is_active and not p.is_folded],
            key=lambda p: p.seat,
        )
        order = self._players_from_dealer(seated)
        # Skip dealer itself for post-flop; first player after dealer acts first
        self.active_order = [p.player_id for p in order]
        if len(self.active_order) > 1:
            # post-flop: first to act is player after dealer
            self.active_order = self.active_order[1:] + [self.active_order[0]]
        self.current_player_idx = 0

    def _run_out_cards_and_showdown(self):
        """Deal remaining community cards and go to showdown."""
        while len(self.community_cards) < 5:
            if self.state == GameState.PRE_FLOP:
                self.community_cards.extend(self.deck.deal(3))
                self.state = GameState.FLOP
            elif self.state == GameState.FLOP:
                self.community_cards.extend(self.deck.deal(1))
                self.state = GameState.TURN
            elif self.state == GameState.TURN:
                self.community_cards.extend(self.deck.deal(1))
                self.state = GameState.RIVER
                break
        self._end_hand()

    def _build_side_pots(self):
        """Rebuild pots accounting for all-in players."""
        active = [p for p in self.players.values() if p.is_active and not p.is_folded]
        all_in_players = sorted(
            [p for p in active if p.is_all_in],
            key=lambda p: p.total_bet_this_round,
        )
        if not all_in_players:
            # Update eligible players in main pot
            self.pots[0].eligible_players = [p.player_id for p in active]
            return
        # Simple approach: keep single pot (side pots calculated at showdown)
        self.pots[0].eligible_players = [p.player_id for p in active]

    def _end_hand(self):
        self.state = GameState.SHOWDOWN
        self._determine_winners()
        self.state = GameState.FINISHED
        self._log("Hand complete")

    def _determine_winners(self):
        active = [p for p in self.players.values() if p.is_active and not p.is_folded]
        if len(active) == 1:
            winner = active[0]
            pot = sum(pot.amount for pot in self.pots)
            winner.chips += pot
            self.pots[0].amount = 0
            winner.stats.games_won += 1
            winner.stats.hands_won += 1
            self.winners = [{"player_id": winner.player_id, "name": winner.name, "amount": pot, "hand": "Last player standing"}]
            self._log(f"{winner.name} wins {pot} (last player)")
            return

        # Evaluate hands
        player_hands = {}
        for p in active:
            player_hands[p.player_id] = p.hole_cards + self.community_cards

        # Handle side pots
        total_pot = sum(pot.amount for pot in self.pots)
        self.winners = []

        winner_ids, evaluations = HandEvaluator.determine_winners(player_hands)

        # Split pot among winners
        share = total_pot // len(winner_ids)
        remainder = total_pot % len(winner_ids)

        for i, wid in enumerate(winner_ids):
            amt = share + (1 if i == 0 else 0) * remainder
            self.players[wid].chips += amt
            self.players[wid].stats.games_won += 1
            self.players[wid].stats.hands_won += 1
            hand_info = evaluations[wid]
            self.winners.append({
                "player_id": wid,
                "name": self.players[wid].name,
                "amount": amt,
                "hand": hand_info["hand_name"],
                "hand_rank": hand_info["rank"],
            })
            self._log(f"{self.players[wid].name} wins {amt} with {hand_info['hand_name']}")

        for pot in self.pots:
            pot.amount = 0

        # Update stats
        for p in self.players.values():
            if p.is_active:
                p.stats.games_played += 1

    # ── Serialization ──────────────────────────────────────────────────────────

    def to_dict(self, viewer_id: Optional[str] = None) -> dict:
        return {
            "table_id": self.table_id,
            "game_id": self.game_id,
            "name": self.name,
            "state": self.state.value,
            "round": self.round_name,
            "community_cards": [c.to_dict() for c in self.community_cards],
            "pots": [p.to_dict() for p in self.pots],
            "total_pot": sum(p.amount for p in self.pots),
            "players": {
                pid: p.to_dict(show_cards=(viewer_id == pid or self.state == GameState.SHOWDOWN))
                for pid, p in self.players.items()
            },
            "current_player_id": self.get_current_player_id(),
            "dealer_seat": self.dealer_seat,
            "small_blind": self.small_blind,
            "big_blind": self.big_blind,
            "current_raise": self.current_raise,
            "min_raise": self.min_raise,
            "winners": self.winners,
            "game_log": self.game_log[-20:],
            "max_players": self.max_players,
        }

    def get_valid_actions(self, player_id: str) -> List[dict]:
        if self.get_current_player_id() != player_id:
            return []
        player = self.players[player_id]
        call_amt = self._call_amount(player)
        actions = [{"action": "fold", "amount": 0}]
        if call_amt == 0:
            actions.append({"action": "check", "amount": 0})
        else:
            actions.append({"action": "call", "amount": call_amt})
        if player.chips > call_amt:
            actions.append({"action": "raise", "min_amount": self.min_raise, "amount": self.min_raise})
        if player.chips > 0:
            actions.append({"action": "all_in", "amount": player.chips})
        return actions

    def _log(self, message: str):
        ts = datetime.utcnow().strftime("%H:%M:%S")
        self.game_log.append(f"[{ts}] {message}")


# ── In-memory table registry ───────────────────────────────────────────────────

_tables: Dict[str, Table] = {}


def get_table(table_id: str) -> Optional[Table]:
    return _tables.get(table_id)


def create_table(name: str, max_players: int = 6, small_blind: int = 10, big_blind: int = 20) -> Table:
    table_id = str(uuid.uuid4())
    table = Table(table_id=table_id, name=name, max_players=max_players, small_blind=small_blind, big_blind=big_blind)
    _tables[table_id] = table
    return table


def list_tables() -> List[Table]:
    return list(_tables.values())


def delete_table(table_id: str):
    _tables.pop(table_id, None)
