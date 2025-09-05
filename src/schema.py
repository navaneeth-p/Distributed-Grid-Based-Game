"""
The database schema for the game
"""

from datetime import datetime, timezone
from enum import Enum
import os
from typing import Optional, List
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    sessionmaker,
)

from sqlalchemy import (
    create_engine,
    String,
    Integer,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Enum as SAEnum,
)


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./game.db")

engine = create_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine, autoflush=False, expire_on_commit=False, future=True
)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64))


class GameStatus(str, Enum):
    waiting = "waiting"
    in_progress = "in_progress"
    finished = "finished"


class Game(Base):
    __tablename__ = "games"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    status: Mapped[GameStatus] = mapped_column(SAEnum(GameStatus), default=GameStatus.waiting)  # type: ignore[arg-type]
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now(timezone.utc)
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now(timezone.utc)
    )
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now(timezone.utc)
    )
    winner_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    turn_no: Mapped[int] = mapped_column(Integer, default=0)
    players: Mapped[List["Player"]] = relationship(
        back_populates="game", cascade="all, delete-orphan"
    )
    moves: Mapped[List["Move"]] = relationship(
        back_populates="game", cascade="all, delete-orphan"
    )


class Player(Base):
    __tablename__ = "players"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    player_order: Mapped[int] = mapped_column(Integer)
    game: Mapped[Game] = relationship(back_populates="players")
    user: Mapped[User] = relationship()

    __table_args__ = (
        UniqueConstraint("game_id", "player_order", name="unique_game_player_slot"),
        UniqueConstraint("game_id", "user_id", name="unique_game_user"),
    )


class Move(Base):
    __tablename__ = "moves"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    row: Mapped[int] = mapped_column(Integer)
    col: Mapped[int] = mapped_column(Integer)
    move_no: Mapped[int] = mapped_column(Integer)
    performed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now(timezone.utc)
    )
    game: Mapped[Game] = relationship(back_populates="moves")
    user: Mapped[User] = relationship()

    __table_args__ = (
        UniqueConstraint("game_id", "row", "col", name="unique_cell"),
        UniqueConstraint("game_id", "move_no", name="unique_move_number"),
    )


def init_db():
    Base.metadata.create_all(engine)
