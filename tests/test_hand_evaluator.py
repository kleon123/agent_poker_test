"""Tests for the hand evaluator."""
import pytest

from poker.card import Card
from poker.hand_evaluator import (
    HAND_RANK_FLUSH,
    HAND_RANK_FOUR_OF_A_KIND,
    HAND_RANK_FULL_HOUSE,
    HAND_RANK_HIGH_CARD,
    HAND_RANK_ONE_PAIR,
    HAND_RANK_STRAIGHT,
    HAND_RANK_STRAIGHT_FLUSH,
    HAND_RANK_THREE_OF_A_KIND,
    HAND_RANK_TWO_PAIR,
    best_hand,
    evaluate_five_card_hand,
    hand_name,
)


def cards(*specs):
    """Create cards from 'Xs' notation, e.g. cards('Ah', 'Kd')."""
    return [Card(r, s) for r, s in specs]


class TestEvaluateFiveCardHand:
    def test_high_card(self):
        hand = cards(("A", "h"), ("K", "d"), ("J", "c"), ("9", "s"), ("7", "h"))
        score = evaluate_five_card_hand(hand)
        assert score[0] == HAND_RANK_HIGH_CARD

    def test_one_pair(self):
        hand = cards(("A", "h"), ("A", "d"), ("K", "c"), ("J", "s"), ("9", "h"))
        score = evaluate_five_card_hand(hand)
        assert score[0] == HAND_RANK_ONE_PAIR

    def test_two_pair(self):
        hand = cards(("A", "h"), ("A", "d"), ("K", "c"), ("K", "s"), ("9", "h"))
        score = evaluate_five_card_hand(hand)
        assert score[0] == HAND_RANK_TWO_PAIR

    def test_three_of_a_kind(self):
        hand = cards(("A", "h"), ("A", "d"), ("A", "c"), ("K", "s"), ("9", "h"))
        score = evaluate_five_card_hand(hand)
        assert score[0] == HAND_RANK_THREE_OF_A_KIND

    def test_straight(self):
        hand = cards(("5", "h"), ("6", "d"), ("7", "c"), ("8", "s"), ("9", "h"))
        score = evaluate_five_card_hand(hand)
        assert score[0] == HAND_RANK_STRAIGHT

    def test_ace_low_straight(self):
        hand = cards(("A", "h"), ("2", "d"), ("3", "c"), ("4", "s"), ("5", "h"))
        score = evaluate_five_card_hand(hand)
        assert score[0] == HAND_RANK_STRAIGHT

    def test_flush(self):
        hand = cards(("2", "h"), ("5", "h"), ("7", "h"), ("J", "h"), ("A", "h"))
        score = evaluate_five_card_hand(hand)
        assert score[0] == HAND_RANK_FLUSH

    def test_full_house(self):
        hand = cards(("A", "h"), ("A", "d"), ("A", "c"), ("K", "s"), ("K", "h"))
        score = evaluate_five_card_hand(hand)
        assert score[0] == HAND_RANK_FULL_HOUSE

    def test_four_of_a_kind(self):
        hand = cards(("A", "h"), ("A", "d"), ("A", "c"), ("A", "s"), ("K", "h"))
        score = evaluate_five_card_hand(hand)
        assert score[0] == HAND_RANK_FOUR_OF_A_KIND

    def test_straight_flush(self):
        hand = cards(("5", "h"), ("6", "h"), ("7", "h"), ("8", "h"), ("9", "h"))
        score = evaluate_five_card_hand(hand)
        assert score[0] == HAND_RANK_STRAIGHT_FLUSH

    def test_royal_flush_is_straight_flush(self):
        hand = cards(("T", "s"), ("J", "s"), ("Q", "s"), ("K", "s"), ("A", "s"))
        score = evaluate_five_card_hand(hand)
        assert score[0] == HAND_RANK_STRAIGHT_FLUSH

    def test_wrong_number_of_cards(self):
        with pytest.raises(ValueError):
            evaluate_five_card_hand(cards(("A", "h"), ("K", "d")))

    def test_straight_flush_beats_four_of_a_kind(self):
        sf = evaluate_five_card_hand(
            cards(("5", "h"), ("6", "h"), ("7", "h"), ("8", "h"), ("9", "h"))
        )
        quads = evaluate_five_card_hand(
            cards(("A", "h"), ("A", "d"), ("A", "c"), ("A", "s"), ("K", "h"))
        )
        assert sf > quads

    def test_higher_pair_beats_lower_pair(self):
        aces = evaluate_five_card_hand(
            cards(("A", "h"), ("A", "d"), ("K", "c"), ("J", "s"), ("9", "h"))
        )
        kings = evaluate_five_card_hand(
            cards(("K", "h"), ("K", "d"), ("A", "c"), ("J", "s"), ("9", "h"))
        )
        assert aces > kings


class TestBestHand:
    def test_best_from_seven(self):
        seven = cards(
            ("A", "h"), ("A", "d"), ("A", "c"), ("A", "s"),
            ("K", "h"), ("Q", "d"), ("J", "c"),
        )
        score, combo = best_hand(seven)
        assert score[0] == HAND_RANK_FOUR_OF_A_KIND

    def test_best_hand_picks_flush_over_pair(self):
        seven = cards(
            ("2", "h"), ("5", "h"), ("7", "h"), ("J", "h"), ("A", "h"),
            ("A", "d"), ("K", "c"),
        )
        score, combo = best_hand(seven)
        assert score[0] == HAND_RANK_FLUSH

    def test_too_few_cards(self):
        with pytest.raises(ValueError):
            best_hand(cards(("A", "h"), ("K", "d"), ("Q", "c"), ("J", "s")))


class TestHandName:
    def test_names(self):
        assert hand_name((HAND_RANK_HIGH_CARD, [])) == "High Card"
        assert hand_name((HAND_RANK_STRAIGHT_FLUSH, [])) == "Straight Flush"
        assert hand_name((HAND_RANK_FULL_HOUSE, [])) == "Full House"
