# Skill: Create ARC-AGI-3 Game

## Overview
This skill guides the creation of ARC-AGI-3 games with Procedural Content Generation (PCG) support for training DreamerV3 agents.

## Game Structure

```
environment_files/{game_id}/{version}/
├── {game_id}.py          # Main game file
└── metadata.json         # Game metadata
```

## Required Components

### 1. Imports
```python
import random
import numpy as np
from arcengine import (
    ActionInput,
    ARCBaseGame,
    Camera,
    GameAction,
    Level,
    Sprite,
)
```

### 2. Sprite Definitions
Define sprites with:
- `pixels`: 2D array of color values (0-9)
- `name`: Unique identifier
- `visible`: Boolean for rendering
- `collidable`: Boolean for collision detection
- `tags`: List for categorization
- `layer`: Optional rendering layer

### 3. PCG Implementation

#### State Randomization
```python
# Grid topology randomization
grid_size = (rng.randint(8, 32), rng.randint(8, 32))

# Entity randomization
entity_count = rng.randint(3, 10)
for i in range(entity_count):
    x = rng.randint(0, grid_size[0] - 1)
    y = rng.randint(0, grid_size[1] - 1)
    color = rng.choice([4, 5, 6, 7, 8, 9])
```

#### Action Randomization
Map actions randomly each episode:
```python
# ACTION1-4 for movement, scrambled per episode
action_map = {
    GameAction.ACTION1: possible_actions[rng.randint(0, 3)],  # up/down/left/right
    GameAction.ACTION2: possible_actions[rng.randint(0, 3)],
    # ...
}
```

#### Transition Dynamics
Implement physics rules:
- Collision: push, collect, bounce, destroy
- Proximity: merge, transform when adjacent
- Global: gravity, wrap-around, time limits

### 4. Game Class Structure

```python
class Co01(ARCBaseGame):
    def __init__(self, seed: int = 0) -> None:
        self._rng = random.Random(seed)
        # Initialize action mapping
        self._scramble_actions()
        # Setup camera and levels
        camera = Camera(background=0, letter_box=4, width=8, height=8)
        super().__init__(game_id="co01", levels=levels, camera=camera)
    
    def _scramble_actions(self):
        """Randomize action meanings for this episode."""
        pass
    
    def on_set_level(self, level: Level) -> None:
        """Generate procedural content when level loads."""
        self._generate_level_content()
    
    def step(self) -> None:
        """Process actions with scrambled mapping."""
        # Handle action based on scrambled mapping
        # Check win conditions
        # Advance level if complete
        self.complete_action()
```

### 5. Sparse Rewards (Checkpoints)

Implement 10 checkpoints per level:
- Spatial: Reach coordinate (x, y)
- State: Collect N targets
- Survival: Avoid hazards for N steps

```python
def _check_checkpoints(self):
    """Check and reward milestone achievements."""
    for checkpoint in self.current_level._data.get("checkpoints", []):
        if checkpoint["type"] == "spatial":
            # Check if player at target position
            pass
        elif checkpoint["type"] == "collection":
            # Check target count
            pass
```

### 6. Win Condition

```python
def _check_win(self) -> bool:
    """Check if all targets collected/win condition met."""
    return len(self._targets) == 0
```

## Testing

Run with:
```python
import arc_agi
arc = arc_agi.Arcade()
env = arc.make("co01-v1", seed=0, render_mode="terminal")

# Test with scrambled actions
env.step(GameAction.ACTION1)  # May be up, down, left, or right
```

## Metadata Requirements

```json
{
  "game_id": "co01-v1",
  "title": "Collection Game",
  "default_fps": 20,
  "baseline_actions": [10, 15, 25],
  "tags": ["pcg", "meta-learning"],
  "local_dir": "environment_files/co01/v1"
}
```

## Training Integration

For DreamerV3 training:
1. Wrap in Gymnasium interface
2. Generate millions of episodes
3. Record (State, Action, Next State) sequences
4. Include prediction error as intrinsic reward

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
- ACTION1-4: Primary actions (movement/tools)
- ACTION5: Special action
- ACTION6: Click/interact (if needed)

## Critical Implementation Details

### Level Data Access
**Use `self.current_level._data` (with underscore), NOT `self.current_level.data`**
```python
def on_set_level(self, level: Level) -> None:
    difficulty = self.current_level._data.get("difficulty", 1)  # CORRECT
    # NOT: self.current_level.data.get("difficulty", 1)  # WRONG - AttributeError
```

### Sprite Management
**Level does NOT have `get_sprite_with_tag()` method.** Store sprite references as instance variables:
```python
class MyGame(ARCBaseGame):
    def __init__(self, seed: int = 0) -> None:
        self._player_sprite = None  # Store reference here
        # ... other init
    
    def on_set_level(self, level: Level) -> None:
        # Clear existing sprites before regenerating
        self.current_level._sprites = []
        
        # Create and store player sprite
        self._player_sprite = sprites["player"].clone().set_position(x, y)
        self.current_level.add_sprite(self._player_sprite)
    
    def step(self) -> None:
        # Move player by updating BOTH position and sprite
        self._player_pos = (new_x, new_y)
        if self._player_sprite:
            self._player_sprite.set_position(new_x, new_y)
```

### Camera Dimensions
Camera width/height should match the actual grid size for proper rendering:
```python
def __init__(self, seed: int = 0) -> None:
    # Get level dimensions from first level
    grid_w, grid_h = levels[0].grid_size
    camera = Camera(
        background=BACKGROUND_COLOR,
        letter_box=PADDING_COLOR,
        width=grid_w,   # Match grid, don't hardcode
        height=grid_h,  # Match grid, don't hardcode
    )
```

### Environment step() Return Value
**`env.step()` returns a single result object, NOT a tuple like Gymnasium.**
```python
# CORRECT:
result = env.step(action)

# WRONG - this will cause unpacking errors:
obs, reward, terminated, truncated, info = env.step(action)
```

### Clearing Sprites Between Episodes
Always clear the sprites list in `on_set_level()` before regenerating:
```python
def on_set_level(self, level: Level) -> None:
    """Called when level is set or reset."""
    # Clear existing sprites to prevent duplicates
    self.current_level._sprites = []
    
    # Now generate new procedural content
    self._generate_level_content()
```

## Best Practices

1. **Seeded Randomness**: Always use `random.Random(seed)` for reproducibility
2. **Action Scrambling**: Remap actions every `reset()` call
3. **Progressive Difficulty**: Increase complexity with level number
4. **Sparse Rewards**: Only give reward at checkpoints, not every step
5. **Visual Diversity**: Randomize colors and patterns
6. **Physics Variety**: Change collision rules between episodes

## Examples

See existing game:
- `environment_files/co01/v1/co01.py` (PCG example with movement)
