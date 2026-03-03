"""Tests for Card and Deck classes."""
import pytest

from poker.card import Card, Deck, RANK_VALUES, RANKS, SUITS


class TestCard:
    def test_valid_card(self):
        c = Card("A", "s")
        assert c.rank == "A"
        assert c.suit == "s"
        assert c.value == 14

    def test_repr(self):
        assert repr(Card("K", "h")) == "Kh"

    def test_equality(self):
        assert Card("5", "d") == Card("5", "d")
        assert Card("5", "d") != Card("5", "h")

    def test_hash(self):
        s = {Card("2", "c"), Card("2", "c"), Card("3", "h")}
        assert len(s) == 2

    def test_invalid_rank(self):
        with pytest.raises(ValueError):
            Card("X", "s")

    def test_invalid_suit(self):
        with pytest.raises(ValueError):
            Card("A", "x")

    def test_all_values(self):
        assert RANK_VALUES["2"] == 2
        assert RANK_VALUES["T"] == 10
        assert RANK_VALUES["A"] == 14


class TestDeck:
    def test_deck_size(self):
        d = Deck()
        assert len(d) == 52

    def test_deal_reduces_size(self):
        d = Deck()
        d.deal()
        assert len(d) == 51

    def test_deal_all_cards(self):
        d = Deck()
        cards = [d.deal() for _ in range(52)]
        assert len(cards) == 52
        # All unique
        assert len(set(cards)) == 52

    def test_empty_deck_raises(self):
        d = Deck()
        for _ in range(52):
            d.deal()
        with pytest.raises(ValueError):
            d.deal()

    def test_deck_covers_all_ranks_and_suits(self):
        d = Deck()
        cards = [d.deal() for _ in range(52)]
        ranks_found = {c.rank for c in cards}
        suits_found = {c.suit for c in cards}
        assert ranks_found == set(RANKS)
        assert suits_found == set(SUITS)
