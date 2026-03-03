from dataclasses import dataclass
from enum import Enum
from itertools import combinations
from typing import List

from app.game_engine.card import Card, Rank, Suit


class HandRank(int, Enum):
    HIGH_CARD = 1
    ONE_PAIR = 2
    TWO_PAIR = 3
    THREE_OF_A_KIND = 4
    STRAIGHT = 5
    FLUSH = 6
    FULL_HOUSE = 7
    FOUR_OF_A_KIND = 8
    STRAIGHT_FLUSH = 9
    ROYAL_FLUSH = 10


@dataclass
class HandResult:
    rank: HandRank
    cards: List[Card]      # best 5-card hand
    description: str
    score: tuple           # tuple for tiebreaking comparisons


class HandEvaluator:
    @staticmethod
    def evaluate(cards: List[Card]) -> HandResult:
        """Evaluate best 5-card hand from 5-7 cards."""
        if len(cards) < 5:
            raise ValueError(f"Need at least 5 cards, got {len(cards)}")
        if len(cards) == 5:
            return HandEvaluator._evaluate_five(cards)
        best: HandResult | None = None
        for combo in combinations(cards, 5):
            result = HandEvaluator._evaluate_five(list(combo))
            if best is None or result.score > best.score:
                best = result
        return best  # type: ignore[return-value]

    @staticmethod
    def _evaluate_five(cards: List[Card]) -> HandResult:
        ranks = sorted([c.rank.value for c in cards], reverse=True)
        suits = [c.suit for c in cards]
        is_flush = len(set(suits)) == 1
        is_straight, straight_high = HandEvaluator._check_straight(ranks)

        rank_counts: dict[int, int] = {}
        for r in ranks:
            rank_counts[r] = rank_counts.get(r, 0) + 1
        counts = sorted(rank_counts.values(), reverse=True)
        count_ranks = sorted(rank_counts.keys(), key=lambda r: (rank_counts[r], r), reverse=True)

        if is_straight and is_flush:
            if straight_high == 14:
                return HandResult(
                    rank=HandRank.ROYAL_FLUSH,
                    cards=cards,
                    description="Royal Flush",
                    score=(HandRank.ROYAL_FLUSH, straight_high),
                )
            return HandResult(
                rank=HandRank.STRAIGHT_FLUSH,
                cards=cards,
                description=f"Straight Flush, {Rank(straight_high)}",
                score=(HandRank.STRAIGHT_FLUSH, straight_high),
            )

        if counts[0] == 4:
            quad_rank = count_ranks[0]
            kicker = count_ranks[1]
            return HandResult(
                rank=HandRank.FOUR_OF_A_KIND,
                cards=cards,
                description=f"Four of a Kind, {Rank(quad_rank)}s",
                score=(HandRank.FOUR_OF_A_KIND, quad_rank, kicker),
            )

        if counts[0] == 3 and counts[1] == 2:
            trip_rank = count_ranks[0]
            pair_rank = count_ranks[1]
            return HandResult(
                rank=HandRank.FULL_HOUSE,
                cards=cards,
                description=f"Full House, {Rank(trip_rank)}s over {Rank(pair_rank)}s",
                score=(HandRank.FULL_HOUSE, trip_rank, pair_rank),
            )

        if is_flush:
            return HandResult(
                rank=HandRank.FLUSH,
                cards=cards,
                description=f"Flush, {Rank(ranks[0])} high",
                score=(HandRank.FLUSH, *ranks),
            )

        if is_straight:
            return HandResult(
                rank=HandRank.STRAIGHT,
                cards=cards,
                description=f"Straight, {Rank(straight_high)} high",
                score=(HandRank.STRAIGHT, straight_high),
            )

        if counts[0] == 3:
            trip_rank = count_ranks[0]
            kickers = count_ranks[1:3]
            return HandResult(
                rank=HandRank.THREE_OF_A_KIND,
                cards=cards,
                description=f"Three of a Kind, {Rank(trip_rank)}s",
                score=(HandRank.THREE_OF_A_KIND, trip_rank, *kickers),
            )

        if counts[0] == 2 and counts[1] == 2:
            high_pair = count_ranks[0]
            low_pair = count_ranks[1]
            kicker = count_ranks[2]
            return HandResult(
                rank=HandRank.TWO_PAIR,
                cards=cards,
                description=f"Two Pair, {Rank(high_pair)}s and {Rank(low_pair)}s",
                score=(HandRank.TWO_PAIR, high_pair, low_pair, kicker),
            )

        if counts[0] == 2:
            pair_rank = count_ranks[0]
            kickers = count_ranks[1:4]
            return HandResult(
                rank=HandRank.ONE_PAIR,
                cards=cards,
                description=f"One Pair, {Rank(pair_rank)}s",
                score=(HandRank.ONE_PAIR, pair_rank, *kickers),
            )

        return HandResult(
            rank=HandRank.HIGH_CARD,
            cards=cards,
            description=f"High Card, {Rank(ranks[0])}",
            score=(HandRank.HIGH_CARD, *ranks),
        )

    @staticmethod
    def _check_straight(ranks: List[int]) -> tuple[bool, int]:
        unique = sorted(set(ranks), reverse=True)
        for i in range(len(unique) - 4):
            window = unique[i:i + 5]
            if window[0] - window[4] == 4 and len(window) == 5:
                return True, window[0]
        # Check wheel: A-2-3-4-5
        if set([14, 2, 3, 4, 5]).issubset(set(ranks)):
            return True, 5
        return False, 0

    @staticmethod
    def compare_hands(hand1: HandResult, hand2: HandResult) -> int:
        """Return -1 if hand1 < hand2, 0 if equal, 1 if hand1 > hand2."""
        if hand1.score > hand2.score:
            return 1
        if hand1.score < hand2.score:
            return -1
        return 0
