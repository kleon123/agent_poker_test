"""An agent that chooses actions uniformly at random."""
import random
from typing import Dict, Tuple

from ..agent import ACTION_CALL, ACTION_CHECK, ACTION_FOLD, ACTION_RAISE, BaseAgent


class RandomAgent(BaseAgent):
    """Makes random legal decisions.

    Parameters
    ----------
    name:
        Display name for this agent.
    raise_fraction:
        Probability of raising when a raise is legal (default 0.2).
    fold_fraction:
        Probability of folding when facing a bet (default 0.2).
    """

    def __init__(
        self,
        name: str,
        raise_fraction: float = 0.2,
        fold_fraction: float = 0.2,
    ) -> None:
        super().__init__(name)
        self.raise_fraction = raise_fraction
        self.fold_fraction = fold_fraction

    def act(self, state: Dict, player_index: int) -> Tuple[str, int]:
        current_bet = state["current_bet"]
        my_bet = state["players"][player_index]["current_bet"]
        my_chips = state["players"][player_index]["chips"]
        min_raise = state["min_raise"]
        call_amount = current_bet - my_bet

        roll = random.random()

        if call_amount == 0:
            # No bet to call — check or raise
            if roll < self.raise_fraction and my_chips >= min_raise:
                raise_to = my_bet + min_raise + random.randint(0, min(50, my_chips - min_raise))
                return ACTION_RAISE, raise_to
            return ACTION_CHECK, 0
        else:
            # Facing a bet — fold, call, or raise
            if roll < self.fold_fraction:
                return ACTION_FOLD, 0
            if roll < self.fold_fraction + self.raise_fraction and my_chips >= current_bet - my_bet + min_raise:
                raise_to = current_bet + min_raise + random.randint(0, min(50, my_chips - (current_bet - my_bet + min_raise)))
                return ACTION_RAISE, raise_to
            return ACTION_CALL, 0
