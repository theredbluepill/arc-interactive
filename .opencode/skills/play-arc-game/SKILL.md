# Play ARC Game Skill

Skill for playing and testing ARC-AGI-3 games using `run_game.py`.

## Running Games

### Interactive Mode
```bash
uv run python run_game.py --game <stem> --version auto
```

(`<stem>` is the two-letter+digits id from `GAMES.md`, e.g. `ez01`. `auto` picks the sole package dir under `environment_files/<stem>/`.)

### Auto Mode (Random Actions)
```bash
uv run python run_game.py --game <stem> --version auto --mode auto --steps 50
```

### Programmatic Testing

`arc.make` needs the **full** `game_id` string from that package’s `metadata.json` (e.g. `ez01-63be02fb`). From repo root you can resolve it with `scripts/env_resolve.full_game_id_for_stem("ez01")`.

```python
from arc_agi import Arcade, OperationMode
from arcengine import GameAction

arc = Arcade("environment_files", OperationMode.OFFLINE)
env = arc.make("ez01-63be02fb", seed=0)  # replace with your tree’s metadata game_id

# Execute actions
result = env.step(GameAction.ACTION1, reasoning={"test": 0})
print(f"State: {result.state}")
```

Other stems: **pb02** (two-crate push), **nw01** (arrow-tile forcing), **ex01** (uses **ACTION5** on the exit pad), **gp01** / **lo01** (**ACTION6**-only play; **ACTION1–4** are no-ops) — each uses its own `game_id` from disk.

## ACTION6: Click/Coordinate Actions

For games using ACTION6 (click), coordinates are in **display space** (0-63), not grid space.

### Display to Grid Conversion

For a 32×32 grid on a 64×64 camera:
```python
# Grid to display (what you send in action.data)
display_x = grid_x * 2 + 1
display_y = grid_y * 2 + 1

# Display to grid (what you receive)
grid_x = (display_x - 1) // 2
grid_y = (display_y - 1) // 2
```

### Helper Function for Clicking
```python
def click_at(env, grid_x, grid_y, camera_width=64):
    """Execute a click action at grid coordinates."""
    scale = camera_width // 32  # 2 for 64x64 camera
    display_x = grid_x * scale + (scale // 2)
    display_y = grid_y * scale + (scale // 2)
    return env.step(
        GameAction.ACTION6,
        data={"x": display_x, "y": display_y},
        reasoning={"click": f"at ({grid_x}, {grid_y})"}
    )
```

### Click Cursor for GIFs

To make clicking visible in GIF captures, add a click indicator to your game's UI:

```python
class GameUI(RenderableUserDisplay):
    def __init__(self):
        self._click_pos = None
        self._click_frames = 0
    
    def set_click(self, x, y):
        """Show click cursor at grid position."""
        self._click_pos = (x, y)
        self._click_frames = 10  # Show for 10 frames
    
    def render_interface(self, frame):
        if self._click_pos and self._click_frames > 0:
            cx, cy = self._click_pos
            scale = 2  # Match your grid-to-display ratio
            # Draw crosshair cursor
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    if abs(dx) == 2 or abs(dy) == 2:
                        px, py = cx * scale + dx, cy * scale + dy
                        if 0 <= px < 64 and 0 <= py < 64:
                            frame[py, px] = 7  # Navy color
            self._click_frames -= 1
        return frame
```

Then call `self._ui.set_click(grid_x, grid_y)` when ACTION6 is executed.

## Action Mapping

Actions are **abstract** - each game defines what they mean. The canonical mapping is:

- **ACTION1**: Up-like (semantic "forward" for the game)
- **ACTION2**: Down-like (semantic "backward" for the game)
- **ACTION3**: Left-like (semantic "left" for the game)
- **ACTION4**: Right-like (semantic "right" for the game)
- **ACTION5**: Special (game-dependent: interact, select, rotate, etc.)
- **ACTION6**: Click/Coordinate (requires x,y in action.data)
- **ACTION7**: Undo (when the environment supports it)

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
create_gif("<ez01 game_id from metadata>", GameAction.ACTION1, [2, 4, 6, 6, 7], "assets/ez01.gif")
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

1. **Missing metadata.json**: Game won't load. New packages usually start at `environment_files/{stem}/v1/`; CI may rename the folder to an 8-char prefix — `game_id` / `local_dir` in metadata must stay in sync.

2. **Camera size mismatch**: Camera must match largest level grid size (16x16, 24x24, etc.)

3. **Targets not collected**: Use `ignore_collidable=True` in `get_sprite_at()`

4. **Action not working**: Check action mapping - ACTION1 is Up, not necessarily "button 1"

## Quick Reference

| Task | Command/Tool |
|------|--------------|
| List games | `run_game.py --list` |
| Play game (pygame) | `run_game.py --game <stem> --version auto --mode human` |
| Auto test | `run_game.py --game <stem> --version auto --mode auto --steps 100` |
| Check state | `result.state`, `result.levels_completed` |
| Create GIF | Use `include_frame_data=True` + colorize function |
