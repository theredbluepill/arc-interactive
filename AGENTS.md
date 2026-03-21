# ARCAGI-3 Game Designer Agent

## Role
Agent responsible for designing and implementing ARC-AGI-3 games.

## Benchmark principle

ARC-AGI-style benchmarks are about **whether an AI can solve puzzles that humans can solve** when both operate under the **same official interface**: defined actions, observation format, and stated game rules. The goal is to measure **general problem-solving**, not which system had the **most task-specific training data** or memorized solutions.

When you author games in this repo, treat **human solvability (given that shared spec)** as a design guide: prefer **well-posed** levels—where goals are clear from layout, mechanics, or fair in-observation cues—over **under-specified** puzzles that only yield to guessing, huge search, or spoilers absent from the agent’s observation.

## Workflow

### 1. Game Design Phase
**Input**: Game concept or requirements
**Output**: Game specification

**Key Questions**:
- Grid size? (8x8, 16x16, 24x24, 64x64)
- What entities? (player, targets, walls, hazards)
- What actions? (define what ACTION1-7 mean for your game)
- Win/lose conditions?

### 2. Implementation Phase
**Input**: Game specification
**Output**: Working game in `environment_files/`

**Steps**:
1. Create directory: `environment_files/{stem}/{version}/` (two-letter stem + digits, e.g. `ez01`; version folder is usually `v1` on first landing, then often an 8-char git prefix after CI — see `CONTRIBUTING.md`)
2. Implement `{stem}.py` with:
   - Sprite definitions
   - Static levels (no PCG)
   - Game class extending `ARCBaseGame`
   - Win/lose conditions
3. Test with: `arc.make` using the full `game_id` from that folder’s `metadata.json`, or locally `uv run python run_game.py --game {stem} --version auto` — add `--mode human` for **pygame** hand-play (`scripts/human_play_pygame.py`).

### 3. Documentation Phase
**Input**: Completed game
**Output**: Updated tracking files

**Steps**:
1. Add entry to `GAMES.md` with all metadata columns
2. If you discover a **reusable** pattern (not stem-specific), add a short bullet under **Lessons learned (cross-repo)** below; otherwise rely on `GAMES.md`, `{stem}.py`, and **`scripts/render_arc_game_gif.py`** (see skill **`generate-arc-game-gif`**)

## Established Game Patterns

Based on `environment_files/` games (vc33, ls20, ft09):

### 1. Camera Initialization
```python
Camera(x, y, width, height, background_color, padding_color, [sprite_list])
```
- Position: always `(0, 0)`
- Width/height: 16x16 or 64x64 (match your largest level)
- Last param: list containing a custom RenderableUserDisplay object (optional but recommended)
```python
BACKGROUND_COLOR = 0
PADDING_COLOR = 4

camera = Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR)
# With custom UI sprite:
camera = Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui])
```

### 2. RenderableUserDisplay (UI Class)

All established games use a custom UI class that extends `RenderableUserDisplay`:

```python
from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)

class GameUI(RenderableUserDisplay):
    def __init__(self, game_state: int) -> None:
        self._state = game_state
    
    def update(self, game_state: int) -> None:
        self._state = game_state
    
    def render_interface(self, frame):
        # Draw UI overlay on frame (e.g., targets remaining, timer)
        return frame


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
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._targets = self.current_level.get_sprites_by_tag("target")
        # Initialize UI with target count
        self._ui.update(len(self._targets))
    
    def step(self) -> None:
        # ... game logic ...
        
        # Update UI when state changes
        self._ui.update(len(self._targets))
        
        self.complete_action()
```

### 3. Game Class __init__
```python
class MyGame(ARCBaseGame):
    def __init__(self) -> None:
        # Optional: create custom sprite object
        self._custom = CustomSprite(self)
        
        super().__init__(
            "game_id",
            levels,
            Camera(...),
            False,  # debug flag
            1,      # config value
            [1, 2, 3, 4],  # available_actions: simple actions (ACTION1–4); define semantics in step()
        )
```

### 3. on_set_level()
```python
def on_set_level(self, level: Level) -> None:
    # Store sprite references by tag
    self._player = self.current_level.get_sprites_by_tag("player")[0]
    self._targets = self.current_level.get_sprites_by_tag("target")
    
    # Optional: get level configuration data
    self._difficulty = self.current_level.get_data("difficulty")
```

