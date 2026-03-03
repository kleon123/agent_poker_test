import random

RANK_VALUES = {
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
    "T": 10,
    "J": 11,
    "Q": 12,
    "K": 13,
    "A": 14,
}
RANKS = list(RANK_VALUES.keys())
SUITS = ["h", "d", "c", "s"]  # hearts, diamonds, clubs, spades
SUIT_NAMES = {"h": "hearts", "d": "diamonds", "c": "clubs", "s": "spades"}


class Card:
    """Represents a single playing card."""

    def __init__(self, rank: str, suit: str) -> None:
        if rank not in RANK_VALUES:
            raise ValueError(f"Invalid rank: {rank!r}. Must be one of {RANKS}")
        if suit not in SUITS:
            raise ValueError(f"Invalid suit: {suit!r}. Must be one of {SUITS}")
        self.rank = rank
        self.suit = suit
        self.value: int = RANK_VALUES[rank]

    def __repr__(self) -> str:
        return f"{self.rank}{self.suit}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Card):
            return NotImplemented
        return self.rank == other.rank and self.suit == other.suit

    def __hash__(self) -> int:
        return hash((self.rank, self.suit))


class Deck:
    """A standard 52-card deck."""

    def __init__(self) -> None:
        self.cards = [Card(rank, suit) for rank in RANKS for suit in SUITS]
        self.shuffle()

    def shuffle(self) -> None:
        random.shuffle(self.cards)

    def deal(self) -> Card:
        if not self.cards:
            raise ValueError("Deck is empty")
        return self.cards.pop()

    def __len__(self) -> int:
        return len(self.cards)
