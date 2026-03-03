"""Base agent interface for Texas Hold'em poker."""
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict, Tuple

if TYPE_CHECKING:
    from .game import GameState

# Valid actions
ACTION_FOLD = "fold"
ACTION_CALL = "call"
ACTION_RAISE = "raise"
ACTION_CHECK = "check"

VALID_ACTIONS = {ACTION_FOLD, ACTION_CALL, ACTION_RAISE, ACTION_CHECK}


class BaseAgent(ABC):
    """Abstract base class for a poker-playing agent.

    Subclasses must implement :meth:`act`.
    """

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def act(self, state: Dict, player_index: int) -> Tuple[str, int]:
        """Decide what action to take.

        Parameters
        ----------
        state:
            A dictionary representation of the current game state (as
            returned by :meth:`~poker.game.GameState.to_dict`).  The
            agent's own hole cards are included under
            ``state['players'][player_index]['hand']``.
        player_index:
            Index of this agent's seat in ``state['players']``.

        Returns
        -------
        (action, amount):
            *action* is one of ``'fold'``, ``'call'``, ``'check'``,
            ``'raise'``.  *amount* is the **total** chips to put in for
            a raise (ignored for fold/call/check).
        """
