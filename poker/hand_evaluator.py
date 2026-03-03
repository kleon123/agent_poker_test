"""Hand evaluation for Texas Hold'em poker.

Hand ranks (low to high):
  0 - High Card
  1 - One Pair
  2 - Two Pair
  3 - Three of a Kind
  4 - Straight
  5 - Flush
  6 - Full House
  7 - Four of a Kind
  8 - Straight Flush (including Royal Flush)
"""
from itertools import combinations
from typing import List, Sequence, Tuple

from .card import Card

HAND_RANK_HIGH_CARD = 0
HAND_RANK_ONE_PAIR = 1
HAND_RANK_TWO_PAIR = 2
HAND_RANK_THREE_OF_A_KIND = 3
HAND_RANK_STRAIGHT = 4
HAND_RANK_FLUSH = 5
HAND_RANK_FULL_HOUSE = 6
HAND_RANK_FOUR_OF_A_KIND = 7
HAND_RANK_STRAIGHT_FLUSH = 8

_HAND_NAMES = {
    HAND_RANK_HIGH_CARD: "High Card",
    HAND_RANK_ONE_PAIR: "One Pair",
    HAND_RANK_TWO_PAIR: "Two Pair",
    HAND_RANK_THREE_OF_A_KIND: "Three of a Kind",
    HAND_RANK_STRAIGHT: "Straight",
    HAND_RANK_FLUSH: "Flush",
    HAND_RANK_FULL_HOUSE: "Full House",
    HAND_RANK_FOUR_OF_A_KIND: "Four of a Kind",
    HAND_RANK_STRAIGHT_FLUSH: "Straight Flush",
}

HandScore = Tuple[int, List[int]]


def evaluate_five_card_hand(cards: Sequence[Card]) -> HandScore:
    """Evaluate exactly 5 cards and return a comparable score tuple.

    The returned tuple is ``(hand_rank, [tiebreaker values...])`` where
    higher tuples beat lower tuples.
    """
    if len(cards) != 5:
        raise ValueError(f"Expected 5 cards, got {len(cards)}")

    values = sorted([c.value for c in cards], reverse=True)
    suits = [c.suit for c in cards]

    is_flush = len(set(suits)) == 1

    # Check for a normal straight (5 consecutive distinct values)
    is_straight = len(set(values)) == 5 and (values[0] - values[4] == 4)

    # Ace-low straight: A-2-3-4-5 ("wheel")
    if set(values) == {14, 2, 3, 4, 5}:
        is_straight = True
        values = [5, 4, 3, 2, 1]  # treat ace as low for comparison

    # Count occurrences of each value
    count_map: dict[int, int] = {}
    for v in values:
        count_map[v] = count_map.get(v, 0) + 1

    # Sort groups: primary by count (desc), secondary by card value (desc)
    groups = sorted(count_map.items(), key=lambda x: (x[1], x[0]), reverse=True)
    sorted_values = [g[0] for g in groups]
    count_values = [g[1] for g in groups]

    if is_straight and is_flush:
        return (HAND_RANK_STRAIGHT_FLUSH, values)
    if count_values[0] == 4:
        return (HAND_RANK_FOUR_OF_A_KIND, sorted_values)
    if count_values[0] == 3 and count_values[1] == 2:
        return (HAND_RANK_FULL_HOUSE, sorted_values)
    if is_flush:
        return (HAND_RANK_FLUSH, values)
    if is_straight:
        return (HAND_RANK_STRAIGHT, values)
    if count_values[0] == 3:
        return (HAND_RANK_THREE_OF_A_KIND, sorted_values)
    if count_values[0] == 2 and count_values[1] == 2:
        return (HAND_RANK_TWO_PAIR, sorted_values)
    if count_values[0] == 2:
        return (HAND_RANK_ONE_PAIR, sorted_values)
    return (HAND_RANK_HIGH_CARD, values)


def best_hand(cards: Sequence[Card]) -> Tuple[HandScore, Tuple[Card, ...]]:
    """Find the best 5-card hand from 5–7 cards.

    Returns ``(score, combo)`` where *score* is the hand score tuple and
    *combo* is the 5-card tuple that produced it.
    """
    if len(cards) < 5:
        raise ValueError(f"Need at least 5 cards, got {len(cards)}")

    best_score: HandScore = (-1, [])
    best_combo: Tuple[Card, ...] = ()
    for combo in combinations(cards, 5):
        score = evaluate_five_card_hand(list(combo))
        if score > best_score:
            best_score = score
            best_combo = combo
    return best_score, best_combo


def hand_name(score: HandScore) -> str:
    """Return a human-readable name for a hand score."""
    return _HAND_NAMES[score[0]]
