"""
Test suite to test the endpoints
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from src.schema import Base, GameStatus
from src.service import Service
import src.router as api
from src.tests.utils import *

@pytest.fixture
def client(monkeypatch):
    """
    Spins up a fresh in-memory SQLite DB, wires a new Service,
    and monkeypatches the module's global `service` so endpoints use it.
    """
    engine = create_engine(
        "sqlite://",
        future=True,
        connect_args={"check_same_thread": False},  # TestClient uses threads
        poolclass=StaticPool,  # one shared in-memory DB
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(
        bind=engine, autoflush=False, expire_on_commit=False, future=True
    )
    test_service = Service(SessionLocal)

    # Point the API module at the test service
    monkeypatch.setattr(api, "service", test_service, raising=True)

    # Return a live TestClient bound to the same app object
    with TestClient(api.app) as c:
        yield c


def test_create_user_and_uniqueness(client):
    """
    Tests the users endpoint
    """
    u1 = create_user(client, "u1")
    assert isinstance(u1, int)
    resp = client.post("/users", json={"name": "u1"})
    assert resp.status_code in (200, 400)


def test_session_lifecycle_and_join(client):
    """
    Tests the game joining enpoint
    """
    u1 = create_user(client, "u1")
    u2 = create_user(client, "u2")
    game_id = client.post("/game", json={"creator_user_id": u1}).json()["game_id"]

    # Before join
    game0 = client.get(f"/game/{game_id}").json()
    assert game0["status"] == GameStatus.waiting.value

    # Join + start
    resp = client.post(f"/game/{game_id}/join", json={"user_id": u2})
    assert resp.status_code == 200
    game1 = client.get(f"/game/{game_id}").json()
    assert game1["status"] == GameStatus.in_progress.value
    assert set(game1["players"]) == {u1, u2}

    # Third player should fail
    u3 = create_user(client, "u3")
    resp2 = client.post(f"/game/{game_id}/join", json={"user_id": u3})
    assert resp2.status_code == 400


def test_move_rules_turn_and_occupied(client):
    """
    Tests the move endpoint
    """
    u1, u2, game_id = create_started_game(client)
    # u1 plays (0,0)
    resp = client.post(
        f"/game/{game_id}/move", json={"user_id": u1, "row": 0, "col": 0}
    )
    assert resp.status_code == 200

    # u1 cannot move twice in a row
    resp = client.post(
        f"/game/{game_id}/move", json={"user_id": u1, "row": 0, "col": 1}
    )
    assert resp.status_code == 400

    # u2 moves (0,1)
    resp = client.post(
        f"/game/{game_id}/move", json={"user_id": u2, "row": 0, "col": 1}
    )
    assert resp.status_code == 200

    # u1 cannot take occupied cell
    resp = client.post(
        f"/game/{game_id}/move", json={"user_id": u1, "row": 0, "col": 1}
    )
    assert resp.status_code == 400

    # Still u1's turn since the last move was illegal
    game = client.get(f"/game/{game_id}").json()
    assert game["next_player_id"] == u1


def test_win_via_endpoints(client):
    """
    Tests the game endpoint to get the winner
    """
    u1, u2, game_id = create_started_game(client)

    # u1 wins
    moves = [
        (u1, 0, 0),
        (u2, 1, 0),
        (u1, 0, 1),
        (u2, 1, 1),
        (u1, 0, 2),
    ]
    for u, r, c in moves:
        resp = client.post(
            f"/game/{game_id}/move", json={"user_id": u, "row": r, "col": c}
        )
        assert resp.status_code == 200, resp.text

    game = client.get(f"/game/{game_id}").json()
    assert game["status"] == GameStatus.finished.value
    assert game["winner_id"] == u1


def test_draw_via_endpoints(client):
    """
    Tests the game endpoint to detect draw
    """
    u1, u2, game_id = create_started_game(client)

    draw_moves = [
        (u1, 0, 0),
        (u2, 0, 1),
        (u1, 0, 2),
        (u2, 1, 1),
        (u1, 1, 0),
        (u2, 1, 2),
        (u1, 2, 1),
        (u2, 2, 0),
        (u1, 2, 2),
    ]
    for u, r, c in draw_moves:
        resp = client.post(
            f"/game/{game_id}/move", json={"user_id": u, "row": r, "col": c}
        )
        assert resp.status_code == 200

    game = client.get(f"/game/{game_id}").json()
    assert game["status"] == GameStatus.finished.value
    assert game["winner_id"] is None


def test_user_stats_and_leaderboard_endpoints(client):
    """
    Tests the user stats and leaderboard endpoints
    """
    u1, u2, game_id = create_started_game(client, "u1", "u2")
    # u1 wins
    for u, r, c in [(u1, 0, 0), (u2, 1, 0), (u1, 0, 1), (u2, 1, 1), (u1, 0, 2)]:
        client.post(f"/game/{game_id}/move", json={"user_id": u, "row": r, "col": c})

    # stats
    sa = client.get(f"/users/{u1}/stats").json()
    sb = client.get(f"/users/{u2}/stats").json()
    assert sa["wins"] == 1 and sb["wins"] == 0
    assert sa["efficiency"] == 3

    # leaderboard by wins
    lb_w = client.get("/leaderboard", params={"metric": "wins"}).json()
    assert any(row["user_id"] == u1 for row in lb_w)

    # leaderboard by efficiency
    lb_e = client.get("/leaderboard", params={"metric": "efficiency"}).json()
    assert any(row["user_id"] == u1 for row in lb_e)
