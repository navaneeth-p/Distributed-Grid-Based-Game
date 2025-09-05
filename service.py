"""
Service layer module
"""

from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session
from typing import List
from src.schema import Game, Player, GameStatus, Move, User
from src.models import LeaderBoard, ViewGame, UserStats
from src.utils import construct_board, find_winner, next_player, players_in_order


class Service:
    def __init__(self, session_factory) -> None:
        """
        Init session
        """
        self._sf = session_factory

    def create_user(self, name: str) -> int:
        """
        Method to create a user
        """
        with self._sf() as s, s.begin():
            u = User(name=name)
            s.add(u)
            s.flush()
            return u.id

    def create_game(self, creator_user_id: int) -> int:
        """
        Method to create a game
        """
        with self._sf() as s, s.begin():
            # Validate user
            if not s.get(User, creator_user_id):
                raise HTTPException(404, "User not found")
            game = Game(status=GameStatus.waiting)
            s.add(game)
            s.flush()
            player = Player(game_id=game.id, user_id=creator_user_id, player_order=0)
            s.add(player)
            return game.id

    def get_game_view(self, s: Session, game_id: int) -> ViewGame:
        """
        Method to get the view/state of a game
        """
        game = s.get(Game, game_id)
        if not game:
            raise HTTPException(404, "Game not Found")
        moves: List[Move] = list(
            s.execute(
                select(Move).where(Move.game_id == game.id).order_by(Move.move_no)
            )
            .scalars()
            .all()
        )

        board = construct_board(moves)
        players = [p for p in players_in_order(game) if p is not None]

        return ViewGame(
            id=game.id,
            status=game.status,
            board=board,
            next_player_id=next_player(game),
            players=players,
            winner_id=game.winner_id,
        )

    def get_game(self, game_id: int) -> ViewGame:
        """
        Abstracts get_game_view
        """
        with self._sf() as s:
            return self.get_game_view(s, game_id)

    def join_game(self, game_id: int, user_id: int) -> None:
        """
        Method to join a game
        """
        with self._sf() as s, s.begin():
            game = s.get(Game, game_id)
            if not game:
                raise HTTPException(404, "Game not found")
            if game.status != GameStatus.waiting:
                raise HTTPException(400, "Cannot join: Game has started")
            if not s.get(User, user_id):
                raise HTTPException(404, "User not found")

            # Prevent exisitng players from joining the game again
            existing_players = {player.id for player in game.players}
            if user_id in existing_players:
                raise HTTPException(400, "User already in game")

            if len(game.players) >= 2:
                raise HTTPException(400, "A game can only have up to 2 players")

            order = 0
            for player in game.players:
                if player.player_order == 0:
                    order = 1
                    break
            s.add(
                Player(
                    game_id=game.id,
                    user_id=user_id,
                    player_order=order,
                )
            )
            s.flush()

            # Set game to in-progress if 2 players joined
            if len(game.players) + 1 == 2:
                game.status = GameStatus.in_progress
                game.started_at = datetime.now(timezone.utc)

    def move(self, game_id: int, user_id: int | None, row: int, col: int) -> ViewGame:
        """
        Method to make a move
        """
        with self._sf() as s, s.begin():
            game = s.get(Game, game_id, with_for_update=False)
            if not game:
                raise HTTPException(404, "Game not found")
            if game.status != GameStatus.in_progress:
                raise HTTPException(400, "Game not in progress")
            if not any(player.user_id == user_id for player in game.players):
                raise HTTPException(400, "User not in this game")

            expected_turn = game.turn_no
            order = expected_turn % 2
            order_to_user = {
                player.player_order: player.user_id for player in game.players
            }
            if order_to_user.get(order) != user_id:
                raise HTTPException(400, "Not your turn")

            # Validate the cell is empty
            upd = (
                update(Game)
                .where(Game.id == game_id, Game.turn_no == expected_turn)
                .values(turn_no=Game.turn_no + 1)
            )

            result = s.execute(upd)
            if result.rowcount != 1:
                raise HTTPException(400, "Concurrent moves, try again")

            move_no = expected_turn + 1

            cell_occupied = s.execute(
                select(Move.id).where(
                    Move.game_id == game.id, Move.row == row, Move.col == col
                )
            ).first()

            if cell_occupied:
                # Move not permitted, revert turn number back to executed turn
                s.execute(
                    update(Game)
                    .where(Game.id == game_id, Game.turn_no == expected_turn)
                    .values(turn_no=expected_turn)
                )
                raise HTTPException(400, "Cell already occupied")

            move = Move(
                game_id=game_id, user_id=user_id, move_no=move_no, row=row, col=col
            )
            s.add(move)
            s.flush()

            # Update board
            all_moves = (
                s.execute(
                    select(Move).where(Move.game_id == game.id).order_by(Move.move_no)
                )
                .scalars()
                .all()
            )

            board = construct_board(all_moves)

            # Check for winner or draw
            winner = find_winner(board)

            if winner is not None:
                game.status = GameStatus.finished
                game.winner_id = winner
                game.completed_at = datetime.now(timezone.utc)

            elif game.turn_no >= 9:
                game.status = GameStatus.finished  # Rename to completed
                game.completed_at = datetime.now(timezone.utc)

            s.flush()
            return self.get_game_view(s, game.id)

    def get_user_stats(self, user_id: int) -> UserStats:
        """
        Method to get user stats
        """
        with self._sf() as s:

            games_played = s.execute(
                select(func.count(Player.id)).where(Player.user_id == user_id)
            ).scalar_one()

            wins = s.execute(
                select(func.count(Game.id)).where(Game.winner_id == user_id)
            ).scalar_one()

            draw_games = (
                s.execute(
                    select(Game.id)
                    .join(Player, Player.game_id == Game.id)
                    .where(
                        Game.status == GameStatus.finished,
                        Game.winner_id.is_(None),
                        Player.user_id == user_id,
                    )
                )
                .scalars()
                .all()
            )
            draws = len(draw_games)

            loses = games_played - wins - draws

            win_ratio = (wins / games_played) if games_played else 0.0

            moves = s.execute(
                select(Move.game_id, func.count(Move.id))
                .join(Game, Game.id == Move.game_id)
                .where(Game.winner_id == user_id, Move.user_id == user_id)
                .group_by(Move.game_id)
            ).all()
            efficiency = (sum(c for _, c in moves) / len(moves)) if moves else None

            return UserStats(
                user_id=user_id,
                games=games_played,
                wins=wins,
                loses=loses,
                draws=draws,
                win_ratio=win_ratio,
                efficiency=efficiency,
            )

    def leaderboard(self, metric: str) -> List[LeaderBoard] | str:
        """
        Method to view the leaderboard
        """
        with self._sf() as s:
            total_games_by_user = dict(
                s.execute(
                    select(Player.user_id, func.count(Player.id)).group_by(
                        Player.user_id
                    )
                ).all()
            )

            wins_by_user = dict(
                s.execute(
                    select(Game.winner_id, func.count(Game.id))
                    .where(Game.winner_id.is_not(None))
                    .group_by(Game.winner_id)
                ).all()
            )
            per_game_moves = (
                select(
                    Move.user_id.label("uid"),
                    Move.game_id.label("gid"),
                    func.count(Move.id).label("cnt"),
                )
                .join(Game, Game.id == Move.game_id)
                .where(Game.winner_id == Move.user_id)  # only winner's moves
                .group_by(Move.user_id, Move.game_id)
                .subquery()
            )
            efficiency = dict(
                s.execute(
                    select(
                        per_game_moves.c.uid, func.avg(per_game_moves.c.cnt)
                    ).group_by(per_game_moves.c.uid)
                ).all()
            )

            rows: List[LeaderBoard] = list()
            all_users = set(total_games_by_user) | set(wins_by_user) | set(efficiency)
            for user in all_users:
                wins = wins_by_user.get(user, 0)
                games = total_games_by_user.get(user, 0)

                if metric == "wins":
                    rows.append(
                        LeaderBoard(
                            user_id=user,
                            value=float(wins),
                            wins=wins,
                            games=games,
                        )
                    )

                elif metric == "efficiency":
                    value = efficiency.get(user, 0)
                    if value:
                        rows.append(
                            LeaderBoard(
                                user_id=user,
                                value=float(value),
                                wins=wins,
                                games=games,
                            )
                        )
            if metric == "wins":
                rows.sort(key=lambda x: (-x.value, x.user_id))
            elif metric == "efficiency":
                rows.sort(
                    key=lambda x: (x.value, -wins_by_user.get(x.user_id, 0), x.user_id)
                )
            else:
                return "Unsupported metric"

            return rows[:3]
