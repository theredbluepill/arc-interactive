"""Registry GIF recorders for mo01 (momentum), zq01 (timed hazards), hm01 (Hamiltonian tour).

Generic registry BFS cannot model these win/physics rules; this module plans scripted moves,
includes fail beats + ``env.reset()``, then multi-level clears.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from arcengine import GameAction, GameState, Level

from env_resolve import full_game_id_for_stem, load_stem_game_py
from gif_common import append_frame_repeats, offline_arcade
from registry_gif_lib import DELTA_TO_ACTION, _StepAbort, _cap_gif_frames, safe_env_step

A1, A2, A3, A4 = (
    GameAction.ACTION1,
    GameAction.ACTION2,
    GameAction.ACTION3,
    GameAction.ACTION4,
)


def _mo01_wall_set(level: Level) -> set[tuple[int, int]]:
    return {(s.x, s.y) for s in level.get_sprites() if "wall" in s.tags}


def _mo01_goals(level: Level) -> set[tuple[int, int]]:
    return {(s.x, s.y) for s in level.get_sprites_by_tag("target")}


def mo01_momentum_plan(level: Level) -> list[GameAction] | None:
    """Shortest legal momentum path onto a target cell."""
    gw, gh = level.grid_size
    walls = _mo01_wall_set(level)
    targets = _mo01_goals(level)
    px = level.get_sprites_by_tag("player")[0].x
    py = level.get_sprites_by_tag("player")[0].y
    start = (px, py, 0, 0, 0)  # x,y, fdx, fdy, streak_clamped (0=start)

    def walkable(nx: int, ny: int) -> bool:
        if not (0 <= nx < gw and 0 <= ny < gh):
            return False
        if (nx, ny) in walls:
            return False
        return True

    from collections import deque

    q: deque[tuple[int, int, int, int, int]] = deque([start])
    prev: dict[tuple[int, int, int, int, int], tuple[tuple[int, int, int, int, int], GameAction] | None] = {  # noqa: E501
        start: None
    }
    found: tuple[int, int, int, int, int] | None = None
    while q:
        x, y, fdx, fdy, sc = q.popleft()
        if (x, y) in targets and (x, y) != (px, py):
            found = (x, y, fdx, fdy, sc)
            break
        cand: list[tuple[int, int, int, int, int, GameAction]] = []
        for (dx, dy), act in DELTA_TO_ACTION.items():
            nx, ny = x + dx, y + dy
            if not walkable(nx, ny):
                continue
            if sc == 0:
                cand.append((nx, ny, dx, dy, 1, act))
            elif (dx, dy) == (fdx, fdy):
                nsc = 2 if sc + 1 >= 2 else sc + 1
                cand.append((nx, ny, fdx, fdy, nsc, act))
            elif sc >= 2:
                cand.append((nx, ny, dx, dy, 1, act))
        for nx, ny, ndx, ndy, nsc, act in cand:
            nxt = (nx, ny, ndx, ndy, nsc)
            if nxt not in prev:
                prev[nxt] = ((x, y, fdx, fdy, sc), act)
                q.append(nxt)
    if found is None:
        return None
    path: list[GameAction] = []
    cur = found
    while prev[cur] is not None:
        p, act = prev[cur]
        path.append(act)
        cur = p
    path.reverse()
    return path


def _zq_hazard_phase(tick_after_step: int, period: int) -> bool:
    """``tick_after_step`` = game ``_ticks`` after that many ``step()`` calls."""
    if tick_after_step <= 0:
        return False
    return (tick_after_step // period) % 2 == 1


def zq01_timed_plan(level: Level, *, max_tick: int = 96) -> list[GameAction] | None:
    """
    Plan moves where each step advances time. Blocked moves (wall / active hazard) still
    advance ``_ticks`` without moving — matches ``zq01.py``.
    """
    gw, gh = level.grid_size
    walls = {(s.x, s.y) for s in level.get_sprites() if "wall" in s.tags}
    targets = {(s.x, s.y) for s in level.get_sprites_by_tag("target")}
    hz = {tuple(p) for p in (level.get_data("hazard_cells") or [])}
    period = int(level.get_data("period") or 5)
    px = level.get_sprites_by_tag("player")[0].x
    py = level.get_sprites_by_tag("player")[0].y

    from collections import deque

    # ``Arcade.reset()`` leaves ``_ticks == 1`` before the first scripted ``step()``.
    start = (px, py, 1)
    parent: dict[tuple[int, int, int], tuple[int, int, int] | None] = {start: None}
    move_from: dict[tuple[int, int, int], GameAction] = {}
    q: deque[tuple[int, int, int]] = deque([start])
    goal_state: tuple[int, int, int] | None = None
    while q:
        x, y, t = q.popleft()
        if (x, y) in targets:
            goal_state = (x, y, t)
            break
        nt = t + 1
        if nt > max_tick:
            continue
        hazard = _zq_hazard_phase(nt, period)
        for (dx, dy), act in DELTA_TO_ACTION.items():
            nx, ny = x + dx, y + dy
            blocked = (
                not (0 <= nx < gw and 0 <= ny < gh)
                or (nx, ny) in walls
                or (hazard and (nx, ny) in hz)
            )
            ax, ay = (x, y) if blocked else (nx, ny)
            nxt = (ax, ay, nt)
            if nxt not in parent:
                parent[nxt] = (x, y, t)
                move_from[nxt] = act
                q.append(nxt)
    if goal_state is None:
        return None
    path_rev: list[GameAction] = []
    cur: tuple[int, int, int] | None = goal_state
    while cur is not None and cur != start:
        path_rev.append(move_from[cur])
        cur = parent[cur]
    path_rev.reverse()
    return path_rev


def _hm01_open_cells(level: Level) -> set[tuple[int, int]]:
    gw, gh = level.grid_size
    walls = {(s.x, s.y) for s in level.get_sprites() if "wall" in s.tags}
    return {(x, y) for y in range(gh) for x in range(gw) if (x, y) not in walls}


def hm01_hamiltonian_plan(level: Level) -> list[GameAction] | None:
    """Warnsdorff-style backtracking Hamiltonian path from player onto all open cells."""
    open_cells = _hm01_open_cells(level)
    start = (
        level.get_sprites_by_tag("player")[0].x,
        level.get_sprites_by_tag("player")[0].y,
    )
    if start not in open_cells:
        return None
    need = len(open_cells)

    def neighbors(p: tuple[int, int]) -> list[tuple[int, int]]:
        x, y = p
        out: list[tuple[int, int]] = []
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            q = (x + dx, y + dy)
            if q in open_cells:
                out.append(q)
        return out

    path: list[tuple[int, int]] = []
    visited: set[tuple[int, int]] = set()

    def unvisited_degree(u: tuple[int, int]) -> int:
        return sum(1 for w in neighbors(u) if w not in visited)

    def dfs(v: tuple[int, int]) -> bool:
        path.append(v)
        visited.add(v)
        if len(visited) == need:
            return True
        cand = [u for u in neighbors(v) if u not in visited]
        cand.sort(key=unvisited_degree)
        for u in cand:
            if dfs(u):
                return True
        path.pop()
        visited.remove(v)
        return False

    if not dfs(start):
        return None
    actions: list[GameAction] = []
    for i in range(len(path) - 1):
        x, y = path[i]
        nx, ny = path[i + 1]
        dx, dy = nx - x, ny - y
        actions.append(DELTA_TO_ACTION[(dx, dy)])
    return actions


def record_mo01_registry_gif(
    game_id: str,
    root: Path,
    *,
    overrides: dict[str, Any] | None,
    verbose: bool,
    seed: int,
) -> tuple[Any, list]:
    _ = seed
    o = dict(overrides or {})
    max_gif = int(o.get("max_gif_frames", 520))
    L = int(o.get("target_levels", 0)) or min(4, len(load_stem_game_py(game_id, "mo01_reg").levels))
    level_defs = load_stem_game_py(game_id, "mo01_reg").levels[: max(1, L)]

    arc = offline_arcade(root)
    env = arc.make(full_game_id_for_stem(game_id), seed=0, render_mode=None)
    res = env.reset()
    images: list = []

    def snap_repeats(times: int) -> None:
        fr = getattr(res, "frame", None) or []
        if fr:
            append_frame_repeats(images, fr[0], times)

    snap_repeats(8)

    def step_one(act: GameAction, repeat: int = 1) -> None:
        nonlocal res
        res = safe_env_step(env, act, reasoning={})
        snap_repeats(repeat)

    step_abort = False
    try:
        # Fail: early direction change (streak 1 -> lose).
        step_one(A4)
        step_one(A2)
        snap_repeats(14)
        if res.state != GameState.GAME_OVER:
            raise RuntimeError("mo01: expected GAME_OVER on early turn")

        res = env.reset()
        snap_repeats(10)

        for li, lv_def in enumerate(level_defs):
            plan = mo01_momentum_plan(lv_def)
            if plan is None:
                raise RuntimeError(f"mo01: no plan for registry level {li}")
            if env._game.level_index != li:
                raise RuntimeError("mo01: level_index drift")
            for a in plan:
                step_one(a)
            snap_repeats(12 if li < len(level_defs) - 1 else 10)
            lc = getattr(res, "levels_completed", 0) or 0
            if li < len(level_defs) - 1 and lc != li + 1:
                raise RuntimeError(f"mo01: expected {li+1} levels_completed after L{li+1}, got {lc}")
        if (getattr(res, "levels_completed", 0) or 0) < len(level_defs):
            raise RuntimeError(
                f"mo01: incomplete run ({getattr(res, 'levels_completed', 0)!r} / {len(level_defs)})"
            )
    except _StepAbort as ex:
        step_abort = True
        if verbose:
            print(f"  {game_id}: mo01 step abort ({ex})")

    snap_repeats(8)
    if step_abort and not images:
        res = env.reset()
        fr = getattr(res, "frame", None) or []
        if fr:
            append_frame_repeats(images, fr[0], 24)
    _cap_gif_frames(images, max_gif)
    if verbose:
        print(f"  {game_id}: momentum GIF, {len(images)} frames")
    return res, images


def record_zq01_registry_gif(
    game_id: str,
    root: Path,
    *,
    overrides: dict[str, Any] | None,
    verbose: bool,
    seed: int,
) -> tuple[Any, list]:
    _ = seed
    o = dict(overrides or {})
    max_gif = int(o.get("max_gif_frames", 520))
    L = int(o.get("target_levels", 0)) or min(4, len(load_stem_game_py(game_id, "zq01_reg").levels))
    level_defs = load_stem_game_py(game_id, "zq01_reg").levels[: max(1, L)]

    arc = offline_arcade(root)
    env = arc.make(full_game_id_for_stem(game_id), seed=0, render_mode=None)
    res = env.reset()
    images: list = []

    def snap_repeats(times: int) -> None:
        fr = getattr(res, "frame", None) or []
        if fr:
            append_frame_repeats(images, fr[0], times)

    snap_repeats(8)

    def step_one(act: GameAction, repeat: int = 1) -> None:
        nonlocal res
        res = safe_env_step(env, act, reasoning={})
        snap_repeats(repeat)

    step_abort = False
    try:
        # Fail beats on L1 (period 5): OOB bumps, then approach (3,3) and bump active hazard at x=4.
        step_one(A1, 2)
        step_one(A3, 2)
        for _ in range(3):
            step_one(A4, 1)
        step_one(A4, 2)
        snap_repeats(10)

        res = env.reset()
        snap_repeats(10)

        for li, lv_def in enumerate(level_defs):
            if env._game.level_index != li:
                raise RuntimeError("zq01: level_index drift")
            plan = zq01_timed_plan(lv_def, max_tick=160)
            if plan is None:
                raise RuntimeError(f"zq01: no timed plan for level {li}")
            for a in plan:
                step_one(a, 1)
            snap_repeats(12 if li < len(level_defs) - 1 else 10)
            lc = getattr(res, "levels_completed", 0) or 0
            if li < len(level_defs) - 1 and lc != li + 1:
                raise RuntimeError(f"zq01: after L{li+1} expected lc={li+1}, got {lc}")
    except _StepAbort as ex:
        step_abort = True
        if verbose:
            print(f"  {game_id}: zq01 step abort ({ex})")

    snap_repeats(10)
    if step_abort and not images:
        res = env.reset()
        fr = getattr(res, "frame", None) or []
        if fr:
            append_frame_repeats(images, fr[0], 24)
    _cap_gif_frames(images, max_gif)
    if verbose:
        print(f"  {game_id}: zone-timer GIF, {len(images)} frames")
    return res, images


def record_hm01_registry_gif(
    game_id: str,
    root: Path,
    *,
    overrides: dict[str, Any] | None,
    verbose: bool,
    seed: int,
) -> tuple[Any, list]:
    _ = seed
    o = dict(overrides or {})
    max_gif = int(o.get("max_gif_frames", 520))
    L = int(o.get("target_levels", 0)) or min(4, len(load_stem_game_py(game_id, "hm01_reg").levels))
    level_defs = load_stem_game_py(game_id, "hm01_reg").levels[: max(1, L)]

    arc = offline_arcade(root)
    env = arc.make(full_game_id_for_stem(game_id), seed=0, render_mode=None)
    res = env.reset()
    images: list = []

    def snap_repeats(times: int) -> None:
        fr = getattr(res, "frame", None) or []
        if fr:
            append_frame_repeats(images, fr[0], times)

    snap_repeats(8)

    def step_one(act: GameAction, repeat: int = 1) -> None:
        nonlocal res
        res = safe_env_step(env, act, reasoning={})
        snap_repeats(repeat)

    step_abort = False
    try:
        # Fail: revisiting start on 3×3 empty grid.
        step_one(A4)
        step_one(A2)
        step_one(A3)
        step_one(A1)
        snap_repeats(14)
        if res.state != GameState.GAME_OVER:
            raise RuntimeError("hm01: expected GAME_OVER on revisit")

        res = env.reset()
        snap_repeats(10)

        for li, lv_def in enumerate(level_defs):
            plan = hm01_hamiltonian_plan(lv_def)
            if plan is None:
                raise RuntimeError(f"hm01: no Hamiltonian plan for level {li}")
            if env._game.level_index != li:
                raise RuntimeError("hm01: level_index drift")
            for a in plan:
                step_one(a, 1)
            snap_repeats(12 if li < len(level_defs) - 1 else 10)
            lc = getattr(res, "levels_completed", 0) or 0
            if li < len(level_defs) - 1 and lc != li + 1:
                raise RuntimeError(f"hm01: expected lc={li+1} after L{li+1}, got {lc}")
    except _StepAbort as ex:
        step_abort = True
        if verbose:
            print(f"  {game_id}: hm01 step abort ({ex})")

    snap_repeats(10)
    if step_abort and not images:
        res = env.reset()
        fr = getattr(res, "frame", None) or []
        if fr:
            append_frame_repeats(images, fr[0], 24)
    _cap_gif_frames(images, max_gif)
    if verbose:
        print(f"  {game_id}: Hamiltonian GIF, {len(images)} frames")
    return res, images
