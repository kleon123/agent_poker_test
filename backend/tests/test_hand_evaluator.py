import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from app.game_engine.card import Card, Rank, Suit
from app.game_engine.hand_evaluator import HandEvaluator, HandRank


def make_card(rank: int, suit: str) -> Card:
    return Card(suit=Suit(suit), rank=Rank(rank))


def test_royal_flush():
    cards = [
        make_card(14, "hearts"),
        make_card(13, "hearts"),
        make_card(12, "hearts"),
        make_card(11, "hearts"),
        make_card(10, "hearts"),
    ]
    result = HandEvaluator.evaluate(cards)
    assert result.rank == HandRank.ROYAL_FLUSH


def test_straight_flush():
    cards = [
        make_card(9, "spades"),
        make_card(8, "spades"),
        make_card(7, "spades"),
        make_card(6, "spades"),
        make_card(5, "spades"),
    ]
    result = HandEvaluator.evaluate(cards)
    assert result.rank == HandRank.STRAIGHT_FLUSH


def test_four_of_a_kind():
    cards = [
        make_card(10, "hearts"),
        make_card(10, "diamonds"),
        make_card(10, "clubs"),
        make_card(10, "spades"),
        make_card(5, "hearts"),
    ]
    result = HandEvaluator.evaluate(cards)
    assert result.rank == HandRank.FOUR_OF_A_KIND


def test_full_house():
    cards = [
        make_card(7, "hearts"),
        make_card(7, "diamonds"),
        make_card(7, "clubs"),
        make_card(3, "spades"),
        make_card(3, "hearts"),
    ]
    result = HandEvaluator.evaluate(cards)
    assert result.rank == HandRank.FULL_HOUSE


def test_flush():
    cards = [
        make_card(2, "clubs"),
        make_card(5, "clubs"),
        make_card(7, "clubs"),
        make_card(9, "clubs"),
        make_card(11, "clubs"),
    ]
    result = HandEvaluator.evaluate(cards)
    assert result.rank == HandRank.FLUSH


def test_straight():
    cards = [
        make_card(9, "hearts"),
        make_card(8, "diamonds"),
        make_card(7, "clubs"),
        make_card(6, "spades"),
        make_card(5, "hearts"),
    ]
    result = HandEvaluator.evaluate(cards)
    assert result.rank == HandRank.STRAIGHT


def test_wheel_straight():
    """A-2-3-4-5 straight (wheel)."""
    cards = [
        make_card(14, "hearts"),
        make_card(2, "diamonds"),
        make_card(3, "clubs"),
        make_card(4, "spades"),
        make_card(5, "hearts"),
    ]
    result = HandEvaluator.evaluate(cards)
    assert result.rank == HandRank.STRAIGHT
    assert result.score[1] == 5  # high card of wheel is 5


def test_three_of_a_kind():
    cards = [
        make_card(6, "hearts"),
        make_card(6, "diamonds"),
        make_card(6, "clubs"),
        make_card(3, "spades"),
        make_card(9, "hearts"),
    ]
    result = HandEvaluator.evaluate(cards)
    assert result.rank == HandRank.THREE_OF_A_KIND


def test_two_pair():
    cards = [
        make_card(8, "hearts"),
        make_card(8, "diamonds"),
        make_card(4, "clubs"),
        make_card(4, "spades"),
        make_card(11, "hearts"),
    ]
    result = HandEvaluator.evaluate(cards)
    assert result.rank == HandRank.TWO_PAIR


def test_one_pair():
    cards = [
        make_card(3, "hearts"),
        make_card(3, "diamonds"),
        make_card(7, "clubs"),
        make_card(10, "spades"),
        make_card(14, "hearts"),
    ]
    result = HandEvaluator.evaluate(cards)
    assert result.rank == HandRank.ONE_PAIR


def test_high_card():
    cards = [
        make_card(2, "hearts"),
        make_card(5, "diamonds"),
        make_card(9, "clubs"),
        make_card(11, "spades"),
        make_card(13, "hearts"),
    ]
    result = HandEvaluator.evaluate(cards)
    assert result.rank == HandRank.HIGH_CARD


def test_seven_card_best_hand():
    """Test picking best 5 from 7 cards."""
    cards = [
        make_card(14, "hearts"),
        make_card(13, "hearts"),
        make_card(12, "hearts"),
        make_card(11, "hearts"),
        make_card(10, "hearts"),
        make_card(2, "clubs"),
        make_card(7, "diamonds"),
    ]
    result = HandEvaluator.evaluate(cards)
    assert result.rank == HandRank.ROYAL_FLUSH


def test_compare_hands_better():
    flush_cards = [
        make_card(2, "clubs"),
        make_card(5, "clubs"),
        make_card(7, "clubs"),
        make_card(9, "clubs"),
        make_card(11, "clubs"),
    ]
    pair_cards = [
        make_card(3, "hearts"),
        make_card(3, "diamonds"),
        make_card(7, "clubs"),
        make_card(10, "spades"),
        make_card(14, "hearts"),
    ]
    flush = HandEvaluator.evaluate(flush_cards)
    pair = HandEvaluator.evaluate(pair_cards)
    assert HandEvaluator.compare_hands(flush, pair) == 1
    assert HandEvaluator.compare_hands(pair, flush) == -1


def test_compare_hands_tie():
    cards1 = [
        make_card(14, "hearts"),
        make_card(13, "hearts"),
        make_card(12, "hearts"),
        make_card(11, "hearts"),
        make_card(10, "hearts"),
    ]
    cards2 = [
        make_card(14, "spades"),
        make_card(13, "spades"),
        make_card(12, "spades"),
        make_card(11, "spades"),
        make_card(10, "spades"),
    ]
    h1 = HandEvaluator.evaluate(cards1)
    h2 = HandEvaluator.evaluate(cards2)
    assert HandEvaluator.compare_hands(h1, h2) == 0
