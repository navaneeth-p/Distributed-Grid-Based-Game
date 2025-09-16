"""
Module to simulate gameplay
"""

import random, secrets
import concurrent.futures
from typing import Tuple, Optional, Dict
from fastapi import HTTPException
from sqlalchemy import func, select
from src.router import service, init_db
from src.schema import GameStatus, SessionLocal, Player


def _play_game(user1: int, user2: int) -> Tuple[int, Optional[int]]:
    """
    Returns (game_id, winner_id) or game_id, None if game is tied
    """
    game_id = service.create_game(user1)
    print(f"Game id: {game_id} created by user: {user1}")
    service.join_game(game_id, user2)
    print(f"User: {user2} joined the game {game_id}")

    # Make random valid moves
    cells = [(row, col) for row in range(3) for col in range(3)]
    random.shuffle(cells)
    while True:
        game = service.get_game(game_id)
        if game.status != GameStatus.in_progress:
            print(f"Game {game_id} completed, winner: {game.winner_id}")
            return game_id, game.winner_id

        # Find a valid spot
        for row, col in list(cells):
            if game.board[row][col] is None:
                try:
                    service.move(
                        game_id=game_id, user_id=game.next_player_id, row=row, col=col
                    )
                    cells.remove((row, col))
                    break
                except HTTPException:
                    continue


def run_quick_sim(n_games: int = 10, n_users: int = 10) -> None:
    """
    Run a quick simulation for the number of games and users specified
    """
    init_db()
    user_ids = list()
    for i in range(n_users):
        try:
            # Adding a secrets_token so to not have to delete the db every run
            user = service.create_user(f"user-{i+1}_{secrets.token_hex(3)}")
            user_ids.append(user)
        except Exception as e:
            pass
    users = user_ids or [1, 2]

    pairs = [tuple(random.sample(users, 2)) for _ in range(n_games)]
    wins: Dict[int, int] = {}
    games: Dict[int, int] = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        futures = [ex.submit(_play_game, a, b) for a, b in pairs]
        for f in concurrent.futures.as_completed(futures):
            _, w = f.result()
            if w is not None:
                wins[w] = wins.get(w, 0) + 1

    # Count games per user
    with SessionLocal() as s:
        rows = s.execute(
            select(Player.user_id, func.count(Player.id)).group_by(Player.user_id)
        ).all()

        for user_id, cnt in rows:
            games[user_id] = cnt

    ratios = [(uid, wins.get(uid, 0) / games.get(uid, 1)) for uid in games]
    ratios.sort(key=lambda x: (-x[1], x[0]))
    top3 = ratios[:3]
    print("\nTop 3 ratios by win")
    for user_id, r in top3:
        print(
            f"User: {user_id}, Win ratio: {r:.3f} (wins={wins.get(user_id, 0)}, games={games.get(user_id, 0)})"
        )
