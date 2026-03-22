"""Registry GIF recorders for tw01–rv01 batch: planners that generic BFS misses."""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
from pathlib import Path
from typing import Any

from arcengine import GameAction, GameState, Level
from env_resolve import full_game_id_for_stem, load_stem_game_py
from gif_common import append_frame_repeats, offline_arcade
from registry_gif_lib import (
    _cap_gif_frames,
    _frame_layer0,
    _StepAbort,
    goal_positions_set,
    inject_wall_fails,
    safe_env_step,
)

_ACT1 = (GameAction.ACTION1, GameAction.ACTION2, GameAction.ACTION3, GameAction.ACTION4)
_DELTAS = ((0, -1), (0, 1), (-1, 0), (1, 0))


def _is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True


def _bfs_path_grid(
    gw: int,
    gh: int,
    walls: set[tuple[int, int]],
    start: tuple[int, int],
    goal: tuple[int, int],
    *,
    extra_blocked: set[tuple[int, int]] | None = None,
) -> list[GameAction] | None:
    blk = walls | (extra_blocked or set())
    if start == goal:
        return []
    q: deque[tuple[int, int]] = deque([start])
    prev: dict[tuple[int, int], tuple[tuple[int, int], GameAction] | None] = {
        start: None
    }
    while q:
        x, y = q.popleft()
        if (x, y) == goal:
            out: list[GameAction] = []
            cur = (x, y)
            while prev[cur] is not None:
                p, act = prev[cur]
                out.append(act)
                cur = p
            out.reverse()
            return out
        for (dx, dy), act in zip(_DELTAS, _ACT1, strict=True):
            nx, ny = x + dx, y + dy
            if not (0 <= nx < gw and 0 <= ny < gh):
                continue
            if (nx, ny) in blk:
                continue
            if (nx, ny) not in prev:
                prev[(nx, ny)] = ((x, y), act)
                q.append((nx, ny))
    return None


def _walls_from_level(level: Level) -> set[tuple[int, int]]:
    return {(s.x, s.y) for s in level.get_sprites() if "wall" in s.tags}


def _record_planned_multi_level(
    game_id: str,
    root: Path,
    *,
    overrides: dict[str, Any] | None,
    verbose: bool,
    seed: int,
    build_plans: Callable[[list[Level], int], list[list[GameAction]]],
) -> tuple[Any, list]:
    _ = seed
    o = dict(overrides or {})
    target_levels = int(o.get("target_levels", 0))
    max_gif = int(o.get("max_gif_frames", 520))
    level_hold = int(o.get("tw_rv_level_hold_frames", 18))
    fail_hold = int(o.get("tw_rv_fail_hold_frames", 14))

    mod = load_stem_game_py(game_id, f"{game_id}_registry_tw_rv")
    level_defs: list = mod.levels
    n_authored = len(level_defs)
    L = target_levels if target_levels > 0 else min(3, max(1, n_authored))

    plans = build_plans(level_defs, L)
    if len(plans) != L:
        raise RuntimeError(f"{game_id}: build_plans returned {len(plans)} plans, expected {L}")

    arc = offline_arcade(root)
    env = arc.make(full_game_id_for_stem(game_id), seed=0, render_mode=None)
    res = env.reset()
    images: list = []

    def snap_repeats(times: int) -> None:
        fr = _frame_layer0(res)
        if fr:
            append_frame_repeats(images, fr[0], times)

    snap_repeats(8)
    step_abort = False
    try:
        for _li, plan in enumerate(plans):
            level = env._game.current_level
            goals = goal_positions_set(level)
            res = inject_wall_fails(env, res, level, goals, snap_repeats, count=2)
            for act in plan:
                res = safe_env_step(env, act, reasoning={})
                snap_repeats(1)
                if res.state == GameState.GAME_OVER:
                    snap_repeats(fail_hold)
                    break
            snap_repeats(level_hold)
            if env._game.level_index >= L:
                break
            if res.state == GameState.GAME_OVER:
                res = env.reset()
                snap_repeats(6)
    except _StepAbort as ex:
        step_abort = True
        if verbose:
            print(f"  {game_id}: tw_rv GIF step abort ({ex})")

    snap_repeats(10)
    if step_abort and not images:
        res = env.reset()
        fr = _frame_layer0(res)
        if fr:
            append_frame_repeats(images, fr[0], 24)

    _cap_gif_frames(images, max_gif)
    if verbose:
        print(
            f"  {game_id}: tw_rv planned GIF, {L} level(s), "
            f"{sum(len(p) for p in plans)} moves, {len(images)} frames"
        )
    return res, images


