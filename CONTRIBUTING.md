# Contributing

This guide covers how to run and create games for the ARC-AGI-3 benchmark. You can implement games by hand or **use an AI coding agent** (Cursor, Copilot, etc.) with the files linked below—the repo is set up so agents can follow one skill and land a complete game.

## Prerequisites

This project uses [uv](https://github.com/astral-sh/uv) for dependency management.

## Running Games

### List Available Games
```bash
uv run python run_game.py --list
```

### Run a Game
```bash
uv run python run_game.py --game ez01 --version v1
```

### Interactive Play
```bash
uv run python run_game.py --game ez01 --version v1 --mode terminal
```

Controls (actions are abstract - each game defines what they mean):
- `1-4`: Primary actions (can be movement, rotation, firing, etc.)
- `5`: Special action (interact, select, rotate, attach/detach, etc.)
- `6`: Coordinate-based action (click at position)
- `7`: Undo
- `q`: Quit

### Auto Mode (Random Actions)
```bash
uv run python run_game.py --game ez01 --version v1 --mode auto --steps 50
```

## Creating a New Game

### AI-assisted workflow (recommended for speed)

Point your agent at the same conventions humans use:

| Resource | What it’s for |
|----------|----------------|
| [AGENTS.md](AGENTS.md) | Camera/UI patterns, abstract actions, common bugs, testing checklist, palette |
| [skills/create-arc-game/SKILL.md](skills/create-arc-game/SKILL.md) | End-to-end steps: layout, sprites, levels, `step()`, metadata, registry |

The repo exposes that skill in three equivalent places: **`skills/`** (symlink at repo root), **`.opencode/skills/`**, and **`.agents/skills/`**—use whichever path your tool resolves best.

**Minimal prompt you can paste:** *Implement a new ARC-AGI-3 game `{game_id}` at `environment_files/{game_id}/v1/`. Follow [AGENTS.md](AGENTS.md) and [skills/create-arc-game/SKILL.md](skills/create-arc-game/SKILL.md): static levels only, `ARCBaseGame` + `metadata.json`, register a row in [GAMES.md](GAMES.md). Game design: [grid size, entities, win/lose, which actions 1–7 do].*

**Done when:** `uv run python run_game.py --game {game_id} --version v1` runs, win advances levels, and [GAMES.md](GAMES.md) has a complete table row (optional: preview GIF under `assets/` like existing games).

If you prefer to implement without an agent, follow the numbered steps below.

### 1. Create Game Directory
```
environment_files/{game_id}/{version}/
├── {game_id}.py
└── metadata.json
```

### 2. Implement Game

Follow the patterns from established games in `environment_files/`.

**Basic structure:**
```python
from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)

# Define sprites
sprites = {
    "player": Sprite(pixels=[[9]], name="player", visible=True, collidable=True, tags=["player"]),
    "target": Sprite(pixels=[[4]], name="target", visible=True, collidable=False, tags=["target"]),
}

# Define levels
levels = [
    Level(
        sprites=[
            sprites["player"].clone().set_position(1, 1),
            sprites["target"].clone().set_position(3, 3),
        ],
        grid_size=(8, 8),
        data={"difficulty": 1},
    ),
]

class MyGame(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = MyGameUI(0)
        super().__init__(
            "mygame",
            levels,
            Camera(0, 0, 8, 8, 0, 4, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._targets = self.current_level.get_sprites_by_tag("target")

    def step(self) -> None:
        # Handle actions (abstract - define what they mean for YOUR game)
        if self.action.id.value == 1:
            # ACTION1 - could be movement, rotation, firing, etc.
            dy = -1
        elif self.action.id.value == 2:
            dy = 1
        elif self.action.id.value == 3:
            dx = -1
        elif self.action.id.value == 4:
            dx = 1
        
        # ... game logic ...
        
        self.complete_action()
```

### 3. Add Metadata
```json
{
  "game_id": "mygame-v1",
  "title": "My Game",
  "description": "Game description",
  "default_fps": 20,
  "baseline_actions": [15],
  "tags": ["static"],
  "local_dir": "environment_files/mygame/v1",
  "date_created": "2026-03-18"
}
```

### 4. Register Game

Add entry to [GAMES.md](GAMES.md):
```markdown
| mygame | 8×8 | 1 | Description here. | | • 1-4: Actions |
```

### 5. Test
```bash
uv run python run_game.py --game mygame --version v1
```

## Key Patterns

### Camera
Camera must match your largest level's grid size:
```python
Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR)
```

### Action Space
Actions are **abstract** - each game defines what they mean:

| Action | Description |
|--------|-------------|
| ACTION1 | Abstract 1 (semantically up) |
| ACTION2 | Abstract 2 (semantically down) |
| ACTION3 | Abstract 3 (semantically left) |
| ACTION4 | Abstract 4 (semantically right) |
| ACTION5 | Special (interact, select, rotate, etc.) |
| ACTION6 | Coordinate-based (x,y required) |
| ACTION7 | Undo |

### Target Collection
```python
# Must use ignore_collidable=True for targets
sprite = self.current_level.get_sprite_at(x, y, ignore_collidable=True)

# Check target first (before checking collidable)
if sprite and "target" in sprite.tags:
    self.current_level.remove_sprite(sprite)
elif not sprite or not sprite.is_collidable:
    self._player.set_position(new_x, new_y)
```

## Repository Structure

```
arc-interactive/
├── environment_files/     # All games
│   ├── ez01/v1/
│   ├── tt01/v1/
│   └── ...
├── skills/                  # Symlink → .opencode/skills (create-arc-game, play-arc-game, …)
├── .opencode/skills/        # Canonical skill definitions
├── assets/                  # Game preview GIFs
├── run_game.py              # CLI runner
├── AGENTS.md                # Agent + human patterns for games
├── GAMES.md                 # Game registry
├── README.md                # Quick start
└── CONTRIBUTING.md          # This guide
```

## Documentation

- [ARC-AGI-3 Docs](https://docs.arcprize.org/add_game)
- [AGENTS.md](AGENTS.md) — implementation patterns and pitfalls
- [Game Registry](GAMES.md)
