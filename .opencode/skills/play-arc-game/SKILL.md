# Play ARC Game Skill

Skill for playing and testing ARC-AGI-3 games using `run_game.py`.

## Running Games

(`<stem>` is the two-letter+digits id from `GAMES.md`, e.g. `ez01`. **`--version auto`** picks the sole package dir under `environment_files/<stem>/`.)

### Random-agent mode (default)
Omit **`--mode`** or pass **`--mode random-agent`** — runs **`--steps`** random picks among **ACTION1–ACTION5** (default 100 steps).

```bash
uv run python run_game.py --game <stem> --version auto --mode random-agent --steps 50
```

### Terminal mode (typed 1–7)
```bash
uv run python run_game.py --game <stem> --version auto --mode terminal
```

### Hand-play (pygame window)
Add **`--mode human`** — opens **`scripts/human_play_pygame.py`** (WASD / arrows, click for ACTION6 in display space). There is no separate matplotlib player in this repo.

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

### Click visibility in previews

Put tap/cursor feedback in **`RenderableUserDisplay`** (final **64×64** frame pixels, multi-frame decay). See **`skills/generate-arc-game-gif/SKILL.md`** and **`environment_files/mm01/63be02fb/mm01.py`** (`Mm01UI`).

## Action Mapping

Actions are **abstract** - each game defines what they mean. The canonical mapping is:

- **ACTION1**: Up-like (semantic "forward" for the game)
- **ACTION2**: Down-like (semantic "backward" for the game)
- **ACTION3**: Left-like (semantic "left" for the game)
- **ACTION4**: Right-like (semantic "right" for the game)
- **ACTION5**: Special (game-dependent: interact, select, rotate, etc.)
- **ACTION6**: Click/Coordinate (requires x,y in action.data)
- **ACTION7**: Undo (when the environment supports it)

## Capturing preview GIFs

Use the repo’s **`scripts/render_arc_game_gif.py`** and the **`generate-arc-game-gif`** skill (`skills/generate-arc-game-gif/SKILL.md`, also under `.opencode/skills/` and `.agents/skills/`). Palette helpers live in **`scripts/gif_common.py`**.

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
| Random-agent smoke | `run_game.py --game <stem> --version auto --mode random-agent --steps 100` |
| Check state | `result.state`, `result.levels_completed` |
| Create GIF | `uv run python scripts/render_arc_game_gif.py --stem <stem>` (see **generate-arc-game-gif** skill) |
