"""An agent that always calls or checks (never folds, never raises)."""
from typing import Dict, Tuple

from ..agent import ACTION_CALL, ACTION_CHECK, BaseAgent


class CallAgent(BaseAgent):
    """Always calls when facing a bet, otherwise checks.

    This is the simplest possible non-folding strategy and serves as a
    useful baseline opponent.
    """

    def act(self, state: Dict, player_index: int) -> Tuple[str, int]:
        current_bet = state["current_bet"]
        my_bet = state["players"][player_index]["current_bet"]
        call_amount = current_bet - my_bet

        if call_amount == 0:
            return ACTION_CHECK, 0
        return ACTION_CALL, 0
