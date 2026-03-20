# ARCAGI-3 Game Designer Agent

## Role
Agent responsible for designing and implementing ARC-AGI-3 games.

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
1. Create directory: `environment_files/{game_id}/{version}/`
2. Implement `{game_id}.py` with:
   - Sprite definitions
   - Static levels (no PCG)
   - Game class extending `ARCBaseGame`
   - Win/lose conditions
3. Test with: `arc.make("{game_id}-{version}", seed=0)`

### 3. Documentation Phase
**Input**: Completed game
**Output**: Updated tracking files

**Steps**:
1. Add entry to `GAMES.md` with all metadata columns
2. Update this `AGENTS.md` with lessons learned

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
        if not sprite or not sprite.collidable:
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
│   ├── {game_id}/
│   │   └── {version}/
│   │       ├── {game_id}.py
│   │       └── metadata.json
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

**Last Updated**: 2026-03-20
**Agent Version**: 2.1

## Lessons Learned (tb01 Bridge Builder)

### Key Insights from tb01 Redesign

1. **Keep entities simple**: 1x1 sprites are MUCH easier to work with than multi-cell sprites
   - Player: 1x1 (single cell collision)
   - Bridges: 1x1 (place anywhere on water)
   - Islands: 3x3 (enough for player to walk around)

2. **Grid size matters**: 24x24 is a good middle ground
   - Large enough for interesting puzzles
   - Small enough to reason about
   - Scales well with 1x1 entities

3. **Bridge collision math**: When player is N cells wide:
   - Bridge must be at least N+1 cells wide to allow stepping off
   - Or: bridge fills single cells, player walks cell-by-cell

4. **Level progression**: When `next_level()` is called:
   - Player position resets to new level's start
   - `on_set_level` clears `self._bridges` (fresh bridges per level)
   - Check `result.levels_completed` for accurate tracking

5. **Lives system**: When player walks into water:
   - Reset to `_start_position` (not (0,0))
   - Bridges persist across deaths **within** the same level
   - Only call `lose()` when lives reach 0

### tb01 Final Design

- **Grid**: 24x24
- **Player**: 1x1 blue square
- **Islands**: 3x3 maroon squares
- **Goal island**: 3x3 green square
- **Water**: cyan/light-blue background (not sprites)
- **Reefs / caps**: gray **rock** cells (no walk / no bridge); **max_bridges** and **step_limit** optional per level (generous on v1)
- **Bridges**: 1x1 orange overlay on water only; **ACTION6** → `display_to_grid`; toggle
- **Actions**: 1-4 movement, 6=toggle bridge on water
- **Lives**: 3 per level
- **Difficulty** (`data["difficulty"]` 1–5): bottom-left **UI ticks**
- **Preview GIF**: `uv run python scripts/render_tb01_gif.py` — hand-authored plans per level (straight row, three-in-a-row ×2, diagonal run, south leg, row + extra hubs); cell-center display coords for clicks (inverse of `display_to_grid`)

### Bugs Fixed

1. **3x3 player collision**: Originally checked 9 cells, but player only occupies 4 cells
2. **Bridge placement distance**: dist=1 placed bridges too close for player to step off
3. **Level transition**: `next_level()` properly resets player to new level start
4. **ACTION6 coords**: Must use `display_to_grid`, not raw `data` as grid coords
5. **Bridge UI overlay**: `Tb01UI` must use the same scale/letterbox math as `Camera.render` (64×64 output), not `h/24` float scaling

## Lessons Learned (sk01 Sokoban)

1. **Levels**: **5** authored levels (was 7); camera stays **16×16** so **8×8** and **12×12** grids letterbox. Harder levels add **wall blockers** (corner posts → partial barrier → vertical wall with one gap → corridor split for three blocks).
2. **Solvability**: Several older wall rings caged blocks; new layouts were checked with a **BFS** over `(player, sorted block positions)` before shipping.
3. **Preview GIF**: `uv run python scripts/render_sk01_gif.py` — same BFS generates optimal-ish move lists per level, then steps **ACTION1–4** (up/down/left/right per `sk01.step`).

