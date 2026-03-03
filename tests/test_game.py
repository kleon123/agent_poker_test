"""Integration tests for TexasHoldemGame."""
import pytest

from poker.agents import CallAgent, RandomAgent
from poker.game import TexasHoldemGame


def make_game(n_players=3, chips=500, small_blind=10):
    agents = [CallAgent(f"Player{i}") for i in range(n_players)]
    return TexasHoldemGame(agents, starting_chips=chips, small_blind=small_blind)


class TestTexasHoldemGame:
    def test_requires_at_least_two_players(self):
        with pytest.raises(ValueError):
            TexasHoldemGame([CallAgent("Solo")], starting_chips=500)

    def test_play_hand_returns_winner_name(self):
        game = make_game()
        winner = game.play_hand()
        # Winner is a player name or None (split pot)
        player_names = {p.name for p in game.players}
        assert winner is None or winner in player_names

    def test_chips_conserved_after_hand(self):
        game = make_game(n_players=3, chips=1000)
        total_before = sum(p.chips for p in game.players)
        game.play_hand()
        total_after = sum(p.chips for p in game.players)
        assert total_before == total_after

    def test_chips_conserved_over_session(self):
        game = make_game(n_players=4, chips=500)
        total_before = sum(p.chips for p in game.players)
        game.play_session(num_hands=50)
        total_after = sum(p.chips for p in game.players)
        assert total_before == total_after

    def test_dealer_advances(self):
        game = make_game()
        assert game.dealer_index == 0
        game.play_hand()
        assert game.dealer_index == 1

    def test_play_session_returns_chip_counts(self):
        game = make_game(n_players=2, chips=200)
        result = game.play_session(num_hands=10)
        assert set(result.keys()) == {p.name for p in game.players}
        assert sum(result.values()) == 400  # 2 players × 200

    def test_random_agents_chips_conserved(self):
        agents = [
            RandomAgent("Alice"),
            RandomAgent("Bob"),
            CallAgent("Carol"),
        ]
        game = TexasHoldemGame(agents, starting_chips=300, small_blind=5)
        total_before = sum(p.chips for p in game.players)
        game.play_session(num_hands=30)
        total_after = sum(p.chips for p in game.players)
        assert total_before == total_after

    def test_heads_up_two_players(self):
        game = make_game(n_players=2, chips=100)
        total = sum(p.chips for p in game.players)
        for _ in range(20):
            active = [p for p in game.players if p.chips > 0]
            if len(active) < 2:
                break
            game.play_hand()
        assert sum(p.chips for p in game.players) == total
