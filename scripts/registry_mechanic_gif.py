"""Showcase GIFs for nw01/bd01/gr01/dt01/wk01/rf01: 1–2 fail beats + reset + multi-level solves."""

from __future__ import annotations

from collections import deque
from pathlib import Path
from typing import Any, Callable

from arcengine import GameAction, GameState, Level

from env_resolve import full_game_id_for_stem, load_stem_game_py
from gif_common import append_frame_repeats, offline_arcade

from registry_gif_lib import _StepAbort, _frame_layer0, safe_env_step

_ACT: dict[int, GameAction] = {
    1: GameAction.ACTION1,
    2: GameAction.ACTION2,
    3: GameAction.ACTION3,
    4: GameAction.ACTION4,
}

# (dx, dy) for new_x = x+dx, new_y = y+dy matching game step()
AD = {1: (0, -1), 2: (0, 1), 3: (-1, 0), 4: (1, 0)}


def _walls_from_level(level: Level) -> set[tuple[int, int]]:
    w: set[tuple[int, int]] = set()
    for s in level.get_sprites():
        if "wall" in s.tags:
            w.add((s.x, s.y))
    return w


def _player_goal(level: Level) -> tuple[tuple[int, int], tuple[int, int]]:
    px = py = None
    gx = gy = None
    for s in level.get_sprites():
        if "player" in s.tags:
            px, py = s.x, s.y
        if "target" in s.tags:
            gx, gy = s.x, s.y
    assert px is not None and gx is not None
    return (px, py), (gx, gy)


def _bfs_simple(
    gw: int,
    gh: int,
    walls: set[tuple[int, int]],
    start: tuple[int, int],
    goal: tuple[int, int],
) -> list[int] | None:
    if start == goal:
        return []
    q: deque[tuple[int, int]] = deque([start])
    prev: dict[tuple[int, int], tuple[tuple[int, int], int] | None] = {start: None}
    while q:
        x, y = q.popleft()
        if (x, y) == goal:
            out: list[int] = []
            cur = (x, y)
            while prev[cur] is not None:
                p, av = prev[cur]
                out.append(av)
                cur = p
            out.reverse()
            return out
        for av, (dx, dy) in AD.items():
            nx, ny = x + dx, y + dy
            if not (0 <= nx < gw and 0 <= ny < gh):
                continue
            if (nx, ny) in walls:
                continue
            if (nx, ny) not in prev:
                prev[(nx, ny)] = ((x, y), av)
                q.append((nx, ny))
    return None


def _bd01_solve_path(
    gw: int,
    gh: int,
    walls: set[tuple[int, int]],
    start: tuple[int, int],
    goal: tuple[int, int],
    max_depth: int = 80,
) -> list[int] | None:
    if start == goal:
        return []
    stack: list[tuple[int, int, frozenset, list[int]]] = [
        (start[0], start[1], frozenset({start}), [])
    ]
    while stack:
        x, y, vis, path = stack.pop()
        if len(path) > max_depth:
            continue
        if (x, y) == goal:
            return path
        for av, (dx, dy) in AD.items():
            nx, ny = x + dx, y + dy
            if not (0 <= nx < gw and 0 <= ny < gh):
                continue
            if (nx, ny) in walls:
                continue
            if (nx, ny) in vis:
                continue
            stack.append((nx, ny, vis | {(nx, ny)}, path + [av]))
    return None


def _gr01_step(
    gw: int,
    gh: int,
    walls: set[tuple[int, int]],
    x: int,
    y: int,
    av: int,
) -> tuple[int, int]:
    dx, dy = AD[av]
    nx, ny = x + dx, y + dy
    if not (0 <= nx < gw and 0 <= ny < gh) or (nx, ny) in walls:
        return x, y
    x, y = nx, ny
    if y + 1 < gh and (x, y + 1) not in walls:
        y += 1
    return x, y


