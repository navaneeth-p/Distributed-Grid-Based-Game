"""
Helpers for tests
"""


def create_two_players_and_start(session):
    """
    Helper to create two players and start a game
    """
    u1 = session.create_user("alice")
    u2 = session.create_user("bob")
    game_id = session.create_game(u1)
    session.join_game(game_id, u2)
    return u1, u2, game_id


def play_moves(session, game_id, seq):
    """
    Helper to make a move in the game
    """
    for u, r, c in seq:
        session.move(game_id, u, r, c)


def create_user(client, name: str) -> int:
    """
    Helper to create a user
    """
    resp = client.post("/users", json={"name": name})
    return resp.json()["user_id"]


def create_started_game(client, u1_name="alice", u2_name="bob"):
    """
    Helper to create an in-progess game
    """
    u1 = create_user(client, u1_name)
    u2 = create_user(client, u2_name)
    game = client.post("/game", json={"creator_user_id": u1}).json()["game_id"]
    resp = client.post(f"/game/{game}/join", json={"user_id": u2})
    return u1, u2, game
