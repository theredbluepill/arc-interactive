"""Shared GIF recording helpers: BFS-to-goal pathing, multi-level capture, recoverable fails."""

from __future__ import annotations

import json
import random
from collections import deque
from pathlib import Path
from typing import Any

from arcengine import GameAction, GameState, Level
from gif_common import (
    append_frame_repeats,
    grid_cell_center_display,
    offline_arcade,
    repo_root,
)


class _StepAbort(Exception):
    """Arcade rejected a step (too many sub-frames or None observation)."""


def safe_env_step(
    env: Any,
    act: GameAction,
    *,
    reasoning: dict | None = None,
    data: dict | None = None,
) -> Any:
    try:
        r = env.step(act, reasoning=reasoning or {}, data=data or {})
    except ValueError as e:
        if "too many frames" in str(e).lower():
            raise _StepAbort(str(e)) from e
        raise
    if r is None:
        raise _StepAbort("env.step returned None")
    return r

DELTA_TO_ACTION: dict[tuple[int, int], GameAction] = {
    (0, -1): GameAction.ACTION1,
    (0, 1): GameAction.ACTION2,
    (-1, 0): GameAction.ACTION3,
    (1, 0): GameAction.ACTION4,
}

GOAL_TAGS = (
    "goal",
    "target",
    "exit",
    "receptor",
    "sink",
    "goal_island",
    "safe_zone",
    "vaccine",
)

GOAL_DATA_KEYS = (
    "goal_island_coords",
    "exit_coords",
)


def goal_positions_set(level: Level) -> set[tuple[int, int]]:
    cells: set[tuple[int, int]] = set()
    for tag in GOAL_TAGS:
        for sp in level.get_sprites_by_tag(tag):
            cells.add((sp.x, sp.y))
    for key in GOAL_DATA_KEYS:
        raw = level.get_data(key)
        if raw:
            cells.update(raw)
    return cells


def walk_blocked(level: Level, x: int, y: int, goals: set[tuple[int, int]]) -> bool:
    if (x, y) in goals:
        return False
    sp = level.get_sprite_at(x, y, ignore_collidable=True)
    if sp is None:
        return False
    tags = set(sp.tags)
    if "mine" in tags:
        return True
    if "hazard" in tags:
        return True
    if sp.is_collidable:
        return True
    return False


def bfs_next_action(
    level: Level,
    start: tuple[int, int],
    goals: set[tuple[int, int]],
) -> GameAction | None:
    w, h = level.grid_size
    if start in goals:
        return None
    q: deque[tuple[int, int]] = deque([start])
    prev: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    found: tuple[int, int] | None = None
    while q:
        x, y = q.popleft()
        if (x, y) in goals:
            found = (x, y)
            break
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nx, ny = x + dx, y + dy
            if not (0 <= nx < w and 0 <= ny < h):
                continue
            if walk_blocked(level, nx, ny, goals):
                continue
            if (nx, ny) not in prev:
                prev[(nx, ny)] = (x, y)
                q.append((nx, ny))
    if found is None:
        return None
    cur = found
    while prev[cur] != start:
        cur = prev[cur]
    dx, dy = cur[0] - start[0], cur[1] - start[1]
    return DELTA_TO_ACTION[(dx, dy)]


def blocked_cardinal_actions(
    level: Level,
    start: tuple[int, int],
    goals: set[tuple[int, int]],
) -> list[GameAction]:
    w, h = level.grid_size
    x, y = start
    out: list[GameAction] = []
    for (dx, dy), act in DELTA_TO_ACTION.items():
        nx, ny = x + dx, y + dy
        if not (0 <= nx < w and 0 <= ny < h):
            out.append(act)
        elif walk_blocked(level, nx, ny, goals):
            out.append(act)
    return out


def _frame_layer0(res: Any) -> list:
    return getattr(res, "frame", None) or []


def load_overrides(root: Path | None = None) -> dict[str, dict[str, Any]]:
    path = (root or repo_root()) / "scripts" / "registry_gif_overrides.json"
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {}
    return data  # type: ignore[return-value]