# --- tw01: waypoint then goal ---


def _tw01_plans(level_defs: list[Level], L: int) -> list[list[GameAction]]:
    out: list[list[GameAction]] = []
    for i in range(L):
        lv = level_defs[i]
        gw, gh = lv.grid_size
        walls = _walls_from_level(lv)
        pl = lv.get_sprites_by_tag("player")[0]
        way = lv.get_sprites_by_tag("waypoint")[0]
        goal = lv.get_sprites_by_tag("goal")[0]
        start = (pl.x, pl.y)
        wpos = (way.x, way.y)
        gpos = (goal.x, goal.y)
        p1 = _bfs_path_grid(gw, gh, walls, start, wpos)
        p2 = _bfs_path_grid(gw, gh, walls, wpos, gpos)
        if p1 is None or p2 is None:
            raise RuntimeError(f"tw01: level {i} no path")
        out.append(p1 + p2)
    return out


def record_tw01_registry_gif(
    game_id: str,
    root: Path,
    *,
    overrides: dict[str, Any] | None = None,
    verbose: bool = False,
    seed: int = 0,
) -> tuple[Any, list]:
    return _record_planned_multi_level(
        game_id, root, overrides=overrides, verbose=verbose, seed=seed, build_plans=_tw01_plans
    )


# --- cq01: visit all rings then stand on goal ---


def _cq01_plans(level_defs: list[Level], L: int) -> list[list[GameAction]]:
    out: list[list[GameAction]] = []
    for i in range(L):
        lv = level_defs[i]
        gw, gh = lv.grid_size
        walls = _walls_from_level(lv)
        pl = lv.get_sprites_by_tag("player")[0]
        goal = lv.get_sprites_by_tag("goal")[0]
        rings = {(r.x, r.y) for r in lv.get_sprites_by_tag("ring")}
        gpos = (goal.x, goal.y)
        start = (pl.x, pl.y)

        q: deque[tuple[int, int, frozenset[tuple[int, int]]]] = deque(
            [(start[0], start[1], frozenset())]
        )
        prev: dict[
            tuple[int, int, frozenset[tuple[int, int]]],
            tuple[tuple[int, int, frozenset[tuple[int, int]]], GameAction] | None,
        ] = {(start[0], start[1], frozenset()): None}
        found: tuple[int, int, frozenset[tuple[int, int]]] | None = None
        while q:
            x, y, vis = q.popleft()
            if vis == rings and (x, y) == gpos:
                found = (x, y, vis)
                break
            for (dx, dy), act in zip(_DELTAS, _ACT1, strict=True):
                nx, ny = x + dx, y + dy
                if not (0 <= nx < gw and 0 <= ny < gh):
                    continue
                if (nx, ny) in walls:
                    continue
                vis2 = vis | ({(nx, ny)} if (nx, ny) in rings else set())
                key = (nx, ny, frozenset(vis2))
                if key not in prev:
                    prev[key] = ((x, y, vis), act)
                    q.append((nx, ny, frozenset(vis2)))
        if found is None:
            raise RuntimeError(f"cq01: level {i} unsolvable in ring BFS")
        path: list[GameAction] = []
        cur = found
        while prev[cur] is not None:
            p, act = prev[cur]
            path.append(act)
            cur = p
        path.reverse()
        out.append(path)
    return out


