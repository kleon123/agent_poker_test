from itertools import combinations
from typing import List, Tuple, Dict, Optional
from .card import Card


HAND_NAMES = {
    0: "High Card",
    1: "One Pair",
    2: "Two Pair",
    3: "Three of a Kind",
    4: "Straight",
    5: "Flush",
    6: "Full House",
    7: "Four of a Kind",
    8: "Straight Flush",
}


class HandEvaluator:
    @staticmethod
    def evaluate(cards: List[Card]) -> Tuple[int, List[int], str]:
        """
        Evaluate best 5-card hand from up to 7 cards.
        Returns (hand_rank 0-8, tiebreaker_values, hand_name).
        Higher hand_rank = better hand. Tiebreaker_values are sorted descending for comparison.
        """
        if len(cards) < 5:
            raise ValueError(f"Need at least 5 cards, got {len(cards)}")

        best_rank = -1
        best_tiebreaker: List[int] = []
        best_name = ""

        for combo in combinations(cards, 5):
            rank, tiebreaker, name = HandEvaluator._evaluate_five(list(combo))
            if rank > best_rank or (rank == best_rank and tiebreaker > best_tiebreaker):
                best_rank = rank
                best_tiebreaker = tiebreaker
                best_name = name

        return best_rank, best_tiebreaker, best_name

    @staticmethod
    def _evaluate_five(cards: List[Card]) -> Tuple[int, List[int], str]:
        ranks = sorted([c.rank for c in cards], reverse=True)
        suits = [c.suit for c in cards]
        rank_counts: Dict[int, int] = {}
        for r in ranks:
            rank_counts[r] = rank_counts.get(r, 0) + 1

        is_flush = len(set(suits)) == 1
        is_straight, straight_high = HandEvaluator._check_straight(ranks)

        counts = sorted(rank_counts.values(), reverse=True)
        count_ranks = sorted(rank_counts.keys(), key=lambda r: (rank_counts[r], r), reverse=True)

        if is_straight and is_flush:
            return 8, [straight_high], HAND_NAMES[8]
        if counts[0] == 4:
            quad_rank = count_ranks[0]
            kicker = count_ranks[1]
            return 7, [quad_rank, kicker], HAND_NAMES[7]
        if counts[0] == 3 and counts[1] == 2:
            trip_rank = count_ranks[0]
            pair_rank = count_ranks[1]
            return 6, [trip_rank, pair_rank], HAND_NAMES[6]
        if is_flush:
            return 5, ranks, HAND_NAMES[5]
        if is_straight:
            return 4, [straight_high], HAND_NAMES[4]
        if counts[0] == 3:
            trip_rank = count_ranks[0]
            kickers = sorted([r for r in ranks if r != trip_rank], reverse=True)
            return 3, [trip_rank] + kickers, HAND_NAMES[3]
        if counts[0] == 2 and counts[1] == 2:
            pair1 = count_ranks[0]
            pair2 = count_ranks[1]
            kicker = count_ranks[2]
            return 2, [pair1, pair2, kicker], HAND_NAMES[2]
        if counts[0] == 2:
            pair_rank = count_ranks[0]
            kickers = sorted([r for r in ranks if r != pair_rank], reverse=True)
            return 1, [pair_rank] + kickers, HAND_NAMES[1]
        return 0, ranks, HAND_NAMES[0]

    @staticmethod
    def _check_straight(sorted_ranks: List[int]) -> Tuple[bool, int]:
        unique = sorted(set(sorted_ranks), reverse=True)
        if len(unique) < 5:
            return False, 0
        # Check normal straight
        for i in range(len(unique) - 4):
            window = unique[i:i + 5]
            if window[0] - window[4] == 4 and len(set(window)) == 5:
                return True, window[0]
        # Check wheel (A-2-3-4-5): A=14, use as 1
        if set([14, 2, 3, 4, 5]).issubset(set(sorted_ranks)):
            return True, 5
        return False, 0

    @staticmethod
    def compare_hands(hand1: Tuple[int, List[int]], hand2: Tuple[int, List[int]]) -> int:
        """
        Compare two evaluated hands.
        Returns 1 if hand1 wins, -1 if hand2 wins, 0 if tie.
        """
        rank1, tb1 = hand1
        rank2, tb2 = hand2
        if rank1 != rank2:
            return 1 if rank1 > rank2 else -1
        for v1, v2 in zip(tb1, tb2):
            if v1 != v2:
                return 1 if v1 > v2 else -1
        return 0

    @staticmethod
    def determine_winners(player_hands: Dict[str, List[Card]]) -> Tuple[List[str], Dict]:
        """
        Given a dict of player_id -> cards (hole + community), determine winners.
        Returns (list of winner ids, dict of player_id -> hand_info).
        """
        evaluations = {}
        for pid, cards in player_hands.items():
            rank, tiebreaker, name = HandEvaluator.evaluate(cards)
            evaluations[pid] = {
                "rank": rank,
                "tiebreaker": tiebreaker,
                "hand_name": name,
            }

        best_rank = max(e["rank"] for e in evaluations.values())
        candidates = {pid: e for pid, e in evaluations.items() if e["rank"] == best_rank}

        # Among candidates with same hand rank, find best tiebreaker
        best_tb = max(e["tiebreaker"] for e in candidates.values())
        winners = [pid for pid, e in candidates.items() if e["tiebreaker"] == best_tb]

        return winners, evaluations