## Lessons Learned (sy01 Mirror Maker)

1. **ACTION6**: Use `self.camera.display_to_grid(x, y)` for grid cells; use **`self.action`**, not `self._action`. `cx // (64 // GRID_WIDTH)` is wrong for letterboxed viewports (e.g. 11×11 → 5px scale + padding).
2. **Click feedback (SKILL / sq01 pattern)**: After a resolved grid hit, `self._ui.set_click(*self._grid_to_frame_pixel(gx, gy))` so the ripple draws in **final 64×64 frame space** (same scale/pad as `display_to_grid` inverse). `Sy01UI` uses expanding Chebyshev ring + plus (see `Sq01UI`).
3. **Placement highlight**: `Sy01UI.set_placed` also uses `_grid_to_frame_pixel` for place/remove flash.
4. **Patterns**: Keep blue template dots in columns **0–4** only (divider **x = 5**); mirror targets are **6–10**.
5. **Preview GIF**: `uv run python scripts/render_sy01_gif.py` — `ACTION6` **`data`** uses **cell-center display pixels** on each mirrored cell (`gx * scale + scale//2 + pad`); **12** no-op steps (`0,0` → `display_to_grid` **None**) burn win defer; levels **1–3**.

## Lessons Learned (ul01 Unlock)

1. **Preview GIF**: `uv run python scripts/render_ul01_gif.py` — scripted full clear of levels 1–5. **L5** must grab the key at `(7,0)` before walking the bottom row to the door at `(7,7)` (all-right first hits the door without a key). **L4** uses three downs to `(3,3)`, not four.

## Lessons Learned (tt01 Collection)

1. **Movement**: `ACTION1`/`2` = vertical (`dy`), `ACTION3`/`4` = horizontal (`dx`) — keep `dx`/`dy` naming in `step()` so it matches the rest of the repo.
2. **Hazards**: Same as walls for movement (`collidable=True`); the player simply cannot enter the cell (no separate `lose()`).
3. **Preview GIF**: `uv run python scripts/render_tt01_gif.py` — greedy shortest-path to the nearest remaining target per segment (BFS), concatenated across 8×8 / 16×16 / 24×24 levels; camera is 24×24 with letterboxing on smaller levels.

## Lessons Learned (wm01 Whack-a-Mole)

1. **ACTION6 coords**: 64×64 frame with 32×32 logic grid uses `grid_x = x // 2`, `grid_y = y // 2` in `wm01.py` (full-frame camera; no letterbox). Clicks for demos: aim near mole center in grid `(mx+2, my+2)` → display `(gx*2+1, gy*2+1)`.
2. **Checkpoints**: Every 3 mole appearances, need `checkpoint_score >= 2` to pass; two passed checkpoints call `next_level()`. Miss enough and `lose()`.
3. **Preview GIF**: `uv run python scripts/render_wm01_gif.py` — `seed=0`, auto-whack when a mole is up else click `(0,0)`; ~72 steps shows clearing level 1 and early level 2.

## Lessons Learned (pt01 Pattern Rotation)

1. **Layout**: Keep rotatables in a **centered** block left of the hint column (`_PLAYFIELD_MAX_X` ≈ 43; separator **44**, hints from **46**). Use `_layout_centered(n, ncols, stride)` so 2×2 → 4×4 boards scale without crowding the target key.
2. **Initial rotations**: Use `_wrong_rotation(target, Random(level_seed))` so pieces never start solved; per-level RNG seeds (**7101**–**7105**) keep layouts reproducible.
3. **ACTION6**: Map through `self.camera.display_to_grid(x, y)`; hit-test **3×3** sprites with `sx <= gx < sx + 3` (half-open), not `<= sx + 3`.
4. **Preview GIF**: `uv run python scripts/render_pt01_gif.py` — precomputes clockwise quarter-turns per tile, plays levels **1–3**.

