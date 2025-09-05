# Backend SWE Take-Home Assignment - Python

## Overview

This is an implementation of a tic-tac-toe like grid based game engine

## Getting Started

### Prerequisites

- Python 3.11 or higher
- pip

### Installation

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### Running simulation

The simulation is implemented as a concurrent in-memory sqlite based run. To run the simulation, run:

```bash
python3 run_simulation.py --n_games=50 --n_players=20 # Specify number of games and players
# or
python3 run_simulation.py # Runs the simulation for a default 50 games for 10 players
```

The simulation as mentioned runs in-memory. There are tests added that test the API endpoints that
verifies that APIs work. To run the server and play the game the user can start the server by

```bash
uvicorn src.router:app --reload --port 8000
```

From here the game the can be played one of two ways.
1. By posting via the API UI at http://127.0.0.1:8000/docs or
2. By using curl on the command line as follows

```bash
# Create users
curl -sX POST http://127.0.0.1:8000/users -H "content-type: application/json" -d '{"name":"alice"}'
curl -sX POST http://127.0.0.1:8000/users -H "content-type: application/json" -d '{"name":"bob"}'

# Create game
curl -sX POST http://127.0.0.1:8000/game -H "content-type: application/json" -d '{"creator_user_id":1}'

# Join game
curl -sX POST http://127.0.0.1:8000/game/1/join -H "content-type: application/json" -d '{"user_id":2}'

# Game status
curl -s http://127.0.0.1:8000/game/1 | jq

# Make a move - Repeat with the other user and a different cell. 
curl -sX POST http://127.0.0.1:8000/game/1/move -H "content-type: application/json" -d '{"user_id":1,"row":0,"col":0}' | jq

# Per user state
curl -s http://127.0.0.1:8000/users/{user_id}/stats | jq

# Top 3 by wins
curl -s "http://127.0.0.1:8000/leaderboard?metric=wins" | jq

# Top 3 by efficieny
curl -s "http://127.0.0.1:8000/leaderboard?metric=efficiency" | jq

```

The application will start on port 8000.

### Running Tests

To run the included unit tests for testing the service and the endpoints, run

```bash
pytest -q
```
Note: src/tests/test_service.py::test_concurrency can be a bit flaky at times to the sqlite test setup and timing of the threads
but will succeed on a re-run.

### Sample Output

The following is an output from a simulation that runs 50 games across 20 players

```bash
Game id: 52 created by user: 41
Game id: 53 created by user: 29
Game id: 54 created by user: 36
Game id: 55 created by user: 42
User: 37 joined the game 55
User: 26 joined the game 52
Game id: 56 created by user: 37
User: 30 joined the game 53
User: 29 joined the game 56
Game id: 57 created by user: 31
User: 25 joined the game 57
Game id: 58 created by user: 23
Game id: 59 created by user: 34
User: 31 joined the game 58
User: 32 joined the game 59
Game 52 completed, winner: 26
Game 55 completed, winner: 37
Game id: 60 created by user: 27
User: 39 joined the game 60
Game id: 61 created by user: 40
User: 26 joined the game 61
Game 60 completed, winner: None
Game id: 62 created by user: 24
User: 31 joined the game 62
Game 62 completed, winner: 24
Game id: 63 created by user: 27
User: 36 joined the game 63
Game 63 completed, winner: 27
Game id: 64 created by user: 29
User: 37 joined the game 64
Game 56 completed, winner: 37
Game id: 65 created by user: 39
User: 24 joined the game 65
Game 57 completed, winner: 31
Game 65 completed, winner: 39
Game id: 66 created by user: 42
User: 41 joined the game 66
Game 66 completed, winner: 42
Game 58 completed, winner: 23
Game id: 67 created by user: 42
User: 23 joined the game 67
Game id: 68 created by user: 38
User: 40 joined the game 68
Game 67 completed, winner: 23
Game id: 69 created by user: 23
User: 25 joined the game 69
Game id: 70 created by user: 34
User: 32 joined the game 70
Game 64 completed, winner: 29
Game id: 71 created by user: 41
User: 33 joined the game 71
Game 70 completed, winner: 34
Game id: 72 created by user: 32
User: 23 joined the game 72
Game 72 completed, winner: None
Game id: 73 created by user: 38
User: 36 joined the game 73
Game 59 completed, winner: 32
Game id: 74 created by user: 29
User: 26 joined the game 74
Game 73 completed, winner: 36
Game id: 75 created by user: 40
Game 68 completed, winner: 38
Game id: 76 created by user: 27
User: 23 joined the game 76
Game 74 completed, winner: 29
Game id: 77 created by user: 40
User: 42 joined the game 77
Game 71 completed, winner: 41
Game id: 78 created by user: 31
Game 77 completed, winner: 40
User: 39 joined the game 78
Game id: 79 created by user: 36
User: 31 joined the game 79
Game 69 completed, winner: 23
Game id: 80 created by user: 38
User: 28 joined the game 80
User: 34 joined the game 54
Game 80 completed, winner: 28
Game id: 81 created by user: 41
User: 23 joined the game 81
Game 78 completed, winner: 31
Game id: 82 created by user: 39
Game 54 completed, winner: 36
User: 33 joined the game 82
Game id: 83 created by user: 40
User: 23 joined the game 83
Game 81 completed, winner: 41
Game id: 84 created by user: 27
User: 31 joined the game 84
User: 41 joined the game 75
Game 79 completed, winner: 36
Game id: 85 created by user: 40
User: 38 joined the game 85
Game 83 completed, winner: 23
Game id: 86 created by user: 42
User: 23 joined the game 86
Game 85 completed, winner: 40
Game id: 87 created by user: 24
User: 25 joined the game 87
Game 82 completed, winner: 33
Game id: 88 created by user: 39
User: 29 joined the game 88
Game 75 completed, winner: 40
Game id: 89 created by user: 39
Game 76 completed, winner: None
Game id: 90 created by user: 33
User: 38 joined the game 90
User: 31 joined the game 89
Game 86 completed, winner: 42
Game id: 91 created by user: 41
User: 33 joined the game 91
Game 87 completed, winner: 24
Game id: 92 created by user: 38
User: 35 joined the game 92
Game 89 completed, winner: 31
Game 91 completed, winner: 33
Game id: 93 created by user: 31
User: 28 joined the game 93
Game id: 94 created by user: 41
User: 38 joined the game 94
Game 53 completed, winner: 29
Game id: 95 created by user: 37
User: 24 joined the game 95
Game 92 completed, winner: 38
Game id: 96 created by user: 37
Game 84 completed, winner: 27
User: 27 joined the game 96
Game id: 97 created by user: 33
User: 34 joined the game 97
Game 90 completed, winner: None
Game id: 98 created by user: 38
User: 30 joined the game 98
Game 94 completekd, winner: 41
Game id: 99 created by user: 33
User: 40 joined the game 99
Game 95 completed, winner: 24
Game id: 100 created by user: 30
User: 37 joined the game 100
Game 97 completed, winner: 33
Game id: 101 created by user: 23
User: 30 joined the game 101
Game 98 completed, winner: 38
Game 101 completed, winner: 30
Game 100 completed, winner: 30
Game 93 completed, winner: 31
Game 96 completed, winner: 37
Game 99 completed, winner: None
Game 61 completed, winner: 40
Game 88 completed, winner: 29

Top 3 ratios by win
User: 29, Win ratio: 0.800 (wins=4, games=5)
User: 24, Win ratio: 0.750 (wins=3, games=4)
User: 36, Win ratio: 0.750 (wins=3, games=4)

```