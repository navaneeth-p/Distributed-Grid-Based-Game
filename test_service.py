"""
Base test file
"""

import pytest
import concurrent.futures
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
import threading
from fastapi import HTTPException

from src.schema import Base
from src.service import Service
from src.schema import GameStatus
from src.tests.utils import *


@pytest.fixture
def session():
    """
    Method to create the test session
    """
    engine = create_engine(
        "sqlite://",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_local = sessionmaker(
        bind=engine, autoflush=True, expire_on_commit=False, future=True
    )
    yield Service(session_local)
    Base.metadata.drop_all(engine)


def test_create_user_uniqueness(session):
    """
    Tests create user and uniqeness functionality
    """
    user_id1 = session.create_user("user1")
    assert isinstance(user_id1, int)


def test_game_join_and_start(session):
    """
    Tests joining game and game start functionality
    """
    u1 = session.create_user("u1")
    u2 = session.create_user("u2")
    game_id = session.create_game(u1)

    # Game not started
    g0 = session.get_game(game_id)
    assert g0.status == GameStatus.waiting

    # Game started
    session.join_game(game_id, u2)
    game1 = session.get_game(game_id)
    assert game1.status == GameStatus.in_progress
    assert set(game1.players) == {u1, u2}

    # Third player cannot join
    u3 = session.create_user("u3")
    with pytest.raises(Exception) as e:
        session.join_game(game_id, u3)
    assert getattr(e.value, "status_code", None) == 400


def test_turn_enforced_and_cell_occupied(session):
    """
    Tests turn based gamepplay enforcement and cell blockiing
    """
    u1, u2, game_id = create_two_players_and_start(session)

    session.move(game_id, u1, 0, 0)

    # Assert u1 cannot go again
    with pytest.raises(Exception) as e:
        session.move(game_id, u1, 0, 1)
    assert getattr(e.value, "status_code", None) == 400

    session.move(game_id, u2, 0, 1)

    # Assert u1 cannot take occupied cell
    with pytest.raises(Exception) as e2:
        session.move(game_id, u1, 0, 1)
    assert getattr(e2.value, "status_code", None) == 400

    # u1 still gets to move since last move was invalid
    game = session.get_game(game_id)
    assert game.next_player_id == u1


def test_win_detection(session):
    """
    Tests win detection during a game
    """
    u1, u2, game_id = create_two_players_and_start(session)

    # u1 wins
    play_moves(
        session,
        game_id,
        [
            (u1, 0, 0),
            (u2, 1, 0),
            (u1, 0, 1),
            (u2, 1, 1),
            (u1, 0, 2),
        ],
    )

    game = session.get_game(game_id)
    assert game.status == GameStatus.finished
    assert game.winner_id == u1


def test_draw_detection(session):
    """
    Tests draw detection during a game
    """
    u1, u2, game_id = create_two_players_and_start(session)

    # Game draws
    play_moves(
        session,
        game_id,
        [
            (u1, 0, 0),
            (u2, 0, 1),
            (u1, 0, 2),
            (u2, 1, 1),
            (u1, 1, 0),
            (u2, 1, 2),
            (u1, 2, 1),
            (u2, 2, 0),
            (u1, 2, 2),
        ],
    )
    game = session.get_game(game_id)
    assert game.status == GameStatus.finished
    assert game.winner_id == None


def test_no_moves_after_game_end(session):
    """
    Tests no moves are allowed once the game ends
    """
    u1, u2, game_id = create_two_players_and_start(session)

    # Game draws
    play_moves(
        session,
        game_id,
        [
            (u1, 0, 0),
            (u2, 1, 0),
            (u1, 0, 1),
            (u2, 1, 1),
            (u1, 0, 2),
        ],
    )
    assert session.get_game(game_id).status == GameStatus.finished
    # No further moves allowed
    with pytest.raises(Exception) as e:
        session.move(game_id, u2, 2, 2)
    assert getattr(e.value, "status_code", None) == 400


def test_concurrency(session):
    """
    Tests concurrency and atomicity for play
    """
    u1, u2, game_id = create_two_players_and_start(session)

    # Two threads both try to submit the SAME move for 'u1' on turn 1
    barrier = threading.Barrier(2)
    def work():
        barrier.wait() 
        try:
            session.move(game_id, u1, 0, 0)
            return "ok"
        except HTTPException as e:
            return e.status_code
        except Exception as e:
            return getattr(e, "status_code", None)

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        results = list(ex.map(lambda _: work(), range(2)))

    # Exactly one ok, one 400
    assert results.count("ok") == 1
    assert results.count(400) == 1

    # Game should proceed with u2's turn
    game = session.get_game(game_id)
    assert game.board[0][0] == u1
    assert game.next_player_id == u2


def test_user_stats_and_win_ratio(session):
    """
    Tests getting user stats and win ratio
    """
    u1, u2, game_id1 = create_two_players_and_start(session)
    # u1 wins
    play_moves(
        session,
        game_id1,
        [
            (u1, 0, 0),
            (u2, 1, 0),
            (u1, 0, 1),
            (u2, 1, 1),
            (u1, 0, 2),
        ],
    )
    # new game: draw
    game_id2 = session.create_game(u1)
    session.join_game(game_id2, u2)
    play_moves(
        session,
        game_id2,
        [
            (u1, 0, 0),
            (u2, 0, 1),
            (u1, 0, 2),
            (u2, 1, 1),
            (u1, 1, 0),
            (u2, 1, 2),
            (u1, 2, 1),
            (u2, 2, 0),
            (u1, 2, 2),
        ],
    )

    su1 = session.get_user_stats(u1)
    su2 = session.get_user_stats(u2)

    assert su1.games == 2 and su2.games == 2
    assert su1.wins == 1 and su2.wins == 0
    assert su1.draws == 1 and su2.draws == 1
    assert su1.loses == 0 and su2.loses == 1
    assert 0.49 < su1.win_ratio < 0.51  # 1/2
    assert su1.efficiency == 3  # u1 won with 3 of u1's moves


def test_leaderboard_wins_and_efficiency(session):
    """
    Tests leaderboard and efficiency compuations
    """
    # Players: u1, u2, u3
    u1 = session.create_user("u1")
    u2 = session.create_user("u2")
    u3 = session.create_user("u3")

    # Game 1: u1 vs u2 -> u1 wins
    game1 = session.create_game(u1)
    session.join_game(game1, u2)
    play_moves(
        session, game1, [(u1, 0, 0), (u2, 1, 0), (u1, 0, 1), (u2, 1, 1), (u1, 0, 2)]
    )

    # Game 2: u2 vs u3 -> u2 wins
    game2 = session.create_game(u3)
    session.join_game(game2, u2)
    play_moves(
        session,
        game2,
        [(u3, 0, 0), (u2, 1, 0), (u3, 0, 2), (u2, 1, 1), (u3, 2, 2), (u2, 1, 2)],
    )

    # Game 3: u1 vs u3 -> draw
    game3 = session.create_game(u1)
    session.join_game(game3, u3)
    play_moves(
        session,
        game3,
        [
            (u1, 0, 0),
            (u3, 0, 1),
            (u1, 0, 2),
            (u3, 1, 1),
            (u1, 1, 0),
            (u3, 1, 2),
            (u1, 2, 1),
            (u3, 2, 0),
            (u1, 2, 2),
        ],
    )

    # Wins leaderboard: u1 and u2 both with 1; tie-break by user_id ascending
    lb_w = session.leaderboard("wins")
    assert lb_w[0].wins >= lb_w[1].wins
    assert set(x.user_id for x in lb_w) >= {u1, u2}

    # Efficiency: u1 should beat u2
    lb_e = session.leaderboard("efficiency")
    ids = [row.user_id for row in lb_e]
    assert u1 in ids and u2 in ids
    # u1 should appear before u2
    assert ids.index(u1) < ids.index(u2)
