# Play ARC Game Skill

Skill for playing and testing ARC-AGI-3 games using `run_game.py`.

## Running Games

### Interactive Mode
```bash
uv run python run_game.py --game <game_id> --version v1
```

### Auto Mode (Random Actions)
```bash
uv run python run_game.py --game <game_id> --version v1 --mode auto --steps 50
```

### Programmatic Testing

```python
from arc_agi import Arcade, OperationMode
from arcengine import GameAction

arc = Arcade('environment_files', OperationMode.OFFLINE)
env = arc.make('ez01-v1', seed=0)

# Execute actions
result = env.step(GameAction.ACTION1, reasoning={'test': 0})
print(f"State: {result.state}")
```

## Action Mapping

- **ACTION1**: Up
- **ACTION2**: Down
- **ACTION3**: Left
- **ACTION4**: Right
- **ACTION5**: Special (game-dependent)
- **ACTION6**: Click/Interact (game-dependent)

## Capturing Frames for GIFs

```python
from arc_agi import Arcade, OperationMode
from arcengine import GameAction
from PIL import Image
import numpy as np

# ARC color palette
COLOR_MAP = {
    0: (0, 0, 0),        # Black (background)
    2: (255, 0, 0),      # Red (hazard)
    3: (0, 255, 0),      # Green
    4: (255, 255, 0),    # Yellow (target)
    5: (128, 128, 128), # Gray (wall)
    6: (0, 255, 255),    # Cyan
    7: (0, 0, 255),      # Navy
    8: (128, 0, 0),      # Maroon
    9: (0, 128, 255),    # Blue (player)
}

def colorize(frame):
    """Convert ARC color indices to RGB."""
    h, w = frame.shape
    rgb = np.zeros((h, w, 3), dtype=np.uint8)
    for color_idx, rgb_val in COLOR_MAP.items():
        mask = frame == color_idx
        rgb[mask] = rgb_val
    return rgb

def create_gif(game_id, action, steps_per_level, output_path):
    """Create a GIF of gameplay."""
    arc = Arcade('environment_files', OperationMode.OFFLINE)
    env = arc.make(game_id, seed=0, include_frame_data=True)
    
    frames = []
    for level_num, n in enumerate(steps_per_level):
        for i in range(n):
            result = env.step(action, reasoning={'step': i})
            frame = result.frame[0]
            rgb = colorize(frame)
            img = Image.fromarray(rgb, 'RGB')
            img = img.convert('P', palette=Image.ADAPTIVE, colors=256)
            frames.append(img)
    
    frames[0].save(output_path, save_all=True, append_images=frames[1:], 
                   duration=150, loop=0, optimize=False)

# Example: ez01 (5 levels, UP action)
create_gif('ez01-v1', GameAction.ACTION1, [2, 4, 6, 6, 7], 'assets/ez01.gif')
```

## Checking Game State

```python
result = env.step(GameAction.ACTION1, reasoning={'test': 0})

# State attributes
print(f"State: {result.state}")           # NOT_FINISHED, WIN, LOSE
print(f"Levels: {result.levels_completed}")
print(f"Win levels: {result.win_levels}")
print(f"Available actions: {result.available_actions}")
print(f"Action input: {result.action_input}")
```

## Finding Available Games

```bash
uv run python run_game.py --list
```

Or check `GAMES.md` for the game registry.

## Testing All Levels

```python
# Run through all levels to completion
for level_num in range(5):  # Adjust for number of levels
    for step in range(20):   # Reasonable step limit
        result = env.step(action, reasoning={'level': level_num, 'step': step})
        if result.state == GameState.WIN:
            break
    if result.levels_completed >= total_levels:
        break
```

## Common Issues

1. **Missing metadata.json**: Game won't load. Create one in `environment_files/{game_id}/v1/`

2. **Camera size mismatch**: Camera must match largest level grid size (16x16, 24x24, etc.)

3. **Targets not collected**: Use `ignore_collidable=True` in `get_sprite_at()`

4. **Action not working**: Check action mapping - ACTION1 is Up, not necessarily "button 1"

## Quick Reference

| Task | Command/Tool |
|------|--------------|
| List games | `run_game.py --list` |
| Play game | `run_game.py --game <id> --version v1` |
| Auto test | `run_game.py --game <id> --mode auto --steps 100` |
| Check state | `result.state`, `result.levels_completed` |
| Create GIF | Use `include_frame_data=True` + colorize function |