def _gr01_solve(
    gw: int,
    gh: int,
    walls: set[tuple[int, int]],
    start: tuple[int, int],
    goal: tuple[int, int],
) -> list[int] | None:
    q: deque[tuple[int, int]] = deque([start])
    prev: dict[tuple[int, int], tuple[tuple[int, int], int] | None] = {start: None}
    while q:
        x, y = q.popleft()
        if (x, y) == goal:
            out: list[int] = []
            cur = (x, y)
            while prev[cur] is not None:
                p, av = prev[cur]
                out.append(av)
                cur = p
            out.reverse()
            return out
        for av in (1, 2, 3, 4):
            ex, ey = _gr01_step(gw, gh, walls, x, y, av)
            if (ex, ey) not in prev:
                prev[(ex, ey)] = ((x, y), av)
                q.append((ex, ey))
    return None


def _nw01_parse(level: Level) -> tuple[int, int, set[tuple[int, int]], dict, tuple[int, int], tuple[int, int]]:
    gw, gh = level.grid_size
    walls = _walls_from_level(level)
    arrows: dict[tuple[int, int], tuple[int, int]] = {}
    for entry in level.get_data("arrows") or []:
        pos, vec = entry
        arrows[tuple(pos)] = (int(vec[0]), int(vec[1]))
    (px, py), (gx, gy) = _player_goal(level)
    return gw, gh, walls, arrows, (px, py), (gx, gy)


def _nw01_solve(level: Level) -> list[int] | None:
    gw, gh, walls, arrows, start, goal = _nw01_parse(level)
    q: deque[tuple[int, int, tuple[int, int] | None]] = deque()
    q.append((start[0], start[1], None))
    seen: set[tuple[int, int, tuple | str]] = set()

    def sk(x, y, f):
        return (x, y, f if f is not None else "__N__")

    seen.add(sk(start[0], start[1], None))
    prev_map: dict[tuple[int, int, tuple | str], tuple[tuple, int] | None] = {
        sk(start[0], start[1], None): None
    }

    while q:
        x, y, f = q.popleft()
        if (x, y) == goal:
            out: list[int] = []
            cur = sk(x, y, f)
            while prev_map[cur] is not None:
                pr, av = prev_map[cur]  # type: ignore[misc]
                out.append(av)
                cur = pr  # type: ignore[assignment]
            out.reverse()
            return out
        if f is not None:
            dx, dy = f
            nf = None
            nx, ny = x + dx, y + dy
            if not (0 <= nx < gw and 0 <= ny < gh) or (nx, ny) in walls:
                continue
            x2, y2 = nx, ny
            if (x2, y2) in arrows:
                nf = arrows[(x2, y2)]
            nk = sk(x2, y2, nf)
            if nk not in seen:
                seen.add(nk)
                prev_map[nk] = (sk(x, y, f), 1)
                q.append((x2, y2, nf))
        else:
            for av in (1, 2, 3, 4):
                dx, dy = AD[av]
                nx, ny = x + dx, y + dy
                if not (0 <= nx < gw and 0 <= ny < gh) or (nx, ny) in walls:
                    continue
                x2, y2 = nx, ny
                nf = arrows.get((x2, y2))
                nk = sk(x2, y2, nf)
                if nk not in seen:
                    seen.add(nk)
                    prev_map[nk] = (sk(x, y, f), av)
                    q.append((x2, y2, nf))
    return None


def _rf01_solve(level: Level) -> list[int] | None:
    gw, gh = level.grid_size
    walls = _walls_from_level(level)
    (px, py), (gx, gy) = _player_goal(level)
    mid = gw // 2

    def apply_move(x: int, y: int, av: int) -> tuple[int, int]:
        dx, dy = AD[av]
        if x >= mid and dx != 0:
            dx = -dx
        nx, ny = x + dx, y + dy
        if not (0 <= nx < gw and 0 <= ny < gh) or (nx, ny) in walls:
            return x, y
        return nx, ny

    q: deque[tuple[int, int]] = deque([(px, py)])
    prev: dict[tuple[int, int], tuple[tuple[int, int], int] | None] = {(px, py): None}
    while q:
        x, y = q.popleft()
        if (x, y) == (gx, gy):
            out: list[int] = []
            cur = (x, y)
            while prev[cur] is not None:
                p, av = prev[cur]
                out.append(av)
                cur = p
            out.reverse()
            return out
        for av in (1, 2, 3, 4):
            ex, ey = apply_move(x, y, av)
            if (ex, ey) not in prev:
                prev[(ex, ey)] = ((x, y), av)
                q.append((ex, ey))
    return None


