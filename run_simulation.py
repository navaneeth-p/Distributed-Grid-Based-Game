'''
File to run the simulation
'''

import argparse

from src.simulation import run_quick_sim


parser = argparse.ArgumentParser("")

parser.add_argument("--n_games", type=int, nargs='?', help="Number of games to be played")
parser.add_argument("--n_players", type=int, nargs='?', help="Number of players")


if __name__ == "__main__":
    args = parser.parse_args()
    n_games = args.n_games
    n_players= args.n_players
    if not n_games and n_players:
        raise ValueError("Please also specify number of games to be played with --n_games")
    if not n_players and n_games:
        raise ValueError("Please asl ospecify number of players with --n_players")
    if not n_players and not n_games:
        # 50 games among 10 users
        run_quick_sim(n_games=50, n_users=10)
    
    else:
        run_quick_sim(n_games=n_games, n_users=n_players)