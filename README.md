# agent_poker_test

Texas Hold'em poker engine for AI agents.

## Overview

This library provides a full Texas Hold'em game engine that agents can plug into.  It handles:

- Card/deck management
- Preflop → flop → turn → river betting rounds (with blinds, raises, all-ins)
- Hand evaluation (High Card through Straight Flush / Royal Flush)
- Showdown with pot splitting on ties

## Project structure

```
poker/
  card.py            # Card and Deck
  hand_evaluator.py  # Evaluate & compare poker hands
  game.py            # TexasHoldemGame engine
  agent.py           # BaseAgent abstract class
  agents/
    call_agent.py    # Always calls/checks
    random_agent.py  # Random legal actions
tests/
  test_card.py
  test_hand_evaluator.py
  test_game.py
main.py              # Example session
```

## Quick start

```bash
pip install -r requirements.txt
python main.py
```

## Writing your own agent

Subclass `BaseAgent` and implement `act`:

```python
from poker.agent import BaseAgent, ACTION_FOLD, ACTION_CALL, ACTION_RAISE, ACTION_CHECK

class MyAgent(BaseAgent):
    def act(self, state: dict, player_index: int):
        # state keys: community_cards, pot, current_bet, stage,
        #             min_raise, players, active_player_index
        # state['players'][player_index]['hand'] contains your hole cards
        current_bet = state['current_bet']
        my_bet = state['players'][player_index]['current_bet']
        if current_bet == my_bet:
            return ACTION_CHECK, 0
        return ACTION_CALL, 0
```

Then pass your agent to the game:

```python
from poker.game import TexasHoldemGame

game = TexasHoldemGame([MyAgent("Bot1"), MyAgent("Bot2")], starting_chips=1000)
results = game.play_session(num_hands=100)
print(results)
```

## Running tests

```bash
python -m pytest tests/ -v
```

## Card notation

Cards are represented as a rank character followed by a suit character:

| Rank | Meaning  | Suit | Meaning  |
|------|----------|------|----------|
| 2–9  | 2–9      | h    | hearts   |
| T    | 10       | d    | diamonds |
| J    | Jack     | c    | clubs    |
| Q    | Queen    | s    | spades   |
| K    | King     |      |          |
| A    | Ace      |      |          |

Example: `Ah` = Ace of hearts, `Tc` = Ten of clubs.
