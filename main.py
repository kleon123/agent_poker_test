"""Example: run a Texas Hold'em session between sample agents."""
import logging

from poker.agents import CallAgent, RandomAgent
from poker.game import TexasHoldemGame

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)


def main() -> None:
    agents = [
        RandomAgent("Alice", raise_fraction=0.25, fold_fraction=0.15),
        RandomAgent("Bob", raise_fraction=0.15, fold_fraction=0.25),
        CallAgent("Carol"),
    ]

    game = TexasHoldemGame(agents, starting_chips=1000, small_blind=10)

    print("Starting Texas Hold'em — 20 hands\n")
    final_chips = game.play_session(num_hands=20)

    print("\n=== Final chip counts ===")
    for name, chips in sorted(final_chips.items(), key=lambda x: -x[1]):
        print(f"  {name}: {chips}")


if __name__ == "__main__":
    main()