### 4. step()
```python
def step(self) -> None:
    # Actions are ABSTRACT - define what each action means for YOUR game
    # Example: if your game is rotation, ACTION1 = rotate, not "up"
    
    if self.action.id.value == 1:
        # ACTION1 - could be movement, rotation, firing, etc.
        dy = -1  # up
    elif self.action.id.value == 2:
        dy = 1   # down
    elif self.action.id.value == 3:
        dx = -1  # left
    elif self.action.id.value == 4:
        dx = 1   # right
    elif self.action.id.value == 5:
        # Special action (interact, select, rotate, etc.)
        self._interact()
    elif self.action.id.value == 6:
        # Coordinate-based action
        x = self.action.data.get("x", 0)
        y = self.action.data.get("y", 0)
        self._click_at(x, y)
    
    # ... rest of game logic ...
    
    if not moved:
        self.complete_action()
        return
    
    # Process movement (example: this template maps ACTION1–4 to grid movement)
    new_x = self._player.x + dx
    new_y = self._player.y + dy
    
    # Check bounds and collisions
    grid_w, grid_h = self.current_level.grid_size
    if 0 <= new_x < grid_w and 0 <= new_y < grid_h:
        sprite = self.current_level.get_sprite_at(new_x, new_y)
        if not sprite or not sprite.is_collidable:
            self._player.set_position(new_x, new_y)
    
    # Check win condition
    if self._check_win():
        self.next_level()
    
    # Check lose condition (optional)
    # if self._check_lose():
    #     self.lose()
    
    self.complete_action()
```

### 5. Sprite Access Methods
```python
# Get sprites by tag
self._player = self.current_level.get_sprites_by_tag("player")[0]
targets = self.current_level.get_sprite_by_tag("target")

# Get sprite at position
sprite = self.current_level.get_sprite_at(x, y)

# Add/remove sprites
self.current_level.add_sprite(new_sprite)
self.current_level.remove_sprite(sprite)

# Sprite methods
sprite.set_position(x, y)
sprite.set_rotation(degrees)
sprite.color_remap(old_color, new_color)
sprite.collides_with(other_sprite)
```

## What NOT to Do

- Don’t assume you need PCG — static levels are fine.
- Don’t add action scrambling — not used here.
- Don’t build elaborate checkpoint systems unless the game design calls for it — established games in this repo typically don’t use them.
- Don’t vary grid size per episode — use a fixed camera matched to your level grid.

## Directory Structure

```
arc-interactive/
├── environment_files/          # All games
│   ├── {stem}/                 # e.g. ez01 (table column in GAMES.md)
│   │   └── {version}/          # e.g. 8-char SHA or v1 before CI bump
│   │       ├── {stem}.py
│   │       └── metadata.json   # game_id must equal "{stem}-{version}"
├── scripts/env_resolve.py      # full_game_id_for_stem / load_stem_game_py
├── GAMES.md                    # Game registry table
└── AGENTS.md                   # This file
```

## Testing Checklist

Before marking a game complete:
- [ ] Game loads with `arc.make()`
- [ ] Player moves correctly with actions 1-4
- [ ] Win condition triggers next_level()
- [ ] Camera renders correctly (size matches grid)
- [ ] Metadata.json is valid
- [ ] Entry added to GAMES.md

## Common Bugs and Solutions

### 1. Camera rendering incorrectly (wrong size)
**Cause**: Camera dimensions don't match grid size.
**Solution**: Set camera to match your largest level:
```python
# For 16x16 levels:
Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR)

# For 64x64 levels:
Camera(0, 0, 64, 64, BACKGROUND_COLOR, PADDING_COLOR)
```

### 2. AttributeError: 'Level' object has no attribute 'data'
**Cause**: Accessing level data incorrectly.
**Solution**: Use `get_data()` method:
```python
difficulty = self.current_level.get_data("difficulty")
# NOT: self.current_level.data
```

### 3. Sprites duplicating on level reset
**Cause**: Not clearing sprites before regenerating.
**Solution**: For games with dynamic content, clear sprites:
```python
def on_set_level(self, level: Level) -> None:
    self.current_level._sprites = []  # Clear first
    self._generate_level_content()     # Then regenerate
```

### 4. step() not processing actions
**Cause**: Missing `complete_action()` call.
**Solution**: Always call at end of step():
```python
def step(self) -> None:
    # ... game logic ...
    self.complete_action()  # Always call this!
```

### 5. Sprite not moving visually
**Cause**: Only updating coordinates, not sprite position.
**Solution**: Call set_position on sprite:
```python
self._player.set_position(new_x, new_y)
```

### 6. get_sprite_at returns None for targets
**Cause**: By default, get_sprite_at doesn't return non-collidable sprites (like targets).
**Solution**: Use `ignore_collidable=True`:
```python
sprite = self.current_level.get_sprite_at(x, y, ignore_collidable=True)
```