def inject_wall_fails(
    env: Any,
    res: Any,
    level: Level,
    goals: set[tuple[int, int]],
    snap_repeats,
    *,
    count: int = 2,
) -> Any:
    """Recoverable fails: bump walls / OOB. Repeats one bump if only one blocked side."""
    players = level.get_sprites_by_tag("player")
    if not players:
        return res
    start = (players[0].x, players[0].y)
    blocked = blocked_cardinal_actions(level, start, goals)
    if not blocked:
        return res
    seq: list[GameAction] = []
    for act in blocked:
        if len(seq) >= count:
            break
        seq.append(act)
    while len(seq) < count:
        seq.append(blocked[0])
    for act in seq[:count]:
        res = safe_env_step(env, act, reasoning={})
        snap_repeats(2)
    return res


def maybe_idle_win_defer(
    env: Any,
    res: Any,
    snap_repeats,
    *,
    max_idle: int,
) -> Any:
    """If player is on a goal cell but level has not advanced, burn idle ACTION1."""
    level = env._game.current_level
    goals = goal_positions_set(level)
    players = level.get_sprites_by_tag("player")
    if not players or not goals:
        return res
    pos = (players[0].x, players[0].y)
    if pos not in goals:
        return res
    if bfs_next_action(level, pos, goals) is not None:
        return res
    lc0 = getattr(res, "levels_completed", 0) or 0
    li0 = env._game.level_index
    for _ in range(max_idle):
        res = safe_env_step(env, GameAction.ACTION1, reasoning={})
        snap_repeats(1)
        if (getattr(res, "levels_completed", 0) or 0) > lc0:
            break
        if env._game.level_index != li0:
            break
        if res.state in (GameState.WIN, GameState.GAME_OVER):
            break
    return res


def exploration_burst(
    env: Any,
    res: Any,
    level: Level,
    snap_repeats,
    rng: random.Random,
    *,
    n: int,
) -> Any:
    gw, gh = level.grid_size
    has_player = bool(level.get_sprites_by_tag("player"))
    for _ in range(n):
        r = rng.randint(1, 11)
        if has_player and r <= 8:
            act = (
                GameAction.ACTION1,
                GameAction.ACTION2,
                GameAction.ACTION3,
                GameAction.ACTION4,
            )[rng.randint(0, 3)]
            data: dict[str, int] = {}
        elif r <= 10:
            act = GameAction.ACTION5
            data = {}
        else:
            act = GameAction.ACTION6
            gx = rng.randrange(0, gw)
            gy = rng.randrange(0, gh)
            cx, cy = grid_cell_center_display(gx, gy, grid_w=gw, grid_h=gh)
            data = {"x": cx, "y": cy}
        res = safe_env_step(env, act, reasoning={}, data=data)
        snap_repeats(1)
        if res.state in (GameState.WIN, GameState.GAME_OVER):
            break
    return res