## Lessons Learned (sv01 Survival)

1. **Palette**: **Food** = index **14** (green). **Warm zone** tiles = **12** (orange — reads warmer than red **8** and avoids hazard-like coloring). UI hunger bar stays **14**; warmth bar uses **12** to match zones.
2. **Mechanics**: Hunger drops every step; warmth drops only when the player is not standing on a `warm_zone` cell. `next_level()` after **60** survived steps per level.
3. **ACTION5**: **Idle** — no movement and no food pickup on that step; decay and the step counter still apply. Use instead of pointless jiggle when already safe in a warm zone.
4. **Preview GIF**: `uv run python scripts/render_sv01_gif.py` — greedy BFS bot; uses **ACTION5** when warm and fed enough, else moves toward warmth/food; **180** steps = levels **1–3** on `seed=0` (larger levels may need a stronger policy for full episode capture).

## Lessons Learned (ff01 Flood Fill)

1. **Topology**: Use **`Enclosure`** = wall cell set + **BFS** `interior` from a seed (works for **rect**, **donut** (outer + inner perimeters), **L-room**, **C-bay**). Keep shapes inside **64×64**.
2. **ACTION6**: **`camera.display_to_grid(x, y)`** for grid hits; **`Ff01UI.set_click(*self._grid_to_frame_pixel(gx, gy))`** so the ripple matches **Sq01** (Chebyshev ring + plus) in final **64×64** space. Off-grid: clamp raw **x,y** to **0–63** for feedback only, then count as a miss.
3. **Difficulty**: Step budget **`max(10, 8 + level*2 + n_shapes*6)`**; **ACTION1–4** are **no-ops** for GIF pacing and agents that need idle steps. **`WIN_HOLD_FRAMES`** defers **`next_level()`** so fills read clearly.
4. **Preview GIF**: `uv run python scripts/render_ff01_gif.py` — full **5** levels to **`GameState.WIN`**; after each **ACTION6**, burn **`Ff01UI.CLICK_ANIM_FRAMES`** with **ACTION1**; assert **`level_index`** between levels. (Terminal **`FrameDataRaw`** may show **`levels_completed==0`** even on **WIN** — don’t assert that field.)

## Lessons Learned (rs01 Rule Switcher)

1. **Movement**: **ACTION1–4** = up / down / left / right (same as `GAMES.md`). Camera **16×16**; smaller grids letterbox inside the viewport.
2. **Rules**: Only targets matching **`_safe_color`** may be collected until **`_all_cycled`** (full rotation through `safe_colors`); then any remaining target is allowed. **`_steps % cycle_interval == 0`** advances the signpost.
3. **HUD (`Rs01UI`)**: **~5** top pixel rows on the **64×64** frame — level color badge, **cycle strip** (one slot per phase; active slot white cap + full color), **green dots** when `all_cycled`, **yellow** target-count ticks, **win-hold** pulse line.
4. **Preview GIF**: `uv run python scripts/render_rs01_gif.py` — **L1** + **L2** full clears (BFS L2 under the 12-step cycle), **`WIN_HOLD_FRAMES`** after each, then a short **L3** empty-lane teaser (**2/3** levels passed); **`_sync_ui()`** after gameplay and during win hold.

## Lessons Learned (sq01 Sequencing)