### 7. Target collection logic order
**Cause**: If checking is_collidable before checking target tag, targets (which are non-collidable) will be treated as empty space.
**Solution**: Check for target first:
```python
if sprite and "target" in sprite.tags:
    # Collect target first
    self.current_level.remove_sprite(sprite)
    self._targets.remove(sprite)
elif not sprite or not sprite.is_collidable:
    # Move to empty space or non-collidable area
    self._player.set_position(new_x, new_y)
```

### 8. Step-budget helpers (`_burn`, `_burn_step`) and `lose()`
**Cause**: Returning from `step()` when `_burn()` is true after `lose()` without calling `complete_action()`.
**Solution**: Always finish the action:
```python
if self._burn():
    self.complete_action()
    return
```

### 9. Shadowing `ARCBaseGame._state`
**Cause**: `ARCBaseGame` reserves `self._state` for `GameState`; assigning a dict (e.g. grid paint map) breaks the engine (`perform_action` / GIF capture).
**Solution**: Use another name (`_paint`, `_grid_cells`, etc.) for per-game dictionaries.

## Terminal Color Palette (from arc-agi rendering.py)

The terminal rendering uses ANSI RGB colors. Use this mapping for sprite colors:

```python
COLOR_MAP = {
    0: "#FFFFFFFF",  # White
    1: "#CCCCCCFF",  # Off-white
    2: "#999999FF",  # Light Gray
    3: "#666666FF",  # Gray
    4: "#333333FF",  # Dark Gray
    5: "#000000FF",  # Black
    6: "#E53AA3FF",  # Magenta
    7: "#FF7BCCFF",  # Light Magenta
    8: "#F93C31FF",  # Red
    9: "#1E93FFFF",  # Blue
    10: "#88D8F1FF", # Light Blue
    11: "#FFDC00FF", # Yellow
    12: "#FF851BFF", # Orange
    13: "#921231FF", # Maroon
    14: "#4FCC30FF", # Green
    15: "#A356D6FF", # Purple
}
```

**Key Colors:**
- Background: **5** (Black)
- Food: **11** (Yellow)
- Warm zones: **8** (Red)
- Player: **9** (Blue)
- Hazard: **8** (Red)
- Target: **11** (Yellow)
- Wall: **3** (Gray)

## Action Space

