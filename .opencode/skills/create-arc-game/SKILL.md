# Skill: Create ARC-AGI-3 Game

## Overview
This skill guides the creation of ARC-AGI-3 games based on established patterns from `environment_files/`.

## Abstract actions (ACTION1–7)

Per the [ARC-AGI-3 Actions](https://docs.arcprize.org/actions) spec, each game **defines** what `ACTION1`–`ACTION7` do: grid movement, rotation, no-op, idle, clicks, etc. The official docs describe `ACTION1`–`ACTION4` as *simple actions that vary by game*; the up/down/left/right wording is for **human keybinding** in the UI, not a requirement that your `step()` implements cardinal movement.

Many games in this repo map `ACTION1`–`ACTION4` to **grid movement**—that is a **convention**, not a platform rule. If your design uses those IDs for something else (e.g. `ACTION1` = rotate clockwise), document it in `GAMES.md` and implement it explicitly in `step()`.

### New stems vs family variants

- Prefer a **new two-letter prefix** (`xx01`) when the verb is genuinely new (e.g. `nw01` arrow tiles, `bd01` no-revisit).
- Use **`xx02` / `xx03` only** for alternate rules **within** the same family (`pb`, `fs`, `tp`, `ic`, `va` alongside their `xx01`). Cap at **`03`** unless a project plan explicitly adds `04`+ (keeps variants meaningfully distinct).

## Game Structure

```
environment_files/{game_id}/{version}/
├── {game_id}.py          # Main game file
└── metadata.json         # Game metadata
```

## Required Components

### 1. Imports
```python
from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)
```

### 2. RenderableUserDisplay (UI Class)
All established games use a custom UI class:

```python
class GameUI(RenderableUserDisplay):
    def __init__(self, game_state: int) -> None:
        self._state = game_state
    
    def update(self, game_state: int) -> None:
        self._state = game_state
    
    def render_interface(self, frame):
        # Draw UI overlay on frame (e.g., targets remaining, timer)
        return frame
```

### 3. Sprite Definitions
Define sprites with:
- `pixels`: 2D array of color indices (0-15)
- `name`: Unique identifier
- `visible`: Boolean for rendering
- `collidable`: Boolean for collision detection
- `tags`: List for categorization
- `layer`: Optional rendering layer

### 4. Level Definitions
```python
levels = [
    Level(
        sprites=[
            sprites["player"].clone().set_position(1, 1),
            sprites["target"].clone().set_position(3, 3),
            sprites["wall"].clone().set_position(2, 2),
        ],
        grid_size=(16, 16),
        data={"difficulty": 1},
    ),
]
```

### 5. Game Class Structure

```python
class MyGame(ARCBaseGame):
    def __init__(self) -> None:
        # Create UI object
        self._ui = GameUI(0)
        
        super().__init__(
            "mygame",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )
    
    def on_set_level(self, level: Level) -> None:
        # Store sprite references by tag
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._targets = self.current_level.get_sprites_by_tag("target")
        # Initialize UI with target count
        self._ui.update(len(self._targets))
    
    def step(self) -> None:
        # Actions are ABSTRACT - define what they mean for YOUR game
        # Example: if your game is about rotation, ACTION1 = rotate, not "up"
        
        if self.action.id.value == 1:
            # ACTION1 - could be "up", "rotate", "fire", etc.
            dx = -1
        elif self.action.id.value == 2:
            # ACTION2
            dx = 1
        elif self.action.id.value == 3:
            # ACTION3
            dy = -1
        elif self.action.id.value == 4:
            # ACTION4
            dy = 1
        elif self.action.id.value == 5:
            # ACTION5 - special action (interact, select, etc.)
            self._interact()
        elif self.action.id.value == 6:
            # ACTION6 - coordinate-based (use self.action.data for x,y)
            x = self.action.data.get("x", 0)
            y = self.action.data.get("y", 0)
            self._click_at(x, y)
        
        if not moved:
            self.complete_action()
            return
        
        # Process movement
        new_x = self._player.x + dx
        new_y = self._player.y + dy
        
        # Check bounds and collisions
        grid_w, grid_h = self.current_level.grid_size
        if 0 <= new_x < grid_w and 0 <= new_y < grid_h:
            sprite = self.current_level.get_sprite_at(new_x, new_y)
            if not sprite or not sprite.collidable:
                self._player.set_position(new_x, new_y)
        
        # Check win condition
        if len(self._targets) == 0:
            self.next_level()
        
        # Update UI when state changes
        self._ui.update(len(self._targets))
        
        self.complete_action()
```

## Camera Configuration

**CRITICAL**: Camera dimensions must match your largest level's grid size:

```python
# For 16x16 levels:
Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR)

# For 64x64 levels:
Camera(0, 0, 64, 64, BACKGROUND_COLOR, PADDING_COLOR)
```

## Win/Lose Conditions

```python
def step(self) -> None:
    # ... movement logic ...
    
    # Check win condition
    if self._check_win():
        self.next_level()
    
    # Check lose condition (optional)
    if self._check_lose():
        self.lose()
    
    self.complete_action()
```

## Testing

Run with:
```python
import arc_agi
from arcengine import GameAction

arc = arc_agi.Arcade()
env = arc.make("mygame-v1", seed=0)  # use the full game_id from your package metadata after CI naming
result = env.step(GameAction.ACTION1, reasoning={})  # meaning defined by the game; often movement in this repo
```

## Metadata Requirements

```json
{
  "game_id": "mygame-v1",
  "title": "My Game",
  "default_fps": 20,
  "baseline_actions": [10, 15, 25],
  "tags": ["static"],
  "local_dir": "environment_files/mygame/v1"
}
```

`game_id` / `local_dir` must match the version directory name. Starting in `v1/` is typical; the repo’s **bump-env-versions** workflow may rename it to an 8-char SHA on merge and rewrite these fields.

## Common Patterns

## Color Palette

Use indices 0-15 in sprite pixels. The rendering layer converts these to RGB.

```python
COLOR_MAP = {
    0: (255, 255, 255),  # White
    1: (204, 204, 204),  # Off-white
    2: (153, 153, 153),  # Light Gray
    3: (102, 102, 102),  # Gray
    4: (51, 51, 51),     # Dark Gray
    5: (0, 0, 0),        # Black
    6: (229, 58, 163),   # Magenta
    7: (255, 123, 204),  # Light Magenta
    8: (249, 60, 49),    # Red
    9: (30, 147, 255),   # Blue
    10: (136, 216, 241), # Light Blue
    11: (255, 220, 0),   # Yellow
    12: (255, 133, 27),  # Orange
    13: (146, 18, 49),   # Maroon
    14: (79, 204, 48),   # Green
    15: (163, 86, 214),  # Purple
}
```

**Common colors:**
- Background: `5` (Black)
- Walls: `3` (Gray) or `2` (Light Gray)
- Player: `9` (Blue)
- Targets/Food: `11` (Yellow)
- Hazards/Warm zones: `8` (Red)
- Green items: `14` (Green)

### Grid Sizes
- Level 1: 8x8 (easy)
- Level 2: 16x16 (medium)
- Level 3: 24x24 (hard)
- Level 4+: 32x32+ (expert)

### Action Space

Actions are **abstract** — each game defines what they mean. See [ARC-AGI-3 Actions](https://docs.arcprize.org/actions).

| Action | Description |
|--------|-------------|
| `ACTION1` | Simple game-defined action (often grid movement in this repo; human UI may map to “up”) |
| `ACTION2` | Simple game-defined action (often grid movement; UI may map to “down”) |
| `ACTION3` | Simple game-defined action (often grid movement; UI may map to “left”) |
| `ACTION4` | Simple game-defined action (often grid movement; UI may map to “right”) |
| `ACTION5` | Special action (interact, select, rotate, attach/detach, execute, idle, etc.) |
| `ACTION6` | Coordinate-based action (requires x,y) |
| `ACTION7` | Undo action |

**Example** — rotation: `ACTION1` means rotate clockwise, not “move up”:
```python
def step(self) -> None:
    if self.action.id.value == 1:
        self._rotate_cw()  # Not movement!
        self.complete_action()
        return
    # ... handle other actions
```

## What NOT to Do

| Don't Do This | Do This Instead |
|--------------|-----------------|
| PCG randomization | Static levels |
| Action scrambling | Fixed action mapping |
| 10 checkpoints | No checkpoints needed |
| Dynamic camera size | Fixed camera matching max grid |

## Common Bugs and Solutions

### 1. Camera wrong size
```python
# Wrong - camera 8x8 but level 16x16
Camera(0, 0, 8, 8, ...)

# Correct - match largest level
Camera(0, 0, 16, 16, ...)
```

### 2. Level data access
```python
# Wrong
difficulty = self.current_level.data["difficulty"]

# Correct
difficulty = self.current_level.get_data("difficulty")
```

### 3. Sprite movement
```python
# Wrong - only updating coordinate
self._player_x = new_x

# Correct - updating sprite position
self._player.set_position(new_x, new_y)
```

### 4. Missing complete_action()
```python
# Wrong - step() doesn't end properly
def step(self) -> None:
    # ... logic ...

# Correct - always call complete_action()
def step(self) -> None:
    # ... logic ...
    self.complete_action()
```

### 5. get_sprite_at returns None for targets
```python
# Wrong - targets have is_collidable=False, so they're not returned
sprite = self.current_level.get_sprite_at(x, y)

# Correct - use ignore_collidable=True
sprite = self.current_level.get_sprite_at(x, y, ignore_collidable=True)
```

### 6. Target collection logic order
```python
# Wrong - non-collidable targets get treated as empty space
if not sprite or not sprite.is_collidable:
    self._player.set_position(new_x, new_y)
elif sprite and "target" in sprite.tags:
    # Never reached!

# Correct - check target first
if sprite and "target" in sprite.tags:
    self.current_level.remove_sprite(sprite)
    self._targets.remove(sprite)
    self._player.set_position(new_x, new_y)
elif not sprite or not sprite.is_collidable:
    self._player.set_position(new_x, new_y)
```

## GIF Demo for GAMES.md

All game GIFs in `assets/` must be **64×64 pixels** (the engine’s final frame is already 64×64; only resize if you captured a different size).

```python
from PIL import Image, Image as PILImage

# After capturing frames from the game:
img = img.resize((64, 64), PILImage.Resampling.NEAREST)

# Save GIF
frames[0].save("assets/{game_id}.gif", save_all=True, 
               append_images=frames[1:], duration=150, loop=0)
```

### Click / ACTION6 games

Demos should make **where the agent clicked** obvious for several frames.

1. **Click indicator in `RenderableUserDisplay`**  
   On `ACTION6`, after `camera.display_to_grid(x, y)` returns level grid coordinates `(gx, gy)`, convert them to **pixels on the final 64×64 frame** before drawing. The camera scales and letterboxes smaller viewports (e.g. 12×12 → 60×60 centered with padding). Drawing grid coords as if they were pixel coords pins the cursor to the top-left (wrong).  
   **Inverse of `display_to_grid`** (match `Camera` math in arcengine):

   ```python
   def _grid_to_frame_pixel(self, gx: int, gy: int) -> tuple[int, int]:
       cam = self.camera
       cw, ch = cam.width, cam.height
       scale_x = int(64 / cw)
       scale_y = int(64 / ch)
       scale = min(scale_x, scale_y)
       x_pad = int((64 - (cw * scale)) / 2)
       y_pad = int((64 - (ch * scale)) / 2)
       px = gx * scale + scale // 2 + x_pad
       py = gy * scale + scale // 2 + y_pad
       return px, py

   # In step(), after a valid hit:
   self._ui.set_click(*self._grid_to_frame_pixel(gx, gy))
   ```

2. **Animation, not a single frame**  
   Use a multi-step overlay (e.g. **expanding ring + cross** over ~15–20 render passes) so GIFs and markdown previews show a clear tap. Store `_click_frames` and decrement inside `render_interface` each time the frame is composed. See `environment_files/sq01/<version>/sq01.py` (`Sq01UI`; `<version>` is the sole package dir under `sq01/`).

3. **Recording the GIF**  
   - `arc.make(..., include_frame_data=True)` and `env.reset()` / `env.step(GameAction.ACTION6, data={"x": ..., "y": ...})`.  
   - Coordinates in `data` are **display space 0–63** (same as `display_to_grid` input). For a 12×12 camera with scale 5 and padding 2, center of grid cell `(gx, gy)` is  
     `display_x = gx * scale + scale // 2 + x_pad` (and similarly for `y`).  
   - Use `arc_agi.rendering.COLOR_MAP` + `hex_to_rgb` to turn index frames into RGB for Pillow, **or** attach a fixed 16-color palette to `P` mode images.  
   - Prefer **one captured frame per `step()`** and a **list of per-frame `duration` values** (ms) for pacing; hold the first frame of each level briefly so level changes read clearly.  
   - If the game uses an end-of-level delay (`next_level()` after N frames), include those steps in the capture so the GIF shows progression.  
   - **Pillow** often **merges consecutive identical bitmaps** when saving GIFs; that is normal. If you need more apparent length, vary the on-screen effect (your click animation) or timing rather than duplicating identical numpy frames.  
   - Example script: `scripts/render_sq01_gif.py`.

## Examples

See established games:
- `environment_files/vc33/9851e02b/vc33.py`
- `environment_files/ls20/cb3b57cc/ls20.py`
- `environment_files/ft09/9ab2447a/ft09.py`
- `environment_files/ez01/<version>/ez01.py`
- `environment_files/sq01/<version>/sq01.py` (ACTION6, grid→frame click FX, GIF script)