def record_cq01_registry_gif(
    game_id: str,
    root: Path,
    *,
    overrides: dict[str, Any] | None = None,
    verbose: bool = False,
    seed: int = 0,
) -> tuple[Any, list]:
    return _record_planned_multi_level(
        game_id, root, overrides=overrides, verbose=verbose, seed=seed, build_plans=_cq01_plans
    )


# --- dv01: position + timeline ---


def _dv01_plans(level_defs: list[Level], L: int) -> list[list[GameAction]]:
    out: list[list[GameAction]] = []
    for i in range(L):
        lv = level_defs[i]
        gw, gh = lv.grid_size
        pl = lv.get_sprites_by_tag("player")[0]
        goal = lv.get_sprites_by_tag("goal")[0]
        gpos = (goal.x, goal.y)
        w0 = {(s.x, s.y) for s in lv.get_sprites_by_tag("wall") if "t0" in s.tags}
        w1 = {(s.x, s.y) for s in lv.get_sprites_by_tag("wall") if "t1" in s.tags}

        def blocked(x: int, y: int, tl: int) -> bool:
            if tl == 0:
                return (x, y) in w0
            return (x, y) in w1

        start = (pl.x, pl.y, 0)
        q: deque[tuple[int, int, int]] = deque([start])
        prev: dict[tuple[int, int, int], tuple[tuple[int, int, int], GameAction] | None] = {
            start: None
        }
        found: tuple[int, int, int] | None = None
        while q:
            x, y, tl = q.popleft()
            if (x, y) == gpos:
                found = (x, y, tl)
                break
            # toggle
            nt = 1 - tl
            key_t = (x, y, nt)
            if key_t not in prev:
                prev[key_t] = ((x, y, tl), GameAction.ACTION5)
                q.append(key_t)
            for (dx, dy), act in zip(_DELTAS, _ACT1, strict=True):
                nx, ny = x + dx, y + dy
                if not (0 <= nx < gw and 0 <= ny < gh):
                    continue
                if blocked(nx, ny, tl):
                    continue
                key = (nx, ny, tl)
                if key not in prev:
                    prev[key] = ((x, y, tl), act)
                    q.append(key)
        if found is None:
            raise RuntimeError(f"dv01: level {i} unsolvable")
        path: list[GameAction] = []
        cur = found
        while prev[cur] is not None:
            p, act = prev[cur]
            path.append(act)
            cur = p
        path.reverse()
        out.append(path)
    return out


def record_dv01_registry_gif(
    game_id: str,
    root: Path,
    *,
    overrides: dict[str, Any] | None = None,
    verbose: bool = False,
    seed: int = 0,
) -> tuple[Any, list]:
    return _record_planned_multi_level(
        game_id, root, overrides=overrides, verbose=verbose, seed=seed, build_plans=_dv01_plans
    )


# --- ox01: (x, y, phase) — phase flips every step ---


def _ox01_plans(level_defs: list[Level], L: int) -> list[list[GameAction]]:
    out: list[list[GameAction]] = []
    for i in range(L):
        lv = level_defs[i]
        gw, gh = lv.grid_size
        pl = lv.get_sprites_by_tag("player")[0]
        goal = lv.get_sprites_by_tag("goal")[0]
        ha = {(s.x, s.y) for s in lv.get_sprites_by_tag("haz_a")}
        hb = {(s.x, s.y) for s in lv.get_sprites_by_tag("haz_b")}
        gpos = (goal.x, goal.y)
        start_a = True  # matches on_set_level _active_a = True

        def collides(cx: int, cy: int, active_a: bool) -> bool:
            if (cx, cy) in ha:
                return active_a
            if (cx, cy) in hb:
                return not active_a
            return False

        def lethal(x: int, y: int, phase_a: bool) -> bool:
            return collides(x, y, phase_a)

        start = (pl.x, pl.y, start_a)
        q: deque[tuple[int, int, bool]] = deque([start])
        prev: dict[tuple[int, int, bool], tuple[tuple[int, int, bool], GameAction] | None] = {
            start: None
        }
        found: tuple[int, int, bool] | None = None
        while q:
            x, y, a = q.popleft()
            if (x, y) == gpos:
                found = (x, y, a)
                break
            for (dx, dy), act in zip(_DELTAS, _ACT1, strict=True):
                nx, ny = x + dx, y + dy
                na = not a
                if 0 <= nx < gw and 0 <= ny < gh and not collides(nx, ny, a):
                    px, py = nx, ny
                else:
                    px, py = x, y
                if lethal(px, py, na):
                    continue
                key = (px, py, na)
                if key not in prev:
                    prev[key] = ((x, y, a), act)
                    q.append(key)
        if found is None:
            raise RuntimeError(f"ox01: level {i} unsolvable")
        path: list[GameAction] = []
        cur = found
        while prev[cur] is not None:
            p, act = prev[cur]
            path.append(act)
            cur = p
        path.reverse()
        out.append(path)
    return out


