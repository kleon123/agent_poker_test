"""Texas Hold'em game engine."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from .agent import ACTION_CALL, ACTION_CHECK, ACTION_FOLD, ACTION_RAISE, BaseAgent
from .card import Card, Deck
from .hand_evaluator import best_hand, hand_name

logger = logging.getLogger(__name__)


@dataclass
class PlayerState:
    """Mutable state for one player within a hand."""

    name: str
    chips: int
    hand: List[Card] = field(default_factory=list)
    current_bet: int = 0
    folded: bool = False
    all_in: bool = False

    def reset_for_hand(self) -> None:
        self.hand = []
        self.current_bet = 0
        self.folded = False
        self.all_in = False


@dataclass
class GameState:
    """Snapshot of the game visible to agents and game logic."""

    players: List[PlayerState]
    community_cards: List[Card]
    pot: int
    current_bet: int
    stage: str  # 'preflop', 'flop', 'turn', 'river', 'showdown'
    dealer_index: int
    active_player_index: int
    min_raise: int

    def to_dict(self, player_index: Optional[int] = None) -> Dict:
        """Serialise the state to a plain dict.

        Each player's hole cards are only included for the player
        identified by *player_index* (so agents can only see their own
        cards).
        """
        return {
            "community_cards": [str(c) for c in self.community_cards],
            "pot": self.pot,
            "current_bet": self.current_bet,
            "stage": self.stage,
            "dealer_index": self.dealer_index,
            "min_raise": self.min_raise,
            "active_player_index": self.active_player_index,
            "players": [
                {
                    "name": p.name,
                    "chips": p.chips,
                    "current_bet": p.current_bet,
                    "folded": p.folded,
                    "all_in": p.all_in,
                    "hand": (
                        [str(c) for c in p.hand]
                        if player_index is not None and i == player_index
                        else []
                    ),
                }
                for i, p in enumerate(self.players)
            ],
        }


class TexasHoldemGame:
    """Runs a Texas Hold'em cash-game session with a list of agents.

    Parameters
    ----------
    agents:
        Ordered list of :class:`~poker.agent.BaseAgent` instances.
    starting_chips:
        Starting chip count for each player.
    small_blind:
        Small-blind amount (big blind is twice this).
    """

    def __init__(
        self,
        agents: Sequence[BaseAgent],
        starting_chips: int = 1000,
        small_blind: int = 10,
    ) -> None:
        if len(agents) < 2:
            raise ValueError("Need at least 2 agents to play")
        self.agents = list(agents)
        self.small_blind = small_blind
        self.big_blind = small_blind * 2
        self.players = [PlayerState(a.name, starting_chips) for a in agents]
        self.dealer_index = 0
        self.hand_number = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def play_hand(self) -> Optional[str]:
        """Play a single hand and return the winner's name (or None for split)."""
        active_players = [p for p in self.players if p.chips > 0]
        if len(active_players) < 2:
            raise RuntimeError("Not enough players with chips to play")

        self.hand_number += 1
        logger.info("=== Hand #%d ===", self.hand_number)

        deck = Deck()
        pot = 0

        for p in self.players:
            p.reset_for_hand()

        # --- Blinds ---
        n = len(self.players)
        sb_idx = (self.dealer_index + 1) % n
        bb_idx = (self.dealer_index + 2) % n

        pot += self._post_blind(self.players[sb_idx], self.small_blind)
        pot += self._post_blind(self.players[bb_idx], self.big_blind)
        current_bet = self.big_blind
        min_raise = self.big_blind

        # --- Deal hole cards ---
        for _ in range(2):
            for p in self.players:
                if p.chips > 0 or p.current_bet > 0:
                    p.hand.append(deck.deal())

        logger.info(
            "Blinds: %s posts SB=%d, %s posts BB=%d",
            self.players[sb_idx].name,
            self.small_blind,
            self.players[bb_idx].name,
            self.big_blind,
        )

        community_cards: List[Card] = []

        # --- Betting stages ---
        stages = [
            ("preflop", 0, (self.dealer_index + 3) % n),
            ("flop", 3, (self.dealer_index + 1) % n),
            ("turn", 1, (self.dealer_index + 1) % n),
            ("river", 1, (self.dealer_index + 1) % n),
        ]

        for stage_name, num_community, first_to_act in stages:
            if stage_name != "preflop":
                current_bet = 0
                min_raise = self.big_blind
                for p in self.players:
                    p.current_bet = 0

            for _ in range(num_community):
                community_cards.append(deck.deal())

            if stage_name != "preflop":
                logger.info(
                    "%s — community: %s",
                    stage_name.upper(),
                    [str(c) for c in community_cards],
                )

            state = self._make_state(
                community_cards, pot, current_bet, stage_name, min_raise
            )
            pot, current_bet, min_raise = self._betting_round(
                state,
                first_to_act,
                pot,
                current_bet,
                min_raise,
                community_cards,
                stage_name,
            )

            # Early finish if only one player remains
            still_in = [p for p in self.players if not p.folded]
            if len(still_in) == 1:
                winner = still_in[0]
                winner.chips += pot
                logger.info(
                    "%s wins %d (all others folded)", winner.name, pot
                )
                self._advance_dealer()
                return winner.name

        # --- Showdown ---
        still_in = [p for p in self.players if not p.folded]
        logger.info("SHOWDOWN — community: %s", [str(c) for c in community_cards])
        winner_name = self._showdown(still_in, community_cards, pot)
        self._advance_dealer()
        return winner_name

    def play_session(self, num_hands: int) -> Dict[str, int]:
        """Play *num_hands* hands and return final chip counts."""
        for _ in range(num_hands):
            active = [p for p in self.players if p.chips > 0]
            if len(active) < 2:
                break
            self.play_hand()
        return {p.name: p.chips for p in self.players}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _post_blind(self, player: PlayerState, amount: int) -> int:
        actual = min(amount, player.chips)
        player.chips -= actual
        player.current_bet += actual
        if player.chips == 0:
            player.all_in = True
        return actual

    def _make_state(
        self,
        community_cards: List[Card],
        pot: int,
        current_bet: int,
        stage: str,
        min_raise: int,
    ) -> GameState:
        return GameState(
            players=self.players,
            community_cards=community_cards,
            pot=pot,
            current_bet=current_bet,
            stage=stage,
            dealer_index=self.dealer_index,
            active_player_index=0,
            min_raise=min_raise,
        )

    def _betting_round(
        self,
        state: GameState,
        first_to_act: int,
        pot: int,
        current_bet: int,
        min_raise: int,
        community_cards: List[Card],
        stage: str,
    ) -> Tuple[int, int, int]:
        """Run a single betting round.  Returns updated (pot, current_bet, min_raise)."""
        n = len(self.players)
        # Track who has acted since the last raise
        last_raiser = -1
        acted: set[int] = set()

        idx = first_to_act
        while True:
            player = self.players[idx]

            if player.folded or player.all_in:
                idx = (idx + 1) % n
                # If we've gone all the way around with no one able to act, stop
                eligible = [
                    i
                    for i in range(n)
                    if not self.players[i].folded and not self.players[i].all_in
                ]
                if not eligible:
                    break
                if all(i in acted for i in eligible) and idx != last_raiser:
                    # Check if betting is closed (everyone has matched)
                    bets_matched = all(
                        self.players[i].current_bet == current_bet
                        or self.players[i].all_in
                        or self.players[i].folded
                        for i in range(n)
                    )
                    if bets_matched:
                        break
                continue

            still_in = [p for p in self.players if not p.folded]
            if len(still_in) <= 1:
                break

            state.active_player_index = idx
            state.pot = pot
            state.current_bet = current_bet
            state.min_raise = min_raise

            agent = self.agents[idx]
            player_state_dict = state.to_dict(player_index=idx)
            action, amount = agent.act(player_state_dict, idx)
            action = action.lower()

            call_amount = current_bet - player.current_bet

            if action == ACTION_FOLD:
                player.folded = True
                logger.info("%s folds", player.name)
            elif action == ACTION_CHECK:
                if call_amount > 0:
                    # Can't check when there's a bet; treat as call
                    action = ACTION_CALL
                else:
                    logger.info("%s checks", player.name)
            if action == ACTION_CALL:
                actual = min(call_amount, player.chips)
                player.chips -= actual
                player.current_bet += actual
                pot += actual
                if player.chips == 0:
                    player.all_in = True
                logger.info(
                    "%s calls %d (chips left: %d)", player.name, actual, player.chips
                )
            elif action == ACTION_RAISE:
                # amount = total chips player wants to put in this street
                raise_to = max(amount, current_bet + min_raise)
                raise_to = min(raise_to, player.chips + player.current_bet)
                added = raise_to - player.current_bet
                actual_added = min(added, player.chips)
                min_raise = max(min_raise, raise_to - current_bet)
                current_bet = raise_to
                player.chips -= actual_added
                player.current_bet += actual_added
                pot += actual_added
                if player.chips == 0:
                    player.all_in = True
                last_raiser = idx
                acted = {idx}  # reset: everyone else must act again
                logger.info(
                    "%s raises to %d (chips left: %d)",
                    player.name,
                    player.current_bet,
                    player.chips,
                )

            acted.add(idx)
            idx = (idx + 1) % n

            # End the round when everyone eligible has acted and bets match
            eligible = [
                i
                for i in range(n)
                if not self.players[i].folded and not self.players[i].all_in
            ]
            if not eligible:
                break
            bets_matched = all(
                self.players[i].current_bet == current_bet
                for i in eligible
            )
            if bets_matched and all(i in acted for i in eligible):
                break

        return pot, current_bet, min_raise

    def _showdown(
        self,
        players: List[PlayerState],
        community_cards: List[Card],
        pot: int,
    ) -> Optional[str]:
        """Evaluate hands, award the pot, return winner's name."""
        results = []
        for p in players:
            score, combo = best_hand(p.hand + community_cards)
            results.append((score, p, combo))
            logger.info(
                "%s shows %s → %s",
                p.name,
                [str(c) for c in p.hand],
                hand_name(score),
            )

        best_score = max(r[0] for r in results)
        winners = [r[1] for r in results if r[0] == best_score]

        share = pot // len(winners)
        remainder = pot % len(winners)
        for w in winners:
            w.chips += share
        # Give leftover chip to first winner
        winners[0].chips += remainder

        if len(winners) == 1:
            logger.info(
                "%s wins %d with %s",
                winners[0].name,
                pot,
                hand_name(best_score),
            )
            return winners[0].name
        else:
            logger.info(
                "Split pot (%d each) between %s with %s",
                share,
                [w.name for w in winners],
                hand_name(best_score),
            )
            return None

    def _advance_dealer(self) -> None:
        n = len(self.players)
        self.dealer_index = (self.dealer_index + 1) % n
