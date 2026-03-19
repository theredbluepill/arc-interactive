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
            [1, 2, 3, 4],  # action space: movement actions
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

## What NOT to Do (Based on Old AGENTS.md)

These features are **NOT required** for standard ARC-AGI-3 games:

| Old Documentation Said | Actually |
|----------------------|----------|
| PCG required | Static levels work fine |
| Action scrambling | Not used |
| 10 checkpoints per level | No checkpoints in established games |
| Dynamic grid per episode | Fixed camera size |

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

Actions are **abstract** - each game defines what they mean:

| Action | Description |
|--------|-------------|
| ACTION1 | Abstract action 1 (semantically up) |
| ACTION2 | Abstract action 2 (semantically down) |
| ACTION3 | Abstract action 3 (semantically left) |
| ACTION4 | Abstract action 4 (semantically right) |
| ACTION5 | Special action (interact, select, rotate, attach/detach, execute) |
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
   - Bridges persist (stored in game instance, not level)
   - Check `result.levels_completed` for accurate tracking

5. **Lives system**: When player walks into water:
   - Reset to `_start_position` (not (0,0))
   - Bridges persist across deaths
   - Only call `lose()` when lives reach 0

### tb01 Final Design

- **Grid**: 24x24
- **Player**: 1x1 blue square
- **Islands**: 3x3 maroon squares
- **Goal island**: 3x3 green square
- **Bridges**: 1x1 orange squares (placed ahead of player)
- **Actions**: 1-4 movement, 6=place bridge ahead
- **Lives**: 3 per level

### Bugs Fixed

1. **3x3 player collision**: Originally checked 9 cells, but player only occupies 4 cells
2. **Bridge placement distance**: dist=1 placed bridges too close for player to step off
3. **Level transition**: `next_level()` properly resets player to new level start
