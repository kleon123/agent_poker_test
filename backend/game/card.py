import random
from typing import List, Optional


SUITS = ["spades", "hearts", "diamonds", "clubs"]
SUIT_SYMBOLS = {"spades": "♠", "hearts": "♥", "diamonds": "♦", "clubs": "♣"}
RANK_NAMES = {
    2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8",
    9: "9", 10: "10", 11: "J", 12: "Q", 13: "K", 14: "A"
}


class Card:
    def __init__(self, rank: int, suit: str):
        if rank not in RANK_NAMES:
            raise ValueError(f"Invalid rank: {rank}")
        if suit not in SUITS:
            raise ValueError(f"Invalid suit: {suit}")
        self.rank = rank
        self.suit = suit

    def __str__(self) -> str:
        return f"{RANK_NAMES[self.rank]}{SUIT_SYMBOLS[self.suit]}"

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self, other) -> bool:
        if not isinstance(other, Card):
            return False
        return self.rank == other.rank and self.suit == other.suit

    def __lt__(self, other) -> bool:
        return self.rank < other.rank

    def __hash__(self):
        return hash((self.rank, self.suit))

    def to_dict(self) -> dict:
        return {
            "rank": self.rank,
            "suit": self.suit,
            "display": str(self),
            "rank_name": RANK_NAMES[self.rank],
            "suit_symbol": SUIT_SYMBOLS[self.suit],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Card":
        return cls(rank=data["rank"], suit=data["suit"])

    @property
    def is_red(self) -> bool:
        return self.suit in ("hearts", "diamonds")


class Deck:
    def __init__(self):
        self.cards: List[Card] = []
        self.reset()

    def reset(self):
        self.cards = [Card(rank, suit) for suit in SUITS for rank in RANK_NAMES]

    def shuffle(self):
        random.shuffle(self.cards)

    def deal(self, count: int = 1) -> List[Card]:
        if count > len(self.cards):
            raise ValueError(f"Not enough cards in deck (need {count}, have {len(self.cards)})")
        dealt = self.cards[:count]
        self.cards = self.cards[count:]
        return dealt

    def deal_one(self) -> Card:
        return self.deal(1)[0]

    def __len__(self) -> int:
        return len(self.cards)