1. **ACTION6**: `camera.display_to_grid(x, y)` for hits; **2×2** blocks use half-open test `sx <= gx < sx + 2`. Ripple uses **`_grid_to_frame_pixel(gx, gy)`** (final **64×64** space).
2. **Click ripple in one `env.step`**: After `set_click`, set **`_ripple_tail = CLICK_ANIM_FRAMES - 1`** and **omit `complete_action()`** until the tail drains (same inner-loop idea as **ms01** death frames). **Level-complete** and **game-over defer** still use **`complete_action()`** immediately so **`_end_frames`** burns on following steps.
3. **Off-grid click**: Clamp raw **`x, y`** to **0–63** for **`set_click`** so padding taps still show a ripple before wrong-life logic.
4. **Preview GIF**: `uv run python scripts/render_sq01_gif.py` — **cell centers** `gx*5+4` for **12×12** (scale **5**, pad **2**); **`snap_all`** every sub-frame; **L2** opens with one **wrong-order** tap (blue before red) then the full sequence; **exactly 12** win-defer steps per clear (matches `_end_frames`; more would execute real clicks on the next level); defer uses in-bounds **`DEFER_XY`** (not padding).

## Lessons Learned (ms01 Blind Sapper)

1. **Movement**: **ACTION1–4** = up / down / left / right (`dy` negative = up), matching `GAMES.md`. Camera **16×16**; smaller boards **letterbox** in the frame.
2. **Hidden mines**: `tags=["mine"]`, **not collidable** — loss is detected by stepping onto a mine cell; the hit mine is **revealed** immediately. **`lose()`** runs only after a short **death animation** (see below).
3. **Mine fail FX + multi-frame action**: On a mine hit, **`complete_action()` is omitted** until the burst finishes so `perform_action` keeps stepping. **`_death_ticks`** counts sub-steps; **`Ms01UI`** draws a **red border pulse + expanding Chebyshev rings + plus** at the blast cell (**64×64** frame coords via `_grid_to_frame_pixel`). One player **step** into a mine can return **8** frames in `frame` — GIF scripts should **append every** layer.
4. **Pathing for GIFs**: **BFS** on walkable cells (bounds, not mine, not wall) from **player** to **goal**; import `levels` from `ms01.py` and read positions from sprites.
5. **Preview GIF**: `uv run python scripts/render_ms01_gif.py` — **BFS** clears **level 1**; **level 2** then **three east** into mine **`GAME_OVER`**; uses **`MS_DEATH_TICK`** for the mine-step sub-frames; **HUD** in `Ms01UI` helps level change read in markdown.

## Lessons Learned (mm01 Memory Match)

1. **Step budget**: **Every** `step()` decrements `_steps_remaining` first (including while waiting for mismatch flip-back). Only **ACTION6** is in `available_actions`; off-grid clicks still burn steps if you need to stall (not used in the preview GIF).
2. **Coords**: Full **64×64** camera — tile hit-test uses `_offset_*` and `_tile_size`; **ACTION6** `x,y` are **frame pixels**. Centers: `offset + col * tile_size + tile_size // 2` (import `LEVEL_LAYOUTS`, `LEVEL_DIMS`, `_compute_tile_size_and_offsets` from `mm01.py` for GIF scripts).
3. **Lose state**: `lose()` sets **`GameState.GAME_OVER`** (not a separate `LOSE` enum).
4. **Preview GIF**: `uv run python scripts/render_mm01_gif.py` — **slow** frame durations; **2–3** deliberate **wrong pairs** (flip-back) across **levels 1–3** via `MISMATCHES_PER_LEVEL`, then scripted clears from `LEVEL_LAYOUTS`; holds after level-ups and at the end.

## Lessons Learned (pb01 / fs01 / tp01 / ic01 / va01 batch)

