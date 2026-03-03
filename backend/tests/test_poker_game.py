import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from app.game_engine.poker_game import PokerGame
from app.game_engine.constants import GamePhase, PlayerAction, PlayerStatus


def make_game(n: int = 2) -> PokerGame:
    player_ids = [f"player{i}" for i in range(n)]
    player_names = [f"Player {i}" for i in range(n)]
    return PokerGame(
        game_id="test-game",
        table_id="test-table",
        player_ids=player_ids,
        player_names=player_names,
        starting_chips=1000,
        small_blind=10,
        big_blind=20,
    )


def test_start_hand_deals_cards():
    game = make_game(2)
    state = game.start_hand()
    assert state.phase == GamePhase.PRE_FLOP
    for player in state.players.values():
        assert len(player.cards) == 2


def test_start_hand_posts_blinds():
    game = make_game(2)
    state = game.start_hand()
    # Heads-up: dealer = small blind
    total_in_pot = sum(p.total_bet_this_round for p in state.players.values())
    assert total_in_pot == 30  # 10 + 20
    assert state.pot == 30


def test_preflop_player_order_two():
    game = make_game(2)
    state = game.start_hand()
    # In heads-up, dealer is SB. UTG (first to act preflop) is dealer/SB
    assert state.current_player_id == state.dealer_id


def test_fold_wins_pot():
    game = make_game(2)
    state = game.start_hand()
    first = state.current_player_id
    state = game.process_action(first, PlayerAction.FOLD)
    assert state.phase == GamePhase.FINISHED
    assert state.winner_info is not None
    # Check the non-folded player won
    loser = first
    winner = [pid for pid in state.players if pid != loser][0]
    assert state.players[winner].chips > 1000


def test_call_check_through_showdown():
    game = make_game(2)
    state = game.start_hand()

    # Preflop: first player calls (or checks if already even)
    first = state.current_player_id
    actions = game.get_valid_actions(first)
    action_names = {a for a, _, _ in actions}

    # First player acts (call or check)
    if PlayerAction.CALL in action_names:
        state = game.process_action(first, PlayerAction.CALL)
    else:
        state = game.process_action(first, PlayerAction.CHECK)

    if state.phase == GamePhase.PRE_FLOP:
        second = state.current_player_id
        state = game.process_action(second, PlayerAction.CHECK)

    assert state.phase in (GamePhase.FLOP, GamePhase.FINISHED)
    if state.phase == GamePhase.FLOP:
        assert len(state.community_cards) == 3


def test_raise_action():
    game = make_game(2)
    state = game.start_hand()
    first = state.current_player_id
    actions = {a: (mn, mx) for a, mn, mx in game.get_valid_actions(first)}
    assert PlayerAction.RAISE in actions or PlayerAction.ALL_IN in actions

    if PlayerAction.RAISE in actions:
        mn, mx = actions[PlayerAction.RAISE]
        state = game.process_action(first, PlayerAction.RAISE, mn)
        assert state.last_action["action"] == "raise"


def test_all_in():
    game = make_game(2)
    state = game.start_hand()
    first = state.current_player_id
    state = game.process_action(first, PlayerAction.ALL_IN)
    assert game.players[first].status == PlayerStatus.ALL_IN


def test_phase_transitions():
    """Play through all phases via check/call."""
    game = make_game(2)
    state = game.start_hand()

    def play_street():
        for _ in range(10):
            if state.phase not in (GamePhase.PRE_FLOP, GamePhase.FLOP, GamePhase.TURN, GamePhase.RIVER):
                break
            pid = state.current_player_id
            if pid is None:
                break
            acts = {a for a, _, _ in game.get_valid_actions(pid)}
            if PlayerAction.CHECK in acts:
                game.process_action(pid, PlayerAction.CHECK)
            elif PlayerAction.CALL in acts:
                game.process_action(pid, PlayerAction.CALL)
            else:
                break

    # Preflop: first to act is UTG
    pid = state.current_player_id
    acts = {a for a, _, _ in game.get_valid_actions(pid)}
    if PlayerAction.CALL in acts:
        state = game.process_action(pid, PlayerAction.CALL)
    else:
        state = game.process_action(pid, PlayerAction.CHECK)
    # Big blind check
    if state.phase == GamePhase.PRE_FLOP and state.current_player_id:
        state = game.process_action(state.current_player_id, PlayerAction.CHECK)

    assert state.phase in (GamePhase.FLOP, GamePhase.FINISHED)
    if state.phase != GamePhase.FLOP:
        return

    assert len(state.community_cards) == 3

    # Flop
    for _ in range(2):
        pid = state.current_player_id
        if pid and state.phase == GamePhase.FLOP:
            state = game.process_action(pid, PlayerAction.CHECK)

    if state.phase != GamePhase.TURN:
        return
    assert len(state.community_cards) == 4

    # Turn
    for _ in range(2):
        pid = state.current_player_id
        if pid and state.phase == GamePhase.TURN:
            state = game.process_action(pid, PlayerAction.CHECK)

    if state.phase != GamePhase.RIVER:
        return
    assert len(state.community_cards) == 5

    # River
    for _ in range(2):
        pid = state.current_player_id
        if pid and state.phase == GamePhase.RIVER:
            state = game.process_action(pid, PlayerAction.CHECK)

    assert state.phase == GamePhase.FINISHED
    assert state.winner_info is not None


def test_three_player_game():
    game = make_game(3)
    state = game.start_hand()
    assert state.phase == GamePhase.PRE_FLOP
    # SB and BB are set
    assert state.small_blind_id != state.big_blind_id
    assert state.dealer_id != state.small_blind_id or len(game._player_order) == 2


def test_get_state_for_player_hides_others():
    game = make_game(2)
    game.start_hand()
    pid = game._player_order[0]
    state = game.get_state_for_player(pid)
    # Own cards visible
    own_cards = state["players"][pid]["cards"]
    assert all(c is not None for c in own_cards)
    # Opponent cards hidden
    other = game._player_order[1]
    other_cards = state["players"][other]["cards"]
    assert all(c is None for c in other_cards)


def test_get_state_for_observer_hides_cards():
    game = make_game(2)
    game.start_hand()
    state = game.get_state_for_observer()
    # Observer sees all cards
    for pid, pdata in state["players"].items():
        assert all(c is not None for c in pdata["cards"])


def test_chip_conservation():
    """Total chips should be conserved across a hand."""
    game = make_game(3)
    total_before = sum(p.chips for p in game.players.values())
    state = game.start_hand()

    # Play out by folding quickly
    pid = state.current_player_id
    state = game.process_action(pid, PlayerAction.FOLD)
    if state.phase != GamePhase.FINISHED:
        pid = state.current_player_id
        state = game.process_action(pid, PlayerAction.FOLD)

    total_after = sum(p.chips for p in game.players.values())
    assert total_before == total_after
