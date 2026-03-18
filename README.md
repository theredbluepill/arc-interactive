# ARC-AGI-3 Games

A collection of games for the ARC-AGI-3 benchmark.

## Quick Start

This project uses [uv](https://github.com/astral-sh/uv) for dependency management and running games.

### Running Games

All commands use `uv run`:

#### List Available Games
```bash
uv run python run_game.py --list
```

#### Run a Game
```bash
uv run python run_game.py --game co01 --version v1
```

#### Interactive Play
```bash
uv run python run_game.py --game co01 --version v1 --mode terminal
```

Controls:
- `1-4`: Movement actions
- `5-6`: Special actions
- `q`: Quit

#### Show Game Info
```bash
uv run python run_game.py --game co01 --version v1 --info
```

## Games

See [GAMES.md](GAMES.md) for the complete list of available games and detailed information.

## Repository Structure

```
arc-games/
├── environment_files/     # All games
│   ├── co01/v1/
│   ├── vc33/9851e02b/
│   └── ...
├── run_game.py           # CLI runner
├── GAMES.md              # Game registry
└── README.md             # This file
```

## Adding New Games

1. Create game directory: `environment_files/{game_id}/{version}/`
2. Implement game following [ARC-AGI-3 API](https://docs.arcprize.org/add_game)
3. Add metadata.json
4. Register in [GAMES.md](GAMES.md)
5. Test: `uv run python run_game.py --game {game_id} --version {version}`

## Documentation

- [ARC-AGI-3 Docs](https://docs.arcprize.org/add_game)
- [Game Registry](GAMES.md)

---

**Last Updated**: 2026-03-18