1. **pb01**: Single **block** + **target** — reuse sk01-style push (next cell block → push if beyond free). **`Pb01UI`** corner tile turns **green** when the crate sits on the goal. **`_sync_ui()`** maps **14/15** when the block enters/leaves the pad; step limit **60 + 15×difficulty**.
2. **fs01**: **Switches** are **non-collidable**; track **`_activated`** as a **set** of `(x, y)` stepped on. When **`len(_activated) == len(_switch_positions)`**, remove **door** sprites. Win only when **`len(_door)==0`** and player stands on **target**. **`Fs01UI`** shows plate progress in the bottom-left.
3. **tp01**: **`portal_pairs`** in **`level.get_data()`** builds **`_portal_to_partner`** (bidirectional). After a normal move onto a portal cell, **`set_position`** to the partner; **one teleport per step** (no loop). Magenta portals (**color 7**), yellow goal.
4. **ic01**: **Slide** in a loop until the **next** cell is out of bounds or **`_blocked`** (wall or hazard). **Targets are walk-through** during the slide; add a **wall** past the goal if you need the player to **stop on** the target cell (e.g. wall at **(1, 0)** under a goal at **(1, 1)** when sliding up).
5. **va01**: **`_open_cells`** = all grid cells with no **wall** sprite; **`_visited`** starts with the player’s start cell. Win when **`_visited == _open_cells`** (set equality). **`Va01UI`** shows remaining cells in the corner.

## Lessons Learned (pb02–va03 variants + nw01–ex01 stems)

### Variants (`xx02` / `xx03` only — cap at `03` unless a plan extends)

1. **pb02**: Two **block** + **target** pairs — same push rules as **pb01** but search over two crates.
2. **pb03**: **Decoy** pad (distinct tag/color); **lose** when a crate is **pushed onto** the decoy (check the cell the block enters).
3. **fs02**: **OR** latches — any one **switch** opens the **door** (not “all plates” like **fs01**).
4. **fs03**: **Sequence** — order is the **sprite list order** of switches in the level data.
5. **tp02**: **`directed_pairs`** `[[[x1,y1],[x2,y2]], …]` — warp **from→to** only (no symmetric return).
6. **tp03**: Remove **both** **`portal`** sprites after one use (`get_sprites_by_tag`, not raw `_sprites`).
7. **ic02**: **Torus** wrap on slide — bound the slide loop (**grid_w×grid_h**) to avoid infinite loops.
8. **ic03**: **`slide_cap`** in **`level.data`** — partial slide each ACTION1–4.
9. **va02**: Coverage set = walkable cells **minus** **`hazard`** tags (cannot “visit” hazard floor).
10. **va03**: **`visit_order`** list — step waypoints **1…N** in order; if the player **starts** on waypoint **1**, advance **`_next`** immediately.

### New two-letter stems (`xx01`)

1. **nw01**: **`arrows`** `(x,y)→(dx,dy)` — entering an arrow cell **stores** a forced move for the **next** ACTION1–4 only.
2. **bd01**: **`_visited`** includes the **start** cell; entering a visited cell **`lose()`**.
3. **gr01**: After a resolved player move, apply **one** gravity step (`gravity` in **`level.data`**).
4. **dt01**: Cyan **waypoint** must be touched before the yellow **goal** (`_hit_waypoint`).
5. **wk01**: On leaving a **`weak`** tile, replace it with a **`hole`** (collidable); stepping into a hole **`lose()`**.
6. **rf01**: For `player.x >= grid_w//2`, negate horizontal **`dx`** (swap left/right semantics).
7. **mo01**: Track **`_dir`** + **`_streak`** — changing direction before **`_streak >= 2`** **`lose()`**.
8. **zq01**: In **`on_set_level`**, remove prior **`zq_hazard`** sprites before re-adding (clean resets). Toggle with **`set_visible` / `set_collidable`**.
9. **hm01**: Win when **`len(_visited) == _need`** where **`_need`** counts all non-wall cells; **revisit** before win **`lose()`**.
10. **ex01**: **`[1,2,3,4,5]`** — **`ACTION5`** only increments hold when **`_on_exit_pad`**; movement resets **`_hold`**. **`hold_frames`** per level in **`level.data`**.

## Lessons Learned (gp01 / lo01 click-first games)