def run_showcase_fallback(env: Any, res: Any, images: list, snap_repeats) -> Any:
    """Mixed ACTION1–6 tour (legacy pending-gifs phase 2). Returns last step result."""
    images.clear()
    res = env.reset()
    fr = _frame_layer0(res)
    if not fr:
        raise RuntimeError("showcase: no frame after reset")
    snap_repeats(8)
    level = env._game.current_level
    gw, gh = level.grid_size
    has_player = bool(level.get_sprites_by_tag("player"))
    for i in range(44):
        data: dict[str, int] = {}
        if has_player:
            phase = i % 7
            if phase < 4:
                act = (
                    GameAction.ACTION1,
                    GameAction.ACTION2,
                    GameAction.ACTION3,
                    GameAction.ACTION4,
                )[phase]
            elif phase == 4:
                act = GameAction.ACTION5
            else:
                act = GameAction.ACTION6
                gx = (i // 2) % gw
                gy = ((i // 2) // gw) % gh
                cx, cy = grid_cell_center_display(gx, gy, grid_w=gw, grid_h=gh)
                data = {"x": cx, "y": cy}
        else:
            act = GameAction.ACTION6
            gx = (i % gw + gw // 2) % gw
            gy = (i * 3 + gh // 2) % gh
            cx, cy = grid_cell_center_display(gx, gy, grid_w=gw, grid_h=gh)
            data = {"x": cx, "y": cy}
        res = safe_env_step(env, act, reasoning={}, data=data)
        snap_repeats(1)
    return res


def _cap_gif_frames(images: list, max_frames: int = 500) -> None:
    if len(images) <= max_frames:
        return
    stride = max(2, (len(images) + max_frames - 1) // max_frames)
    images[:] = images[::stride]


def record_registry_gif(
    game_id: str,
    root: Path,
    *,
    overrides: dict[str, Any] | None = None,
    verbose: bool = False,
    seed: int = 0,
) -> tuple[Any, list]:
    """
    Multi-level GIF frames: per-level wall-bump fails, BFS moves, idle win-defer,
    exploration if stuck. Falls back to showcase if too few frames.
    """
    o = dict(overrides or {})
    target_levels = int(o.get("target_levels", 0))  # 0 = min(3, n_levels)
    max_total_steps = int(o.get("max_total_steps", 1400))
    max_idle = int(o.get("max_idle_between", 28))
    stagnation_trigger = int(o.get("stagnation_steps", 100))
    explore_steps = int(o.get("exploration_burst", 36))
    min_frames = int(o.get("min_frames", 36))

    arc = offline_arcade(root)
    env = arc.make(f"{game_id}-v1", seed=0, render_mode=None)
    res = env.reset()
    rng = random.Random(seed + sum(ord(c) for c in game_id))

    images: list = []

    def snap_repeats(times: int) -> None:
        fr = _frame_layer0(res)
        if fr:
            append_frame_repeats(images, fr[0], times)

    snap_repeats(6)

    n_authored = len(env._game._levels)
    L = target_levels if target_levels > 0 else min(3, max(1, n_authored))

    fail_injected: set[int] = set()
    stagnation = 0
    prev_progress_key: tuple[int, int, tuple[int, int] | None] = (
        -1,
        -1,
        None,
    )

    step_abort = False
    try:
        for _tick in range(max_total_steps):
            if len(images) > 4000:
                break
            if res.state in (GameState.WIN, GameState.GAME_OVER):
                break
            lc = getattr(res, "levels_completed", 0) or 0
            if lc >= L:
                break

            level = env._game.current_level
            li = env._game.level_index
            goals = goal_positions_set(level)
            players = level.get_sprites_by_tag("player")

            pos_key: tuple[int, int] | None = None
            if players:
                pos_key = (players[0].x, players[0].y)
            progress_key = (li, lc, pos_key)
            if progress_key == prev_progress_key:
                stagnation += 1
            else:
                stagnation = 0
                prev_progress_key = progress_key

            if li not in fail_injected:
                res = inject_wall_fails(env, res, level, goals, snap_repeats, count=2)
                fail_injected.add(li)
                stagnation = 0
                prev_progress_key = (-1, -1, None)
                continue

            if stagnation >= stagnation_trigger:
                res = exploration_burst(
                    env, res, level, snap_repeats, rng, n=explore_steps
                )
                stagnation = 0
                prev_progress_key = (-1, -1, None)
                continue

            if not players:
                res = exploration_burst(
                    env, res, level, snap_repeats, rng, n=min(24, explore_steps)
                )
                snap_repeats(1)
                continue

            start = (players[0].x, players[0].y)
            act = bfs_next_action(level, start, goals) if goals else None
            if act is None:
                res = maybe_idle_win_defer(env, res, snap_repeats, max_idle=max_idle)
                res = exploration_burst(
                    env, res, level, snap_repeats, rng, n=min(16, explore_steps // 2)
                )
            else:
                res = safe_env_step(env, act, reasoning={})
                snap_repeats(1)
    except _StepAbort as ex:
        step_abort = True
        if verbose:
            print(f"  {game_id}: step abort ({ex})")

    snap_repeats(8)

    if len(images) < min_frames or step_abort:
        if verbose:
            print(f"  {game_id}: showcase fallback ({len(images)} frames)")
        try:
            res = run_showcase_fallback(env, res, images, snap_repeats)
        except _StepAbort:
            res = env.reset()
            fr = _frame_layer0(res)
            if fr:
                append_frame_repeats(images, fr[0], 24)
        snap_repeats(12)

    max_gif = int(o.get("max_gif_frames", 520))
    _cap_gif_frames(images, max_gif)

    return res, images
