"""
Module that lists the APIs
"""

from fastapi import FastAPI, HTTPException
from typing import Dict, List
from src.schema import init_db, SessionLocal
from src.service import Service
from src.models import (
    CreateGameRequest,
    CreateUserRequest,
    JoinGameRequest,
    MoveRequest,
    ViewGame,
    LeaderBoard,
    UserStats,
)


init_db()
service = Service(SessionLocal)
app = FastAPI(title="Distributed Grid Game Engine")


@app.post("/users")
def create_user(request: CreateUserRequest) -> Dict[str, int]:
    """
    Endpoint to create user
    """
    try:
        user_id = service.create_user(request.name)
        return {"user_id": user_id}
    except Exception as e:
        raise HTTPException(400, f"Couldn't create user: {e}")


@app.post("/game")
def create_game(request: CreateGameRequest) -> Dict[str, int]:
    """
    Endpoint to create a game
    """
    try:
        game_id = service.create_game(request.creator_user_id)
        return {"game_id": game_id}
    except Exception as e:
        raise HTTPException(400, f"Couldn't create game: {e}")


@app.post("/game/{game_id}/join")
def join_game(game_id: int, request: JoinGameRequest) -> Dict[str, str]:
    """
    Endoint to join a game
    """
    try:
        service.join_game(game_id=game_id, user_id=request.user_id)
        return {"status": "Joined game"}
    except Exception as e:
        raise HTTPException(400, f"Couldn't create user: {e}")


@app.post("/game/{game_id}/move")
def move(game_id: int, request: MoveRequest):
    """
    Endpoint to make a move
    """
    return service.move(
        game_id=game_id, user_id=request.user_id, row=request.row, col=request.col
    )


@app.get("/game/{game_id}")
def get_game(game_id: int) -> ViewGame:
    """
    Endpoint to view a game
    """
    return service.get_game(game_id)


@app.get("/leaderboard")
def leaderboard(metric: str) -> List[LeaderBoard] | str:
    """
    Endpoint to view the leaderboard
    """
    return service.leaderboard(metric)


@app.get("/users/{user_id}/stats")
def get_user_stats(user_id: int) -> UserStats:
    """
    Endpoint to get user stats
    """
    return service.get_user_stats(user_id)
