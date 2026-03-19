# Contributing

This guide covers how to run and create games for the ARC-AGI-3 benchmark.

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
├── assets/              # Game preview GIFs
├── run_game.py          # CLI runner
├── GAMES.md            # Game registry
├── README.md           # Quick start
└── CONTRIBUTING.md    # This guide
```

## Documentation

- [ARC-AGI-3 Docs](https://docs.arcprize.org/add_game)
- [Game Registry](GAMES.md)
