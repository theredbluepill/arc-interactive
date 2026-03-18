# Skill: Create ARC-AGI-3 Game

## Overview
This skill guides the creation of ARC-AGI-3 games based on established patterns from `/Users/poonszesen/redpill/environment_files/`.

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
- `pixels`: 2D array of color values (0-9)
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
        moved = False
        dx = 0
        dy = 0
        
        # Handle actions 1-4 (movement)
        if self.action.id.value == 1:
            dy = -1  # up
            moved = True
        elif self.action.id.value == 2:
            dy = 1   # down
            moved = True
        elif self.action.id.value == 3:
            dx = -1  # left
            moved = True
        elif self.action.id.value == 4:
            dx = 1   # right
            moved = True
        
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
arc = arc_agi.Arcade()
env = arc.make("mygame-v1", seed=0)
result = env.step(1)  # Action 1-4 for movement
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

## Common Patterns

### Color Mapping
- 0: Background (black)
- 1-3: Reserved
- 4: Yellow (targets)
- 5: Gray (walls)
- 6-9: Various entity colors

### Grid Sizes
- Level 1: 8x8 (easy)
- Level 2: 16x16 (medium)
- Level 3: 24x24 (hard)
- Level 4+: 32x32+ (expert)

### Action Space
- ACTION1-4: Primary actions (movement)
- ACTION5: Special action
- ACTION6: Click/interact (if needed)

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

## Examples

See established games:
- `redpill/environment_files/vc33/9851e02b/vc33.py`
- `redpill/environment_files/ls20/cb3b57cc/ls20.py`
- `redpill/environment_files/ft09/9ab2447a/ft09.py`