def _dt01_parse(level: Level) -> tuple:
    gw, gh = level.grid_size
    walls = _walls_from_level(level)
    wp: set[tuple[int, int]] = set()
    goals: set[tuple[int, int]] = set()
    px = py = None
    for s in level.get_sprites():
        if "player" in s.tags:
            px, py = s.x, s.y
        elif "waypoint" in s.tags:
            wp.add((s.x, s.y))
        elif "target" in s.tags:
            goals.add((s.x, s.y))
    assert px is not None and len(goals) == 1
    gx, gy = next(iter(goals))
    return gw, gh, walls, wp, (px, py), (gx, gy)


def _dt01_entry_vec(level: Level) -> tuple[int, int]:
    raw = level.get_data("waypoint_enter_from") or "w"
    key = str(raw).lower().strip()[:1]
    return {
        "n": (0, 1),
        "s": (0, -1),
        "e": (-1, 0),
        "w": (1, 0),
    }.get(key, (1, 0))


def _dt01_solve(level: Level, require_wp: bool) -> list[int] | None:
    gw, gh, walls, wps, start, goal = _dt01_parse(level)
    req = _dt01_entry_vec(level)
    q: deque[tuple[int, int, bool]] = deque([(start[0], start[1], False)])
    prev: dict[tuple[int, int, bool], tuple[tuple[int, int, bool], int] | None] = {
        (start[0], start[1], False): None
    }
    while q:
        x, y, hit = q.popleft()
        ok_goal = (x, y) == goal and (hit if require_wp else True)
        if ok_goal:
            out: list[int] = []
            cur = (x, y, hit)
            while prev[cur] is not None:
                p, av = prev[cur]
                out.append(av)
                cur = p
            out.reverse()
            return out
        for av, (dx, dy) in AD.items():
            nx, ny = x + dx, y + dy
            if not (0 <= nx < gw and 0 <= ny < gh):
                continue
            if (nx, ny) in walls:
                continue
            nhit = hit
            if (nx, ny) in wps and (dx, dy) == req:
                nhit = True
            st = (nx, ny, nhit)
            if st not in prev:
                prev[st] = ((x, y, hit), av)
                q.append(st)
    return None


def _wk01_parse(level: Level) -> tuple:
    gw, gh = level.grid_size
    walls = _walls_from_level(level)
    weak = set()
    holes = set()
    px = py = gx = gy = None
    for s in level.get_sprites():
        if "player" in s.tags:
            px, py = s.x, s.y
        elif "target" in s.tags:
            gx, gy = s.x, s.y
        elif "weak" in s.tags:
            weak.add((s.x, s.y))
        elif "hole" in s.tags:
            holes.add((s.x, s.y))
    assert px is not None and gx is not None
    return gw, gh, walls, frozenset(weak), frozenset(holes), (px, py), (gx, gy)


def _wk01_step(
    gw: int,
    gh: int,
    walls: set[tuple[int, int]],
    weak: set[tuple[int, int]],
    holes: set[tuple[int, int]],
    x: int,
    y: int,
    av: int,
) -> tuple[int, int, frozenset, frozenset] | None:
    dx, dy = AD[av]
    nx, ny = x + dx, y + dy
    if not (0 <= nx < gw and 0 <= ny < gh):
        return None
    if (nx, ny) in walls:
        return None
    if (nx, ny) in holes:
        return None
    nweak = set(weak)
    nholes = set(holes)
    if (x, y) in nweak:
        nweak.discard((x, y))
        nholes.add((x, y))
    return nx, ny, frozenset(nweak), frozenset(nholes)