def record_ox01_registry_gif(
    game_id: str,
    root: Path,
    *,
    overrides: dict[str, Any] | None = None,
    verbose: bool = False,
    seed: int = 0,
) -> tuple[Any, list]:
    return _record_planned_multi_level(
        game_id, root, overrides=overrides, verbose=verbose, seed=seed, build_plans=_ox01_plans
    )


# --- sl01: 8-puzzle state BFS ---


def _sl01_encode_state(level: Level) -> tuple[int, ...]:
    gw, gh = level.grid_size
    hole = level.get_sprites_by_tag("player")[0]
    cells: list[int] = []
    for y in range(gh):
        for x in range(gw):
            if hole.x == x and hole.y == y:
                cells.append(0)
                continue
            sp = level.get_sprite_at(x, y, ignore_collidable=True)
            tid = 0
            if sp and "tile" in sp.tags:
                for t in sp.tags:
                    if t.isdigit():
                        tid = int(t)
                        break
            cells.append(tid)
    return tuple(cells)


def _sl01_goal_tuple(goal: list[list[int]]) -> tuple[int, ...]:
    out: list[int] = []
    for row in goal:
        out.extend(int(c) for c in row)
    return tuple(out)


def _sl01_plans(level_defs: list[Level], L: int) -> list[list[GameAction]]:
    out: list[list[GameAction]] = []
    for i in range(L):
        lv = level_defs[i]
        gw, gh = lv.grid_size
        want = _sl01_goal_tuple(lv.get_data("goal") or [])
        start = _sl01_encode_state(lv)
        if start == want:
            out.append([])
            continue

        q: deque[tuple[int, ...]] = deque([start])
        prev: dict[tuple[int, ...], tuple[tuple[int, ...], GameAction] | None] = {start: None}

        def idx(x: int, y: int) -> int:
            return y * gw + x

        def neighbors(st: tuple[int, ...]) -> list[tuple[GameAction, tuple[int, ...]]]:
            zi = st.index(0)
            hx, hy = zi % gw, zi // gw
            res: list[tuple[GameAction, tuple[int, ...]]] = []
            # ACTION1 up: swap hole with tile above (hx, hy-1)
            if hy > 0:
                li = idx(hx, hy - 1)
                ns = list(st)
                ns[zi], ns[li] = ns[li], ns[zi]
                res.append((GameAction.ACTION1, tuple(ns)))
            # ACTION2 down
            if hy < gh - 1:
                li = idx(hx, hy + 1)
                ns = list(st)
                ns[zi], ns[li] = ns[li], ns[zi]
                res.append((GameAction.ACTION2, tuple(ns)))
            # ACTION3 left
            if hx > 0:
                li = idx(hx - 1, hy)
                ns = list(st)
                ns[zi], ns[li] = ns[li], ns[zi]
                res.append((GameAction.ACTION3, tuple(ns)))
            # ACTION4 right
            if hx < gw - 1:
                li = idx(hx + 1, hy)
                ns = list(st)
                ns[zi], ns[li] = ns[li], ns[zi]
                res.append((GameAction.ACTION4, tuple(ns)))
            return res

        found: tuple[int, ...] | None = None
        while q:
            cur = q.popleft()
            if cur == want:
                found = cur
                break
            for act, nxt in neighbors(cur):
                if nxt not in prev:
                    prev[nxt] = (cur, act)
                    q.append(nxt)
        if found is None:
            raise RuntimeError(f"sl01: level {i} unsolvable")
        path: list[GameAction] = []
        cur = found
        while prev[cur] is not None:
            p, act = prev[cur]
            path.append(act)
            cur = p
        path.reverse()
        out.append(path)
    return out