Actions are **abstract** — each game defines what they mean. See [ARC-AGI-3 Actions](https://docs.arcprize.org/actions). Human-facing docs map ACTION1–4 to arrows/WASD for playability; that does **not** require your game to implement cardinal movement.

| Action | Description |
|--------|-------------|
| ACTION1 | Simple game-defined action (often grid movement in this repo; UI may map to “up”) |
| ACTION2 | Simple game-defined action (often grid movement; UI may map to “down”) |
| ACTION3 | Simple game-defined action (often grid movement; UI may map to “left”) |
| ACTION4 | Simple game-defined action (often grid movement; UI may map to “right”) |
| ACTION5 | Special action (interact, select, rotate, attach/detach, execute, idle) |
| ACTION6 | Coordinate-based action (requires x,y in `self.action.data`) |
| ACTION7 | Undo action |

**Example** - a rotation game would define ACTION1 as "rotate clockwise":
```python
def step(self) -> None:
    if self.action.id.value == 1:
        self._rotate_cw()  # Not movement!
    elif self.action.id.value == 6:
        x = self.action.data.get("x", 0)
        y = self.action.data.get("y", 0)
        self._click_at(x, y)
    self.complete_action()
```

## References

- **ARC-AGI-3 Actions**: https://docs.arcprize.org/actions
- **ARC-AGI-3 Docs**: https://docs.arcprize.org/add_game
- **Established Games**:
  - `environment_files/vc33/9851e02b/vc33.py`
  - `environment_files/ls20/cb3b57cc/ls20.py`
  - `environment_files/ft09/9ab2447a/ft09.py`

---

## Lessons learned (cross-repo)

Condensed from many shipped stems. **Preview GIFs** use **`scripts/render_arc_game_gif.py`** + **`registry_gif_lib`** / **`registry_gif_overrides.json`** (skill **`generate-arc-game-gif`**); other automation lives under **`devtools/`**.

### ACTION6, camera, and HUD

- Map display clicks with **`camera.display_to_grid(x, y)`**; raw `action.data` pixels are not grid coordinates.
- Draw click ripples / overlays in **final 64×64 frame space** using the same scale and padding as the camera (e.g. a `_grid_to_frame_pixel` helper). Do not assume `frame_size // grid` without letterbox math.
- Hit-tests for multi-cell sprites: use **half-open** ranges (`sx <= gx < sx + width`).
- Use **`self.action`** from the engine, not a stale alias.
- Keep **`RenderableUserDisplay`** math aligned with **`Camera.render`** when the logical grid letterboxes inside the frame.

### Movement, grid logic, and tags

- **1×1** entities simplify collision; multi-cell avatars need an explicit footprint.
- When ACTION1–4 encode space, keep **`dx` / `dy`** naming consistent with the rest of the repo (often 1/2 = vertical, 3/4 = horizontal).
- **Non-collidable** sprites (targets, mines, switches, trails): decide interactions by **tag / purpose** before treating a cell as empty; use **`get_sprite_at(..., ignore_collidable=True)`** when you must see them.
- **Order matters**: e.g. collect or resolve **target** before treating the cell as walkable.
- Special physics (slide until stop, portals, forced vectors, gravity): run **reachability under your transition model**, not plain “flood fill on floor” — **BFS / search over `(player, …)` state** (blocks, visit sets, stop cells) before shipping.

### `step()`, state, and engine contract

- Almost always end **`step()`** with **`complete_action()`**. The rare exception is deliberate **multi-frame** tails (death FX, click ripple): omit only while the tail drains, then complete; still complete immediately on level/game-over defer paths that rely on follow-up steps.
- Never store game dictionaries in **`self._state`** — reserved for **`GameState`** (`_paint`, `_grid_cells`, etc.).
- After **`lose()`** with burn/defer helpers, still **finish the action** so the runner does not stall.

### Level data, variants, and authoring

- Read config with **`level.get_data("key")`**, not **`level.data`**.
- **`xx02` / `xx03` variants**: implement real rule differences in **code** (and any registry GIF plans), not only new **`GAMES.md`** rows.
- Layout traps to re-check across games: **walls on goals**, **portal bypasses**, **isolated open cells**, **decoy / k-of-n / directed edges** when cloning a mechanic — playtests and small solvers catch these early.

### Lasers, wires, and line semantics

- Ray / pulse loops: on OOB or blocker use **`break`** (or structured fall-through) so **post-loop win checks** still run.
- When a **player** can stand on a **goal** tile, query **tagged** sprites (e.g. receptor) with **`ignore_collidable=True`** before an untagged **`get_sprite_at`**, so sort order does not hide the goal.

### Preview GIFs and automation

- Prefer a **GIF-ready** **`RenderableUserDisplay`** (HUD + multi-frame click/ping cues in final **64×64** space); see skill **`generate-arc-game-gif`** and **`mm01`** / **`sq01`**.
- Extend **`registry_gif_lib`** (and, when needed, shared **`registry_*_gif.py`** helpers it imports) for **reusable** capture patterns; tune stems via **`registry_gif_overrides.json`**. Do **not** add new **`scripts/render_<stem>_gif.py`** CLI entrypoints—use **`render_arc_game_gif.py`** only.
- Build plans from **authored levels** (import **`levels`**, layout constants, tile geometry from the game module).
- **Append every** sub-frame when one logical step emits multiple layers (death animation, multi-hit).
- After **`next_level()`**, assert **`level_index` / `WIN`** — reset mutable state; do not compare **old** paint/counters to the **new** level’s goal.
- New stems that need **registry GIFs**: extend **`registry_gif_overrides.json`** / **`registry_gif_lib`** as needed; record with **`scripts/render_arc_game_gif.py`** (see existing stems in the same family).

### API / toolkit gotchas

- Use **`sprite.is_collidable`**, not **`sprite.collidable`** (arcengine).
- Normalize points from **`level.data`** with list comprehensions **`[(int(a), int(b)) for ...]`** — not **`tuple(int, int)(...)`**-style mistakes on **`tuple()`**.
- **`run_game.py`**: default **local environments** under **`environment_files/`**; **`--online`** + **`ARC_API_KEY`** when you need API metadata. See **`run_game.py --help`**.

### Where to dig deeper

| Need | Start here |
|------|------------|
| Mechanic summary | `GAMES.md` row + `{stem}.py` module docstring |
| Preview / registry GIF | `scripts/render_arc_game_gif.py` + `registry_gif_lib`, `registry_gif_overrides.json` |
| GIF-ready HUD audit | Skill **`generate-arc-game-gif`** (`skills/` / `.opencode/skills/` / `.agents/skills/`) |
| Solvability smoke | `scripts/verify_*solvability*.py` when one exists for your batch |

---

**Last Updated**: 2026-03-21
**Agent Version**: 2.2
