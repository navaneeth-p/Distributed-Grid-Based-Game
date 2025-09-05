"""
Util file with helper functions
"""

from typing import List, Optional

from src.schema import Game, GameStatus, Move

VICTORY_CONDITIONS = [
    # rows
    [(0, 0), (0, 1), (0, 2)],
    [(1, 0), (1, 1), (1, 2)],
    [(2, 0), (2, 1), (2, 2)],
    # cols
    [(0, 0), (1, 0), (2, 0)],
    [(0, 1), (1, 1), (2, 1)],
    [(0, 2), (1, 2), (2, 2)],
    # diags
    [(0, 0), (1, 1), (2, 2)],
    [(0, 2), (1, 1), (2, 0)],
]


def construct_board(moves: List[Move]) -> List[List[Optional[int]]]:
    """
    Method to construct the 3x3 board
    """
    board: List[List[Optional[int]]] = [[None for _ in range(3)] for _ in range(3)]
    for move in moves:
        board[move.row][move.col] = move.user_id

    return board


def find_winner(board: List[List[Optional[int]]]) -> Optional[int]:
    """
    Method to determine the winner
    """
    for condition in VICTORY_CONDITIONS:
        ids = [board[row][col] for row, col in condition]
        if ids[0] is not None and ids.count(ids[0]) == 3:
            return ids[0]

    return None


def next_player(game: Game) -> Optional[int]:
    """
    Method to figure out the next player to move
    """
    if game.status != GameStatus.in_progress:
        return None

    order = game.turn_no % 2  # even goes first, odd goes second
    order_dict = {player.player_order: player.user_id for player in game.players}
    return order_dict.get(order)


def players_in_order(game: Game) -> List[int | None]:
    """
    Method to get the players in the order of play
    """
    order_dict = {player.player_order: player.user_id for player in game.players}
    return [order_dict.get(0), order_dict.get(1)]