def record_sl01_registry_gif(
    game_id: str,
    root: Path,
    *,
    overrides: dict[str, Any] | None = None,
    verbose: bool = False,
    seed: int = 0,
) -> tuple[Any, list]:
    return _record_planned_multi_level(
        game_id, root, overrides=overrides, verbose=verbose, seed=seed, build_plans=_sl01_plans
    )


# --- lf01: laser row + tick ---


def _lf01_plans(level_defs: list[Level], L: int) -> list[list[GameAction]]:
    out: list[list[GameAction]] = []
    for i in range(L):
        lv = level_defs[i]
        gw, gh = lv.grid_size
        walls = _walls_from_level(lv)
        pl = lv.get_sprites_by_tag("player")[0]
        goal = lv.get_sprites_by_tag("goal")[0]
        P = int(lv.get_data("period") or 3)
        row = int(lv.get_data("laser_row") or 5)
        gpos = (goal.x, goal.y)

        def laser_on(tick: int) -> bool:
            return (tick // P) % 2 == 0

        start = (pl.x, pl.y, 0)
        q: deque[tuple[int, int, int]] = deque([start])
        prev: dict[tuple[int, int, int], tuple[tuple[int, int, int], GameAction] | None] = {
            start: None
        }
        found: tuple[int, int, int] | None = None
        while q:
            x, y, t = q.popleft()
            if (x, y) == gpos:
                found = (x, y, t)
                break
            for (dx, dy), act in zip(_DELTAS, _ACT1, strict=True):
                nx, ny = x + dx, y + dy
                if 0 <= nx < gw and 0 <= ny < gh and (nx, ny) not in walls:
                    px, py = nx, ny
                else:
                    px, py = x, y
                if laser_on(t) and py == row:
                    continue
                nt = t + 1
                key = (px, py, nt)
                if key not in prev:
                    prev[key] = ((x, y, t), act)
                    q.append(key)
        if found is None:
            raise RuntimeError(f"lf01: level {i} unsolvable")
        path: list[GameAction] = []
        cur = found
        while prev[cur] is not None:
            p, act = prev[cur]
            path.append(act)
            cur = p
        path.reverse()
        out.append(path)
    return out


def record_lf01_registry_gif(
    game_id: str,
    root: Path,
    *,
    overrides: dict[str, Any] | None = None,
    verbose: bool = False,
    seed: int = 0,
) -> tuple[Any, list]:
    return _record_planned_multi_level(
        game_id, root, overrides=overrides, verbose=verbose, seed=seed, build_plans=_lf01_plans
    )


# --- pm01: step index + prime moves ---


def _pm01_plans(level_defs: list[Level], L: int) -> list[list[GameAction]]:
    out: list[list[GameAction]] = []
    for i in range(L):
        lv = level_defs[i]
        gw, gh = lv.grid_size
        walls = _walls_from_level(lv)
        pl = lv.get_sprites_by_tag("player")[0]
        goal = lv.get_sprites_by_tag("goal")[0]
        gpos = (goal.x, goal.y)
        start = (pl.x, pl.y, 0)
        q: deque[tuple[int, int, int]] = deque([start])
        prev: dict[tuple[int, int, int], tuple[tuple[int, int, int], GameAction] | None] = {
            start: None
        }
        found: tuple[int, int, int] | None = None
        while q:
            x, y, si = q.popleft()
            if (x, y) == gpos:
                found = (x, y, si)
                break
            for (dx, dy), act in zip(_DELTAS, _ACT1, strict=True):
                nsi = si + 1
                if _is_prime(nsi):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < gw and 0 <= ny < gh and (nx, ny) not in walls:
                        px, py = nx, ny
                    else:
                        px, py = x, y
                else:
                    px, py = x, y
                key = (px, py, nsi)
                if key not in prev:
                    prev[key] = ((x, y, si), act)
                    q.append(key)
        if found is None:
            raise RuntimeError(f"pm01: level {i} unsolvable")
        path: list[GameAction] = []
        cur = found
        while prev[cur] is not None:
            p, act = prev[cur]
            path.append(act)
            cur = p
        path.reverse()
        out.append(path)
    return out


def record_pm01_registry_gif(
    game_id: str,
    root: Path,
    *,
    overrides: dict[str, Any] | None = None,
    verbose: bool = False,
    seed: int = 0,
) -> tuple[Any, list]:
    return _record_planned_multi_level(
        game_id, root, overrides=overrides, verbose=verbose, seed=seed, build_plans=_pm01_plans
    )


# --- hz01: hazards spread ---


def _hz01_spread(
    gw: int,
    gh: int,
    walls: set[tuple[int, int]],
    goal: tuple[int, int],
    haz: frozenset[tuple[int, int]],
) -> frozenset[tuple[int, int]]:
    newp: set[tuple[int, int]] = set()
    for hx, hy in haz:
        for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            nx, ny = hx + dx, hy + dy
            if not (0 <= nx < gw and 0 <= ny < gh):
                continue
            if (nx, ny) in walls or (nx, ny) == goal:
                continue
            if (nx, ny) in haz:
                continue
            newp.add((nx, ny))
    return frozenset(haz | newp)


def _hz01_plans(level_defs: list[Level], L: int) -> list[list[GameAction]]:
    out: list[list[GameAction]] = []
    for i in range(L):
        lv = level_defs[i]
        gw, gh = lv.grid_size
        walls = _walls_from_level(lv)
        pl = lv.get_sprites_by_tag("player")[0]
        goal = lv.get_sprites_by_tag("goal")[0]
        gpos = (goal.x, goal.y)
        M = int(lv.get_data("spread_m") or 4)
        haz0 = frozenset((h.x, h.y) for h in lv.get_sprites_by_tag("hazard"))
        start = (pl.x, pl.y, 0, haz0)
        q: deque[tuple[int, int, int, frozenset[tuple[int, int]]]] = deque([start])
        prev: dict[
            tuple[int, int, int, frozenset[tuple[int, int]]],
            tuple[tuple[int, int, int, frozenset[tuple[int, int]]], GameAction] | None,
        ] = {start: None}
        found: tuple[int, int, int, frozenset[tuple[int, int]]] | None = None
        cap = 250_000
        steps = 0
        while q:
            steps += 1
            if steps > cap:
                break
            x, y, ctr, hz = q.popleft()
            if (x, y) == gpos:
                found = (x, y, ctr, hz)
                break
            if (x, y) in hz:
                continue
            for (dx, dy), act in zip(_DELTAS, _ACT1, strict=True):
                nx, ny = x + dx, y + dy
                if 0 <= nx < gw and 0 <= ny < gh and (nx, ny) not in walls and (nx, ny) not in hz:
                    px, py = nx, ny
                else:
                    px, py = x, y
                if (px, py) in hz:
                    continue
                ctr2 = ctr + 1
                hz2 = hz
                if ctr2 >= M:
                    ctr2 = 0
                    hz2 = _hz01_spread(gw, gh, walls, gpos, hz)
                if (px, py) in hz2:
                    continue
                key = (px, py, ctr2, hz2)
                if key not in prev:
                    prev[key] = ((x, y, ctr, hz), act)
                    q.append(key)
        if found is None:
            raise RuntimeError(f"hz01: level {i} unsolvable")
        path: list[GameAction] = []
        cur = found
        while prev[cur] is not None:
            p, act = prev[cur]
            path.append(act)
            cur = p
        path.reverse()
        out.append(path)
    return out


def record_hz01_registry_gif(
    game_id: str,
    root: Path,
    *,
    overrides: dict[str, Any] | None = None,
    verbose: bool = False,
    seed: int = 0,
) -> tuple[Any, list]:
    return _record_planned_multi_level(
        game_id, root, overrides=overrides, verbose=verbose, seed=seed, build_plans=_hz01_plans
    )


# --- sb01: sand fall ---


def _sb01_blocked(
    gw: int,
    gh: int,
    walls: set[tuple[int, int]],
    sand: set[tuple[int, int]],
    x: int,
    y: int,
    ignore: tuple[int, int] | None,
) -> bool:
    if not (0 <= x < gw and 0 <= y < gh):
        return True
    if (x, y) in walls:
        return True
    if (x, y) in sand and (ignore is None or (x, y) != ignore):
        return True
    return False


def _sb01_fall(gw: int, gh: int, walls: set[tuple[int, int]], sand: set[tuple[int, int]]) -> None:
    changed = True
    while changed:
        changed = False
        for cell in list(sand):
            x, y = cell
            ny = y + 1
            if not _sb01_blocked(gw, gh, walls, sand, x, ny, cell):
                sand.remove(cell)
                sand.add((x, ny))
                changed = True


def _sb01_plans(level_defs: list[Level], L: int) -> list[list[GameAction]]:
    out: list[list[GameAction]] = []
    for i in range(L):
        lv = level_defs[i]
        gw, gh = lv.grid_size
        walls = _walls_from_level(lv)
        pl = lv.get_sprites_by_tag("player")[0]
        goal = lv.get_sprites_by_tag("goal")[0]
        gpos = (goal.x, goal.y)
        sand0 = frozenset((s.x, s.y) for s in lv.get_sprites_by_tag("sand"))
        start = (pl.x, pl.y, sand0)
        q: deque[tuple[int, int, frozenset[tuple[int, int]]]] = deque([start])
        prev: dict[
            tuple[int, int, frozenset[tuple[int, int]]],
            tuple[tuple[int, int, frozenset[tuple[int, int]]], GameAction] | None,
        ] = {start: None}
        found: tuple[int, int, frozenset[tuple[int, int]]] | None = None
        cap = 200_000
        it = 0
        while q:
            it += 1
            if it > cap:
                break
            x, y, sd = q.popleft()
            if (x, y) == gpos:
                found = (x, y, sd)
                break
            sand_m = set(sd)
            if (x, y) in sand_m:
                continue
            for (dx, dy), act in zip(_DELTAS, _ACT1, strict=True):
                nx, ny = x + dx, y + dy
                if not (0 <= nx < gw and 0 <= ny < gh):
                    continue
                if (nx, ny) in walls:
                    continue
                if (nx, ny) in sand_m:
                    continue
                sand2 = set(sand_m)
                px, py = nx, ny
                _sb01_fall(gw, gh, walls, sand2)
                if (px, py) in sand2:
                    continue
                key = (px, py, frozenset(sand2))
                if key not in prev:
                    prev[key] = ((x, y, sd), act)
                    q.append(key)
        if found is None:
            raise RuntimeError(f"sb01: level {i} unsolvable")
        path: list[GameAction] = []
        cur = found
        while prev[cur] is not None:
            p, act = prev[cur]
            path.append(act)
            cur = p
        path.reverse()
        out.append(path)
    return out


def record_sb01_registry_gif(
    game_id: str,
    root: Path,
    *,
    overrides: dict[str, Any] | None = None,
    verbose: bool = False,
    seed: int = 0,
) -> tuple[Any, list]:
    return _record_planned_multi_level(
        game_id, root, overrides=overrides, verbose=verbose, seed=seed, build_plans=_sb01_plans
    )