def _wk01_solve(level: Level) -> list[int] | None:
    gw, gh, walls, weak0, holes0, start, goal = _wk01_parse(level)
    q: deque[tuple[int, int, frozenset, frozenset]] = deque(
        [(start[0], start[1], weak0, holes0)]
    )
    prev: dict[
        tuple[int, int, frozenset, frozenset],
        tuple[tuple[int, int, frozenset, frozenset], int] | None,
    ] = {(start[0], start[1], weak0, holes0): None}
    while q:
        x, y, wk, ho = q.popleft()
        if (x, y) == goal:
            out: list[int] = []
            cur = (x, y, wk, ho)
            while prev[cur] is not None:
                p, av = prev[cur]
                out.append(av)
                cur = p
            out.reverse()
            return out
        for av in (1, 2, 3, 4):
            nxt = _wk01_step(gw, gh, walls, set(wk), set(ho), x, y, av)
            if nxt is None:
                continue
            nx, ny, nwk, nho = nxt
            key = (nx, ny, nwk, nho)
            if key not in prev:
                prev[key] = ((x, y, wk, ho), av)
                q.append(key)
    return None


def _solve_levels(
    game_id: str,
    mod: Any,
    indices: list[int],
    solver: Callable[[Any], list[int] | None],
) -> list[int]:
    out: list[int] = []
    for i in indices:
        p = solver(mod.levels[i])
        if not p:
            raise RuntimeError(f"{game_id}: no solve for authored level index {i}")
        out.extend(p)
    return out


def _segments_for_stem(game_id: str, mod: Any) -> list[tuple[str, Any]]:
    """Return list of ('moves', [int]) | ('reset',) | ('hold', int)."""
    segs: list[tuple[str, Any]] = [("hold", 6)]
    L3 = [0, 1, 2]

    if game_id == "bd01":
        # Three revisit-loss demos (HUD turns red); **reset** between each (env is GAME_OVER).
        segs.append(("moves", [4, 3]))
        segs.append(("reset",))
        segs.append(("hold", 6))
        segs.append(("moves", [4, 4, 2, 3, 1]))
        segs.append(("reset",))
        segs.append(("hold", 6))
        segs.append(("moves", [2, 1]))
        segs.append(("reset",))
        segs.append(("hold", 8))
        sol = _solve_levels(
            game_id,
            mod,
            L3,
            lambda lev: _bd01_solve_path(
                lev.grid_size[0],
                lev.grid_size[1],
                _walls_from_level(lev),
                _player_goal(lev)[0],
                _player_goal(lev)[1],
            ),
        )
        segs.append(("moves", sol))
        segs.append(("hold", 14))
        return segs

    if game_id == "wk01":
        # Two hole-death demos on L0 (HUD red), **reset** between; then 3-level solve.
        segs.append(("moves", [4, 4, 4, 4, 3]))
        segs.append(("reset",))
        segs.append(("hold", 6))
        # Detour south then approach weak from above; collapse; step into hole.
        segs.append(("moves", [2, 2, 2, 4, 4, 4, 1, 1, 1, 4, 3]))
        segs.append(("reset",))
        segs.append(("hold", 8))
        segs.append(("moves", _solve_levels(game_id, mod, L3, _wk01_solve)))
        segs.append(("hold", 14))
        return segs

    if game_id == "dt01":
        p_goal_first = _dt01_solve(mod.levels[0], False)
        if not p_goal_first:
            raise RuntimeError("dt01: no path to goal without waypoint on L0")
        segs.append(("moves", p_goal_first))
        segs.append(("hold", 12))
        segs.append(("moves", [3, 3, 3, 3, 4, 4, 4, 4]))
        segs.append(("hold", 16))
        segs.append(("reset",))
        segs.append(("hold", 8))
        segs.append(
            (
                "moves",
                _solve_levels(game_id, mod, [0, 1, 2], lambda lev: _dt01_solve(lev, True)),
            )
        )
        segs.append(("hold", 14))
        return segs

    if game_id == "nw01":
        segs.append(("moves", [1, 1, 1]))
        segs.append(("hold", 8))
        segs.append(("moves", [2, 2, 2]))
        segs.append(("hold", 12))
        segs.append(("reset",))
        segs.append(("hold", 8))
        segs.append(("moves", _solve_levels(game_id, mod, L3, _nw01_solve)))
        segs.append(("hold", 14))
        return segs

    if game_id == "gr01":
        # L0: walk into the **walled pocket** (down, down, up jiggle); dead-end BFS → GAME_OVER.
        segs.append(("moves", [2, 2, 1]))
        segs.append(("reset",))
        segs.append(("hold", 8))
        segs.append(
            (
                "moves",
                _solve_levels(
                    game_id,
                    mod,
                    [0, 1, 2],
                    lambda lev: _gr01_solve(
                        lev.grid_size[0],
                        lev.grid_size[1],
                        _walls_from_level(lev),
                        _player_goal(lev)[0],
                        _player_goal(lev)[1],
                    ),
                ),
            )
        )
        segs.append(("hold", 14))
        return segs

    if game_id == "rf01":
        segs.append(("moves", [3, 3, 3]))
        segs.append(("hold", 8))
        segs.append(("moves", [4, 4, 4]))
        segs.append(("hold", 12))
        segs.append(("reset",))
        segs.append(("hold", 8))
        segs.append(("moves", _solve_levels(game_id, mod, [0, 1, 2], _rf01_solve)))
        segs.append(("hold", 14))
        return segs

    raise ValueError(game_id)


