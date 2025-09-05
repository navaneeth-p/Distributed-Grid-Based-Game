"""
Various supporting models
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional

from src.schema import GameStatus


class APIModel(BaseModel):
    model_config = ConfigDict(use_enum_values=True)


class CreateUserRequest(BaseModel):
    name: str = Field(min_length=1, max_length=64)


class CreateGameRequest(BaseModel):
    creator_user_id: int


class JoinGameRequest(BaseModel):
    user_id: int


class MoveRequest(BaseModel):
    user_id: int
    row: int = Field(ge=0, le=2)
    col: int = Field(ge=0, le=2)


class ViewGame(APIModel):
    id: int
    status: GameStatus
    board: List[List[Optional[int]]]
    next_player_id: Optional[int]
    players: List[int]
    winner_id: Optional[int]


class LeaderBoard(BaseModel):
    user_id: int
    value: float  # Win count or efficiency
    wins: int
    games: int


class UserStats(BaseModel):
    user_id: int
    games: int
    wins: int
    loses: int
    draws: int
    win_ratio: float
    efficiency: Optional[float]  # Avg moves per win