1. **gp01**: **`[1,2,3,4,6]`** — **`ACTION1–4`** are **no-ops** (pacing only). **`ACTION6`** → `camera.display_to_grid(x,y)`; click feedback in **64×64** frame space via **`_grid_to_frame_pixel`** (same letterbox math as **ff01**). Track painted cells with **`paint`** sprites; **`goal_cells`** in **`level.data`**; win when painted set equals goal; dim **`hint`** sprites mark the target cells.
2. **lo01**: Same action list; maintain **`_lit`** and toggle **`+` neighbors** (skip **`wall`**); **`_refresh_lit_sprites`** after each click. Author **grid-corner L-triples** so one **`ACTION6`** on the corner clears that triple without turning on a fourth in-bounds cell.

## Lessons Learned (lw01–bn01 large-grid / mixed-action batch)

1. **lw01**: Store path endpoints in **`level.data["pairs"]`**; keep per-color trails and enforce **no shared cells** across colors; **ACTION6** requires **Manhattan distance 1** from the active path tip.
2. **rp01**: Pulse **BFS** only through **`relay`** tiles from **orthogonal neighbors of `source`**; lamps count lit when **Chebyshev-adjacent** to a **visited relay** (not on the relay cell itself).
3. **ml01**: Laser **raycast** with slash vs backslash mirrors via **`(-dy,-dx)`** vs **`(dy,dx)`**; **ACTION5** = fire only; **ACTION6** places/cycles mirrors on **player-adjacent** cells.
4. **sf01**: **64×64** camera; **3×3 stencil** clamped to grid; **`ACTION5`** paints; win when **`goal <= painted`** (subset); refresh **`paint`** sprites each stamp.
5. **ll01**: **Conway** on full grid; evaluate **`_alive()`** into a **snapshot** before mutating sprites; **lose** on generation **`== need`** if pattern mismatch, or **`>` need**.
6. **wl01**: Tag player-placed tiles **`mywall`** separately from static **`wall`**; **goal** is **non-collidable** — win by **position match** after movement.
7. **dd01**: **`ACTION5`** handles pickup/drop **or** HUD pad ping when idle (no **`ACTION6`**).
8. **ck01**: **Wire connectivity** = BFS from **`in_port`** into **orth-adjacent `wire`** cells until **`out_port`** is reached.
9. **ph01**: Keep numeric phases in **`self._g`**; **`phase_cell`** sprites for display — **skip `mark`** cells so targets stay visible; blur uses **orthogonal** neighbors only.
10. **bn01**: **`hidden`** targets in **`level.data`**; **`ghost`** sprites only when **`(x,y) ∈ revealed`** (union of beacon disks); **wrong `ACTION6` flag** → **`lose()`** immediately.

## Lessons Learned (gp02–hd01 twenty-game batch)

1. **tt02**: When normalizing patrol waypoints from **`level.data`**, use **`[(int(p[0]), int(p[1])) for p in loop]`** — not **`tuple(int(...), int(...))`** (the built-in **`tuple()`** constructor accepts only one iterable argument).
2. **hd01**: **`ACTION5`** charges immunity only on **`station`** cells but must still run the same per-step heat tick and immune decay as movement actions (do not early-return before **`_steps` / `_heat_row`** update).

## Lessons Learned (ACTION6 remediation + 30-game batch)

1. **Non-click ACTION6**: **`dl01`** queue clear → **`ACTION5`**; **`sf01`** stencil paint → **`ACTION5`**; **`sg01`** timing commit → **`ACTION5`**; **`dd01`** pad ping → **`ACTION5`** only.
2. **Click fixes**: **`fl01`** / **`ng01`** path/cell edits use **`camera.display_to_grid`** on **`ACTION6`** with **`action.data` x/y**.
3. **rs03**: Orange **forbidden** targets may remain on the board — win when every **non-forbidden** target is cleared (set equality vs. “empty list”).
4. **Wave-3 ports**: Copied **`xx02`→`xx03`** games need per-plan hooks in code (not only **`GAMES.md`**); **`lo03`** diagonals, **`pt03`** row/col band lock, **`sy03`** horizontal divider + vertical mirror math are the minimal shipped differentiators unless extended later.