def record_mechanic_showcase_gif(
    game_id: str,
    root: Path,
    *,
    overrides: dict[str, Any] | None,
    verbose: bool,
    seed: int,
) -> tuple[Any, list]:
    _ = seed
    o = dict(overrides or {})
    max_gif = int(o.get("max_gif_frames", 900))
    bd01_fail_hold = int(o.get("bd01_fail_hold_frames", 26))
    wk01_fail_hold = int(o.get("wk01_fail_hold_frames", 26))
    gr01_fail_hold = int(o.get("gr01_fail_hold_frames", 26))
    mod = load_stem_game_py(game_id, f"{game_id}_registry_mech")
    segs = _segments_for_stem(game_id, mod)

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
        for seg in segs:
            kind = seg[0]
            if kind == "hold":
                snap_repeats(int(seg[1]))
            elif kind == "reset":
                res = env.reset()
                snap_repeats(8)
            elif kind == "moves":
                for av in seg[1]:
                    res = safe_env_step(env, _ACT[int(av)], reasoning={})
                    snap_repeats(1)
                if game_id == "bd01" and getattr(res, "state", None) == GameState.GAME_OVER:
                    snap_repeats(bd01_fail_hold)
                elif game_id == "wk01" and getattr(res, "state", None) == GameState.GAME_OVER:
                    snap_repeats(wk01_fail_hold)
                elif game_id == "gr01" and getattr(res, "state", None) == GameState.GAME_OVER:
                    snap_repeats(gr01_fail_hold)
    except _StepAbort as ex:
        step_abort = True
        if verbose:
            print(f"  {game_id}: mechanic GIF step abort ({ex})")

    snap_repeats(12)
    if step_abort and not images:
        res = env.reset()
        fr = _frame_layer0(res)
        if fr:
            append_frame_repeats(images, fr[0], 24)

    from registry_gif_lib import _cap_gif_frames

    _cap_gif_frames(images, max_gif)

    if verbose:
        print(
            f"  {game_id}: mechanic showcase GIF, {len(segs)} segments, {len(images)} frames"
        )

    return res, images


MECHANIC_SHOWCASE_STEMS: frozenset[str] = frozenset(
    {"nw01", "bd01", "gr01", "dt01", "wk01", "rf01"}
)
