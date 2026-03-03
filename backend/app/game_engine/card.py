import random
from enum import Enum
from dataclasses import dataclass


class Suit(str, Enum):
    HEARTS = "hearts"
    DIAMONDS = "diamonds"
    CLUBS = "clubs"
    SPADES = "spades"


class Rank(int, Enum):
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14

    def __str__(self):
        names = {
            2: "2", 3: "3", 4: "4", 5: "5", 6: "6",
            7: "7", 8: "8", 9: "9", 10: "10",
            11: "J", 12: "Q", 13: "K", 14: "A"
        }
        return names[self.value]


@dataclass
class Card:
    suit: Suit
    rank: Rank

    def to_dict(self) -> dict:
        return {"suit": self.suit.value, "rank": self.rank.value, "display": str(self)}

    def __str__(self) -> str:
        suit_symbols = {
            Suit.HEARTS: "♥",
            Suit.DIAMONDS: "♦",
            Suit.CLUBS: "♣",
            Suit.SPADES: "♠",
        }
        return f"{self.rank}{suit_symbols[self.suit]}"

    def __repr__(self) -> str:
        return f"Card({self.rank}, {self.suit})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Card):
            return False
        return self.suit == other.suit and self.rank == other.rank

    def __hash__(self) -> int:
        return hash((self.suit, self.rank))


class Deck:
    def __init__(self):
        self._cards: list[Card] = [
            Card(suit=suit, rank=rank)
            for suit in Suit
            for rank in Rank
        ]
        self._dealt = 0

    def shuffle(self) -> None:
        random.shuffle(self._cards)
        self._dealt = 0

    def deal(self) -> Card:
        if self._dealt >= len(self._cards):
            raise ValueError("No cards remaining in deck")
        card = self._cards[self._dealt]
        self._dealt += 1
        return card

    @property
    def remaining(self) -> int:
        return len(self._cards) - self._dealt
