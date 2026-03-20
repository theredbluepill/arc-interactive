"""Shared GIF recording helpers: BFS-to-goal pathing, multi-level capture, recoverable fails."""

from __future__ import annotations

import json
import random
from collections import deque
from pathlib import Path
from typing import Any, Literal

from arcengine import GameAction, GameState, Level
from env_resolve import full_game_id_for_stem, load_stem_game_py
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

# Classic Sokoban (blocks onto targets). Generic ``goal_positions_set`` BFS walks the
# player to *target cells* and never pushes crates — registry GIFs looked "stuck" on L1.
PUSH_SOLVER_STEMS: frozenset[str] = frozenset({"pb01", "pb02", "sk01", "sk02"})

_PUSH_DELTAS: tuple[tuple[int, int, int], ...] = (
    (-1, 0, 1),
    (1, 0, 2),
    (0, -1, 3),
    (0, 1, 4),
)

_PUSH_ACTION: dict[int, GameAction] = {
    1: GameAction.ACTION1,
    2: GameAction.ACTION2,
    3: GameAction.ACTION3,
    4: GameAction.ACTION4,
}

# Floor-switch + door + goal: generic BFS walks to the green target while ``target`` is
# treated as walk-through in ``walk_blocked``, so the recorder never learns to open doors.
SWITCH_DOOR_MODE: dict[str, str] = {
    "fs01": "all",
    "fs02": "or",
    "fs03": "k_of_n",
}


def _parse_floor_switch_level(
    level: Level,
) -> tuple[
    set[tuple[int, int]],
    set[tuple[int, int]],
    list[tuple[int, int]],
    frozenset[tuple[int, int]],
    set[tuple[int, int]],
    tuple[int, int],
    int,
    int,
]:
    walls: set[tuple[int, int]] = set()
    doors: set[tuple[int, int]] = set()
    switches_ordered: list[tuple[int, int]] = []
    targets: set[tuple[int, int]] = set()
    player: tuple[int, int] | None = None
    gw, gh = level.grid_size
    for s in level.get_sprites():
        tgs = s.tags
        p = (s.x, s.y)
        if "player" in tgs:
            player = p
        elif "wall" in tgs:
            walls.add(p)
        elif "door" in tgs:
            doors.add(p)
        elif "switch" in tgs:
            switches_ordered.append(p)
        elif "target" in tgs:
            targets.add(p)
    if player is None:
        raise ValueError("floor-switch parse: no player")
    switch_set = frozenset(switches_ordered)
    return walls, doors, switches_ordered, switch_set, targets, player, gw, gh


def switch_door_plan(
    level: Level, mode: str, *, max_nodes: int = 2_000_000
) -> list[int] | None:
    """BFS on (pos, latch state) until standing on a target with the door logically open."""
    walls, doors, switches_ordered, switch_set, targets, (px, py), gw, gh = (
        _parse_floor_switch_level(level)
    )
    if not targets or not switches_ordered:
        return None

    if mode == "all":
        full = switch_set

        def blocked(x: int, y: int, extra: frozenset[tuple[int, int]]) -> bool:
            if (x, y) in walls:
                return True
            if (x, y) in doors and len(extra) < len(full):
                return True
            return False

        def step_extra(nx: int, ny: int, extra: frozenset[tuple[int, int]]):
            if (nx, ny) in full:
                return frozenset(extra | {(nx, ny)})
            return extra

        start = (px, py, frozenset())
        goal_fn = lambda sx, sy, ex: (sx, sy) in targets and ex == full
    elif mode == "or":

        def blocked(x: int, y: int, opened: bool) -> bool:
            if (x, y) in walls:
                return True
            if (x, y) in doors and not opened:
                return True
            return False

        def step_extra(nx: int, ny: int, opened: bool) -> bool:
            return opened or (nx, ny) in switch_set

        start = (px, py, False)
        goal_fn = lambda sx, sy, op: (sx, sy) in targets and op
    elif mode == "k_of_n":
        raw_k = level.get_data("required_plates")
        if raw_k is None:
            k_need = len(switches_ordered)
        else:
            k_need = int(raw_k)
        n_sw = len(switches_ordered)
        k_need = max(1, min(k_need, n_sw)) if n_sw else 1

        def blocked(x: int, y: int, extra: frozenset[tuple[int, int]]) -> bool:
            if (x, y) in walls:
                return True
            if (x, y) in doors and len(extra) < k_need:
                return True
            return False

        def step_extra(nx: int, ny: int, extra: frozenset[tuple[int, int]]):
            if (nx, ny) in switch_set:
                return frozenset(extra | {(nx, ny)})
            return extra

        start = (px, py, frozenset())
        goal_fn = lambda sx, sy, ex: (sx, sy) in targets and len(ex) >= k_need
    else:
        raise ValueError(f"unknown switch-door mode {mode!r}")

    q: deque[Any] = deque([start])
    came: dict[Any, tuple[Any, int] | None] = {start: None}
    nodes = 0
    while q:
        nodes += 1
        if nodes > max_nodes:
            return None
        state = q.popleft()
        sx, sy = state[0], state[1]
        extra = state[2]
        if goal_fn(sx, sy, extra):
            path: list[int] = []
            cur = state
            while came[cur] is not None:
                prev, act = came[cur]
                path.append(act)
                cur = prev
            path.reverse()
            return path
        for dy, dx, act in _PUSH_DELTAS:
            nx, ny = sx + dx, sy + dy
            if not (0 <= nx < gw and 0 <= ny < gh):
                continue
            ex = extra
            if not blocked(nx, ny, ex):
                nex = step_extra(nx, ny, ex)
                nxt = (nx, ny, nex)
                if nxt not in came:
                    came[nxt] = (state, act)
                    q.append(nxt)
    return None


def _record_switch_door_gif(
    game_id: str,
    root: Path,
    *,
    overrides: dict[str, Any] | None,
    verbose: bool,
    seed: int,
) -> tuple[Any, list]:
    _ = seed
    mode = SWITCH_DOOR_MODE[game_id]
    o = dict(overrides or {})
    target_levels = int(o.get("target_levels", 0))
    max_gif = int(o.get("max_gif_frames", 520))
    level_hold = int(o.get("switch_level_hold_frames", 18))
    # OR mode: pause on the frame the door opens so HUD (all slots → green) reads clearly.
    or_door_open_hold = int(o.get("switch_or_door_open_hold_frames", 0))

    mod = load_stem_game_py(game_id, f"{game_id}_registry_switch")
    level_defs: list = mod.levels
    n_authored = len(level_defs)
    L = (
        target_levels
        if target_levels > 0
        else min(5, max(1, n_authored))
    )

    plans: list[list[int]] = []
    for i in range(L):
        p = switch_door_plan(level_defs[i], mode)
        if p is None:
            raise RuntimeError(
                f"{game_id}: level {i} has no switch-door solution for registry GIF"
            )
        plans.append(p)

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
        for plan in plans:
            for av in plan:
                g = env._game
                door_before = len(getattr(g, "_door", []) or [])
                res = safe_env_step(env, _PUSH_ACTION[av], reasoning={})
                snap_repeats(1)
                if (
                    mode == "or"
                    and or_door_open_hold > 0
                    and door_before > 0
                    and len(getattr(env._game, "_door", []) or []) == 0
                ):
                    snap_repeats(or_door_open_hold)
            snap_repeats(level_hold)
    except _StepAbort as ex:
        step_abort = True
        if verbose:
            print(f"  {game_id}: switch-door GIF step abort ({ex})")

    snap_repeats(10)
    if step_abort and not images:
        res = env.reset()
        fr = _frame_layer0(res)
        if fr:
            append_frame_repeats(images, fr[0], 24)

    _cap_gif_frames(images, max_gif)

    if verbose:
        moves = sum(len(p) for p in plans)
        print(
            f"  {game_id}: switch-door ({mode}) GIF, {L} levels, {moves} moves, {len(images)} frames"
        )

    return res, images


# Portal-aware previews: generic registry BFS does not model warps, so tp02/tp03 used
# to look like duplicate “shuffle near portals” GIFs unless routed here.
PORTAL_PAIR_STEMS: frozenset[str] = frozenset({"tp01", "tp02", "tp03"})


def _parse_portal_geometry(
    level: Level,
) -> tuple[set[tuple[int, int]], set[tuple[int, int]], tuple[int, int], int, int]:
    walls: set[tuple[int, int]] = set()
    targets: set[tuple[int, int]] = set()
    player: tuple[int, int] | None = None
    gw, gh = level.grid_size
    for s in level.get_sprites():
        p = (s.x, s.y)
        tgs = s.tags
        if "player" in tgs:
            player = p
        elif "wall" in tgs:
            walls.add(p)
        elif "target" in tgs:
            targets.add(p)
    if player is None:
        raise ValueError("portal parse: no player")
    return walls, targets, player, gw, gh


def _parse_symmetric_portal_level(
    level: Level,
) -> tuple[
    set[tuple[int, int]],
    set[tuple[int, int]],
    tuple[int, int],
    dict[tuple[int, int], tuple[int, int]],
    int,
    int,
]:
    walls, targets, player, gw, gh = _parse_portal_geometry(level)
    pmap: dict[tuple[int, int], tuple[int, int]] = {}
    for a, b in level.get_data("portal_pairs") or []:
        ta, tb = tuple(a), tuple(b)
        pmap[ta] = tb
        pmap[tb] = ta
    return walls, targets, player, pmap, gw, gh


def symmetric_portal_plan(
    level: Level, *, max_nodes: int = 500_000
) -> list[int] | None:
    """Shortest path on grid; stepping onto a portal cell jumps to its partner."""
    walls, targets, start, pmap, gw, gh = _parse_symmetric_portal_level(level)
    if not targets or not pmap:
        return None
    q: deque[tuple[int, int]] = deque([start])
    came: dict[tuple[int, int], tuple[tuple[int, int], int] | None] = {start: None}
    nodes = 0
    while q:
        nodes += 1
        if nodes > max_nodes:
            return None
        x, y = q.popleft()
        if (x, y) in targets:
            path: list[int] = []
            cur = (x, y)
            while came[cur] is not None:
                prev, act = came[cur]
                path.append(act)
                cur = prev
            path.reverse()
            return path
        for dy, dx, act in _PUSH_DELTAS:
            nx, ny = x + dx, y + dy
            if not (0 <= nx < gw and 0 <= ny < gh):
                continue
            if (nx, ny) in walls:
                continue
            if (nx, ny) in pmap:
                nx, ny = pmap[(nx, ny)]
            nxt = (nx, ny)
            if nxt not in came:
                came[nxt] = ((x, y), act)
                q.append(nxt)
    return None


def directed_portal_plan(
    level: Level, *, max_nodes: int = 500_000
) -> list[int] | None:
    """tp02: ``directed_pairs`` only warp from the first cell to the second (one way)."""
    walls, targets, start, gw, gh = _parse_portal_geometry(level)
    dmap: dict[tuple[int, int], tuple[int, int]] = {}
    for a, b in level.get_data("directed_pairs") or []:
        dmap[tuple(a)] = tuple(b)
    if not targets:
        return None
    q: deque[tuple[int, int]] = deque([start])
    came: dict[tuple[int, int], tuple[tuple[int, int], int] | None] = {start: None}
    nodes = 0
    while q:
        nodes += 1
        if nodes > max_nodes:
            return None
        x, y = q.popleft()
        if (x, y) in targets:
            path: list[int] = []
            cur = (x, y)
            while came[cur] is not None:
                prev, act = came[cur]
                path.append(act)
                cur = prev
            path.reverse()
            return path
        for dy, dx, act in _PUSH_DELTAS:
            nx, ny = x + dx, y + dy
            if not (0 <= nx < gw and 0 <= ny < gh):
                continue
            if (nx, ny) in walls:
                continue
            if (nx, ny) in dmap:
                nx, ny = dmap[(nx, ny)]
            nxt = (nx, ny)
            if nxt not in came:
                came[nxt] = ((x, y), act)
                q.append(nxt)
    return None


def single_use_portal_plan(
    level: Level, *, max_nodes: int = 500_000
) -> list[int] | None:
    """tp03: symmetric ``portal_pairs``, but each pair works once then both ends are floor."""
    walls, targets, start, gw, gh = _parse_portal_geometry(level)
    pairs: list[tuple[tuple[int, int], tuple[int, int]]] = [
        (tuple(a), tuple(b)) for a, b in (level.get_data("portal_pairs") or [])
    ]
    if not targets:
        return None
    n = len(pairs)
    start_key = (start, frozenset(range(n)))
    q: deque[tuple[tuple[int, int], frozenset[int]]] = deque([start_key])
    came: dict[
        tuple[tuple[int, int], frozenset[int]],
        tuple[tuple[tuple[int, int], frozenset[int]], int] | None,
    ] = {start_key: None}
    nodes = 0
    while q:
        nodes += 1
        if nodes > max_nodes:
            return None
        pos, active = q.popleft()
        x, y = pos
        if pos in targets:
            path: list[int] = []
            cur: tuple[tuple[int, int], frozenset[int]] = (pos, active)
            while came[cur] is not None:
                prev, act = came[cur]
                path.append(act)
                cur = prev
            path.reverse()
            return path
        for dy, dx, act in _PUSH_DELTAS:
            nx, ny = x + dx, y + dy
            if not (0 <= nx < gw and 0 <= ny < gh):
                continue
            if (nx, ny) in walls:
                continue
            npos = (nx, ny)
            active2 = active
            for i in active:
                a, b = pairs[i]
                if npos == a:
                    npos = b
                    active2 = frozenset(j for j in active if j != i)
                    break
                if npos == b:
                    npos = a
                    active2 = frozenset(j for j in active if j != i)
                    break
            nk = (npos, active2)
            if nk not in came:
                came[nk] = (((x, y), active), act)
                q.append(nk)
    return None


def _record_portal_pair_gif(
    game_id: str,
    root: Path,
    *,
    overrides: dict[str, Any] | None,
    verbose: bool,
    seed: int,
) -> tuple[Any, list]:
    _ = seed
    o = dict(overrides or {})
    target_levels = int(o.get("target_levels", 0))
    max_gif = int(o.get("max_gif_frames", 520))
    level_hold = int(o.get("portal_level_hold_frames", 16))

    mod = load_stem_game_py(game_id, f"{game_id}_registry_portal")
    level_defs: list = mod.levels
    n_authored = len(level_defs)
    L = (
        target_levels
        if target_levels > 0
        else min(5, max(1, n_authored))
    )

    if game_id == "tp01":
        plan_fn = symmetric_portal_plan
    elif game_id == "tp02":
        plan_fn = directed_portal_plan
    elif game_id == "tp03":
        plan_fn = single_use_portal_plan
    else:
        raise ValueError(f"{game_id}: unknown portal GIF stem")

    plans: list[list[int]] = []
    for i in range(L):
        p = plan_fn(level_defs[i])
        if p is None:
            raise RuntimeError(
                f"{game_id}: level {i} has no portal-plan solution for registry GIF"
            )
        plans.append(p)

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
        for plan in plans:
            for av in plan:
                res = safe_env_step(env, _PUSH_ACTION[av], reasoning={})
                snap_repeats(1)
            snap_repeats(level_hold)
    except _StepAbort as ex:
        step_abort = True
        if verbose:
            print(f"  {game_id}: portal GIF step abort ({ex})")

    snap_repeats(10)
    if step_abort and not images:
        res = env.reset()
        fr = _frame_layer0(res)
        if fr:
            append_frame_repeats(images, fr[0], 24)

    _cap_gif_frames(images, max_gif)

    if verbose:
        moves = sum(len(p) for p in plans)
        print(
            f"  {game_id}: portal GIF ({plan_fn.__name__}), {L} levels, {moves} moves, {len(images)} frames"
        )

    return res, images


# Ice slide variants: one action = slide with stem-specific physics; generic BFS is wrong.
ICE_SLIDE_STEMS: frozenset[str] = frozenset({"ic01", "ic02", "ic03"})


def _parse_ice_slide_level(
    level: Level,
) -> tuple[int, int, set[tuple[int, int]], set[tuple[int, int]], tuple[int, int]]:
    gw, gh = level.grid_size
    blocked: set[tuple[int, int]] = set()
    targets: set[tuple[int, int]] = set()
    player: tuple[int, int] | None = None
    for s in level.get_sprites():
        p = (s.x, s.y)
        tgs = s.tags
        if "player" in tgs:
            player = p
        elif "wall" in tgs or "hazard" in tgs:
            blocked.add(p)
        elif "target" in tgs:
            targets.add(p)
    if player is None:
        raise ValueError("ice slide parse: no player")
    return gw, gh, blocked, targets, player


def _ice_slide_end(
    gw: int,
    gh: int,
    blocked: set[tuple[int, int]],
    px: int,
    py: int,
    dx: int,
    dy: int,
) -> tuple[int, int]:
    while True:
        nx, ny = px + dx, py + dy
        if not (0 <= nx < gw and 0 <= ny < gh):
            break
        if (nx, ny) in blocked:
            break
        px, py = nx, ny
    return (px, py)


def _ice_slide_end_torus(
    gw: int,
    gh: int,
    blocked: set[tuple[int, int]],
    px: int,
    py: int,
    dx: int,
    dy: int,
) -> tuple[int, int]:
    """Stop cell after one slide; matches ic02.step (wrap at edges, cap gw*gh steps)."""
    for _ in range(gw * gh):
        nx = px + dx
        ny = py + dy
        if nx < 0:
            nx = gw - 1
        elif nx >= gw:
            nx = 0
        if ny < 0:
            ny = gh - 1
        elif ny >= gh:
            ny = 0
        if (nx, ny) in blocked:
            break
        px, py = nx, ny
    return (px, py)


def _ice_slide_end_capped(
    gw: int,
    gh: int,
    blocked: set[tuple[int, int]],
    px: int,
    py: int,
    dx: int,
    dy: int,
    cap: int,
) -> tuple[int, int]:
    """Stop cell after one move; matches ic03.step (at most ``cap`` cells)."""
    steps = 0
    k = max(1, cap)
    while steps < k:
        nx, ny = px + dx, py + dy
        if not (0 <= nx < gw and 0 <= ny < gh):
            break
        if (nx, ny) in blocked:
            break
        px, py = nx, ny
        steps += 1
    return (px, py)


def ice_slide_plan(
    level: Level,
    *,
    max_nodes: int = 10_000,
    slide_start: tuple[int, int] | None = None,
    physics: Literal["bounded", "torus", "capped"] = "bounded",
    slide_cap: int | None = None,
) -> list[int] | None:
    """BFS over stop positions; edges are one cardinal slide (physics per stem)."""
    gw, gh, blocked, targets, authored_start = _parse_ice_slide_level(level)
    if not targets:
        return None
    cap = (
        slide_cap
        if slide_cap is not None
        else int(level.get_data("slide_cap") or 3)
    )
    start = slide_start if slide_start is not None else authored_start
    if start in targets:
        return []
    q: deque[tuple[int, int]] = deque([start])
    prev: dict[tuple[int, int], tuple[tuple[int, int], int] | None] = {start: None}
    nodes = 0
    while q:
        nodes += 1
        if nodes > max_nodes:
            return None
        x, y = q.popleft()
        if (x, y) in targets:
            out: list[int] = []
            cur = (x, y)
            while prev[cur] is not None:
                p, act = prev[cur]
                out.append(act)
                cur = p
            out.reverse()
            return out
        for dy, dx, act in _PUSH_DELTAS:
            if physics == "bounded":
                ex, ey = _ice_slide_end(gw, gh, blocked, x, y, dx, dy)
            elif physics == "torus":
                ex, ey = _ice_slide_end_torus(gw, gh, blocked, x, y, dx, dy)
            else:
                ex, ey = _ice_slide_end_capped(
                    gw, gh, blocked, x, y, dx, dy, cap
                )
            if (ex, ey) not in prev:
                prev[(ex, ey)] = ((x, y), act)
                q.append((ex, ey))
    return None


def ic01_showcase_plan(level: Level, *, max_nodes: int = 10_000) -> list[int] | None:
    """
    Preview GIF: optional “failed” beats before the optimal solve — up to two no-move
    slides (hit edge/wall immediately), then one wrong-direction slide if needed, then solve.
    """
    gw, gh, blocked, targets, level_start = _parse_ice_slide_level(level)
    if not targets:
        return None

    bumps: list[int] = []
    for dy, dx, act in _PUSH_DELTAS:
        if len(bumps) >= 2:
            break
        ex, ey = _ice_slide_end(gw, gh, blocked, level_start[0], level_start[1], dx, dy)
        if (ex, ey) == level_start:
            bumps.append(act)

    pos = level_start
    prefix: list[int] = list(bumps)

    if len(bumps) < 2:
        optimal = ice_slide_plan(level, max_nodes=max_nodes, slide_start=pos)
        if optimal is None:
            return None
        if optimal:
            good_first = optimal[0]
            for dy, dx, act in _PUSH_DELTAS:
                if act == good_first:
                    continue
                ex, ey = _ice_slide_end(gw, gh, blocked, pos[0], pos[1], dx, dy)
                if (ex, ey) == pos:
                    continue
                tail = ice_slide_plan(level, max_nodes=max_nodes, slide_start=(ex, ey))
                if tail is not None:
                    prefix.append(act)
                    pos = (ex, ey)
                    break

    main = ice_slide_plan(level, max_nodes=max_nodes, slide_start=pos)
    if main is None:
        return None
    return prefix + main


def _record_ice_slide_gif(
    game_id: str,
    root: Path,
    *,
    overrides: dict[str, Any] | None,
    verbose: bool,
    seed: int,
) -> tuple[Any, list]:
    _ = seed
    o = dict(overrides or {})
    target_levels = int(o.get("target_levels", 0))
    max_gif = int(o.get("max_gif_frames", 950))
    level_hold = int(o.get("ice_level_hold_frames", 14))
    no_move_frames = int(o.get("ice_no_move_frames", 4))

    mod = load_stem_game_py(game_id, f"{game_id}_registry_ice")
    level_defs: list = mod.levels
    n_authored = len(level_defs)
    L = (
        target_levels
        if target_levels > 0
        else min(5, max(1, n_authored))
    )

    plans: list[list[int]] = []
    for i in range(L):
        if game_id == "ic01":
            p = ic01_showcase_plan(level_defs[i])
        elif game_id == "ic02":
            p = ice_slide_plan(level_defs[i], physics="torus")
        elif game_id == "ic03":
            p = ice_slide_plan(level_defs[i], physics="capped")
        else:
            p = ice_slide_plan(level_defs[i])
        if p is None:
            raise RuntimeError(
                f"{game_id}: level {i} has no ice-slide solution for registry GIF"
            )
        plans.append(p)

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
        for plan in plans:
            for av in plan:
                g = env._game
                px, py = g._player.x, g._player.y
                res = safe_env_step(env, _PUSH_ACTION[av], reasoning={})
                if g._player.x == px and g._player.y == py:
                    snap_repeats(no_move_frames)
                else:
                    snap_repeats(1)
            snap_repeats(level_hold)
    except _StepAbort as ex:
        step_abort = True
        if verbose:
            print(f"  {game_id}: ice-slide GIF step abort ({ex})")

    snap_repeats(10)
    if step_abort and not images:
        res = env.reset()
        fr = _frame_layer0(res)
        if fr:
            append_frame_repeats(images, fr[0], 24)

    _cap_gif_frames(images, max_gif)

    if verbose:
        moves = sum(len(p) for p in plans)
        print(
            f"  {game_id}: ice-slide GIF, {L} levels, {moves} moves, {len(images)} frames"
        )

    return res, images


# Visit-all coverage (va01 / va02) and ordered waypoints (va03).
VISIT_ALL_BLOCK_TAGS: dict[str, tuple[str, ...]] = {
    "va01": ("wall",),
    "va02": ("wall", "hazard"),
    "va03": ("wall",),
}


def _visit_all_open_cells(
    level: Level, blocking_tags: tuple[str, ...]
) -> set[tuple[int, int]]:
    gw, gh = level.grid_size
    o: set[tuple[int, int]] = set()
    for x in range(gw):
        for y in range(gh):
            sp = level.get_sprite_at(x, y, ignore_collidable=True)
            if sp is None:
                o.add((x, y))
                continue
            tgs = set(sp.tags)
            if any(t in tgs for t in blocking_tags):
                continue
            o.add((x, y))
    return o


def _bfs_actions_to_any_open(
    open_set: set[tuple[int, int]],
    start: tuple[int, int],
    goals: set[tuple[int, int]],
) -> list[int] | None:
    if start in goals:
        return []
    q: deque[tuple[int, int]] = deque([start])
    prev: dict[tuple[int, int], tuple[tuple[int, int], int] | None] = {start: None}
    found: tuple[int, int] | None = None
    while q:
        x, y = q.popleft()
        if (x, y) in goals:
            found = (x, y)
            break
        for dy, dx, act in _PUSH_DELTAS:
            nx, ny = x + dx, y + dy
            if (nx, ny) not in open_set:
                continue
            if (nx, ny) not in prev:
                prev[(nx, ny)] = ((x, y), act)
                q.append((nx, ny))
    if found is None:
        return None
    out: list[int] = []
    cur = found
    while prev[cur] is not None:
        p, act = prev[cur]
        out.append(act)
        cur = p
    out.reverse()
    return out


def visit_all_greedy_plan(
    level: Level,
    blocking_tags: tuple[str, ...],
    *,
    max_actions: int = 12_000,
) -> list[int] | None:
    """Greedy shortest paths to nearest unvisited open cell until full coverage."""
    open_cells = _visit_all_open_cells(level, blocking_tags)
    player: tuple[int, int] | None = None
    for s in level.get_sprites():
        if "player" in s.tags:
            player = (s.x, s.y)
            break
    if player is None or player not in open_cells:
        return None
    visited: set[tuple[int, int]] = {player}
    plan: list[int] = []
    pos = player
    while visited != open_cells:
        if len(plan) > max_actions:
            return None
        goals = open_cells - visited
        seg = _bfs_actions_to_any_open(open_cells, pos, goals)
        if seg is None:
            return None
        for act in seg:
            plan.append(act)
            dy, dx, _ = next(t for t in _PUSH_DELTAS if t[2] == act)
            pos = (pos[0] + dx, pos[1] + dy)
            visited.add(pos)
    return plan


def va03_ordered_plan(
    level: Level,
    *,
    max_actions: int = 12_000,
) -> list[int] | None:
    """Shortest paths in sequence through ``visit_order``; walls only (marks are walk-through)."""
    raw = level.get_data("visit_order") or []
    order = [(int(p[0]), int(p[1])) for p in raw]
    if not order:
        return []
    gw, gh = level.grid_size
    walls: set[tuple[int, int]] = set()
    player: tuple[int, int] | None = None
    for s in level.get_sprites():
        if "player" in s.tags:
            player = (s.x, s.y)
        elif "wall" in s.tags:
            walls.add((s.x, s.y))
    if player is None:
        return None
    open_cells: set[tuple[int, int]] = set()
    for x in range(gw):
        for y in range(gh):
            if (x, y) not in walls:
                open_cells.add((x, y))
    if player not in open_cells:
        return None
    idx = 0
    if player == order[0]:
        idx = 1
    plan: list[int] = []
    pos = player
    while idx < len(order):
        goal = order[idx]
        seg = _bfs_actions_to_any_open(open_cells, pos, {goal})
        if seg is None:
            return None
        plan.extend(seg)
        for act in seg:
            dy, dx, _ = next(t for t in _PUSH_DELTAS if t[2] == act)
            pos = (pos[0] + dx, pos[1] + dy)
        if pos != goal:
            return None
        idx += 1
        if len(plan) > max_actions:
            return None
    return plan


def _visit_all_blocked_move_ids(level: Level, game_id: str, *, max_ids: int = 2) -> list[int]:
    """Movement action ids (1–4) that are OOB or hit wall/hazard from the player's start cell."""
    px = py = None
    for s in level.get_sprites():
        if "player" in s.tags:
            px, py = s.x, s.y
            break
    if px is None:
        return []
    gw, gh = level.grid_size
    out: list[int] = []
    for dy, dx, aid in _PUSH_DELTAS:
        nx, ny = px + dx, py + dy
        blocked = False
        if not (0 <= nx < gw and 0 <= ny < gh):
            blocked = True
        else:
            sp = level.get_sprite_at(nx, ny, ignore_collidable=True)
            if sp and "wall" in sp.tags:
                blocked = True
            elif game_id == "va02" and sp and "hazard" in sp.tags:
                blocked = True
        if blocked:
            out.append(aid)
            if len(out) >= max_ids:
                break
    return out


def _va03_step_budget_fail_actions(level: Level) -> list[int] | None:
    """
    Successful moves that burn ``step_limit`` without clearing (registry GIF beat).
    Uses a right/right/left/left ping-pong; only valid on levels with no walls where
    that path never satisfies remaining waypoints (verified for shipped va03 L0).
    """
    for s in level.get_sprites():
        if "wall" in s.tags:
            return None
    raw = level.get_data("step_limit")
    if raw is None:
        return None
    lim = int(raw)
    if lim <= 0:
        return None
    pat = (4, 4, 3, 3)
    return [pat[i % 4] for i in range(lim)]


def _record_visit_all_gif(
    game_id: str,
    root: Path,
    *,
    overrides: dict[str, Any] | None,
    verbose: bool,
    seed: int,
) -> tuple[Any, list]:
    _ = seed
    blocking = VISIT_ALL_BLOCK_TAGS[game_id]
    o = dict(overrides or {})
    target_levels = int(o.get("target_levels", 0))
    max_gif = int(o.get("max_gif_frames", 1100))
    level_hold = int(o.get("visit_level_hold_frames", 14))

    mod = load_stem_game_py(game_id, f"{game_id}_registry_visit")
    level_defs: list = mod.levels
    n_authored = len(level_defs)
    L = (
        target_levels
        if target_levels > 0
        else min(5, max(1, n_authored))
    )

    plans: list[list[int]] = []
    for i in range(L):
        if game_id == "va03":
            p = va03_ordered_plan(level_defs[i])
        else:
            p = visit_all_greedy_plan(level_defs[i], blocking)
        if p is None:
            raise RuntimeError(
                f"{game_id}: level {i} has no visit-all plan for registry GIF"
            )
        plans.append(p)

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
        if game_id == "va03":
            burn = _va03_step_budget_fail_actions(level_defs[0])
            if burn:
                for av in burn:
                    res = safe_env_step(env, _PUSH_ACTION[av], reasoning={})
                    snap_repeats(3)
                snap_repeats(16)
                res = env.reset()
                snap_repeats(6)
        fail_ids = (
            _visit_all_blocked_move_ids(level_defs[0], game_id, max_ids=2)
            if game_id == "va02"
            else []
        )
        fail_snap_each, fail_snap_tail = 1, 2
        for av in fail_ids:
            res = safe_env_step(env, _PUSH_ACTION[av], reasoning={})
            snap_repeats(fail_snap_each)
        if fail_ids:
            snap_repeats(fail_snap_tail)
        for plan in plans:
            for av in plan:
                res = safe_env_step(env, _PUSH_ACTION[av], reasoning={})
                snap_repeats(1)
            snap_repeats(level_hold)
    except _StepAbort as ex:
        step_abort = True
        if verbose:
            print(f"  {game_id}: visit-all GIF step abort ({ex})")

    snap_repeats(10)
    if step_abort and not images:
        res = env.reset()
        fr = _frame_layer0(res)
        if fr:
            append_frame_repeats(images, fr[0], 24)

    _cap_gif_frames(images, max_gif)

    if verbose:
        moves = sum(len(p) for p in plans)
        print(
            f"  {game_id}: visit-all GIF, {L} levels, {moves} moves, {len(images)} frames"
        )

    return res, images


def _push_parse_level(level: Level) -> tuple[
    set[tuple[int, int]],
    set[tuple[int, int]],
    set[tuple[int, int]],
    tuple[int, int],
    list[tuple[int, int]],
    int,
    int,
]:
    walls: set[tuple[int, int]] = set()
    targets: set[tuple[int, int]] = set()
    decoys: set[tuple[int, int]] = set()
    player: tuple[int, int] | None = None
    blocks: list[tuple[int, int]] = []
    gw, gh = level.grid_size
    for s in level.get_sprites():
        tgs = s.tags
        if "player" in tgs:
            player = (s.x, s.y)
        elif "wall" in tgs:
            walls.add((s.x, s.y))
        elif "target" in tgs:
            targets.add((s.x, s.y))
        elif "decoy" in tgs:
            decoys.add((s.x, s.y))
        elif "block" in tgs:
            blocks.append((s.x, s.y))
    if player is None:
        raise ValueError("push puzzle parse: no player")
    return walls, targets, decoys, player, blocks, gw, gh


def _push_try_push(
    walls: set[tuple[int, int]],
    gw: int,
    gh: int,
    px: int,
    py: int,
    blocks: tuple[tuple[int, int], ...],
    dy: int,
    dx: int,
    *,
    forbidden_block_dest: frozenset[tuple[int, int]] = frozenset(),
) -> tuple[int, int, tuple[tuple[int, int], ...]] | None:
    nx, ny = px + dx, py + dy
    if not (0 <= nx < gw and 0 <= ny < gh):
        return None
    if (nx, ny) in walls:
        return None
    bl = list(blocks)
    if (nx, ny) not in bl:
        return (nx, ny, blocks)
    i = bl.index((nx, ny))
    bx, by = nx + dx, ny + dy
    if not (0 <= bx < gw and 0 <= by < gh):
        return None
    if (bx, by) in forbidden_block_dest:
        return None
    if (bx, by) in walls or (bx, by) in bl:
        return None
    bl[i] = (bx, by)
    return (nx, ny, tuple(sorted(bl)))


def push_puzzle_plan(
    level: Level,
    *,
    max_nodes: int = 12_000_000,
    win_block_positions: set[tuple[int, int]] | None = None,
    forbidden_block_destinations: frozenset[tuple[int, int]] | None = None,
) -> list[int] | None:
    """BFS over (player, sorted block positions); win when block cells equal win set."""
    walls, targets, _decoys, (px, py), blocks, gw, gh = _push_parse_level(level)
    win_set = win_block_positions if win_block_positions is not None else targets
    forbid = (
        forbidden_block_destinations
        if forbidden_block_destinations is not None
        else frozenset()
    )
    start_bl = tuple(sorted(blocks))
    if set(blocks) == win_set:
        return []
    start = (px, py, start_bl)
    q: deque[tuple[int, int, tuple[tuple[int, int], ...]]] = deque([start])
    came: dict[
        tuple[int, int, tuple[tuple[int, int], ...]],
        tuple[tuple[int, int, tuple[tuple[int, int], ...]], int] | None,
    ] = {start: None}
    nodes = 0
    while q:
        nodes += 1
        if nodes > max_nodes:
            return None
        state = q.popleft()
        px, py, blks = state
        if set(blks) == win_set:
            path: list[int] = []
            cur = state
            while came[cur] is not None:
                prev, act = came[cur]
                path.append(act)
                cur = prev
            path.reverse()
            return path
        for dy, dx, act in _PUSH_DELTAS:
            nxt = _push_try_push(
                walls,
                gw,
                gh,
                px,
                py,
                blks,
                dy,
                dx,
                forbidden_block_dest=forbid,
            )
            if nxt is None:
                continue
            key = (nxt[0], nxt[1], nxt[2])
            if key not in came:
                came[key] = (state, act)
                q.append(key)
    return None


def _pb03_safe_plan(level: Level) -> list[int] | None:
    decoys = _push_parse_level(level)[2]
    return push_puzzle_plan(
        level, forbidden_block_destinations=frozenset(decoys)
    )


def _pb03_decoy_fail_plan(level: Level) -> list[int] | None:
    decoys = _push_parse_level(level)[2]
    if not decoys:
        return None
    return push_puzzle_plan(level, win_block_positions=set(decoys))


def _record_push_puzzle_gif(
    game_id: str,
    root: Path,
    *,
    overrides: dict[str, Any] | None,
    verbose: bool,
    seed: int,
) -> tuple[Any, list]:
    """Solve authored levels offline (fresh level copies) and step the live env."""
    _ = seed  # RNG unused; signature matches record_registry_gif
    o = dict(overrides or {})
    target_levels = int(o.get("target_levels", 0))
    max_gif = int(o.get("max_gif_frames", 520))
    level_hold = int(o.get("push_level_hold_frames", 16))

    mod = load_stem_game_py(game_id, f"{game_id}_registry_push")
    level_defs: list = mod.levels
    n_authored = len(level_defs)
    L = (
        target_levels
        if target_levels > 0
        else min(5, max(1, n_authored))
    )

    plans: list[list[int]] = []
    for i in range(L):
        p = push_puzzle_plan(level_defs[i])
        if p is None:
            raise RuntimeError(
                f"{game_id}: level {i} has no push-puzzle solution for registry GIF"
            )
        plans.append(p)

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
        for plan in plans:
            for av in plan:
                res = safe_env_step(env, _PUSH_ACTION[av], reasoning={})
                snap_repeats(1)
            snap_repeats(level_hold)
    except _StepAbort as ex:
        step_abort = True
        if verbose:
            print(f"  {game_id}: push GIF step abort ({ex})")

    snap_repeats(10)
    if step_abort and not images:
        res = env.reset()
        fr = _frame_layer0(res)
        if fr:
            append_frame_repeats(images, fr[0], 24)

    _cap_gif_frames(images, max_gif)

    if verbose:
        moves = sum(len(p) for p in plans)
        print(f"  {game_id}: push-puzzle GIF, {L} levels, {moves} moves, {len(images)} frames")

    return res, images


def _record_pb03_gif(
    game_id: str,
    root: Path,
    *,
    overrides: dict[str, Any] | None,
    verbose: bool,
    seed: int,
) -> tuple[Any, list]:
    """Level 0: scripted push onto decoy (GAME_OVER + red HUD), reset, then safe solve."""
    _ = seed
    o = dict(overrides or {})
    target_levels = int(o.get("target_levels", 0))
    max_gif = int(o.get("max_gif_frames", 520))
    level_hold = int(o.get("push_level_hold_frames", 16))
    fail_hold = int(o.get("pb03_fail_hold_frames", 22))

    mod = load_stem_game_py(game_id, f"{game_id}_registry_pb03")
    level_defs: list = mod.levels
    n_authored = len(level_defs)
    L = target_levels if target_levels > 0 else min(5, max(1, n_authored))

    fail0 = _pb03_decoy_fail_plan(level_defs[0])
    if fail0 is None:
        raise RuntimeError("pb03: no decoy-loss plan for level 0 registry GIF")
    good0 = _pb03_safe_plan(level_defs[0])
    if good0 is None:
        raise RuntimeError("pb03: no safe solve for level 0 registry GIF")

    later_plans: list[list[int]] = []
    for i in range(1, L):
        p = _pb03_safe_plan(level_defs[i])
        if p is None:
            raise RuntimeError(
                f"{game_id}: level {i} has no decoy-safe solve for registry GIF"
            )
        later_plans.append(p)

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
        for av in fail0:
            res = safe_env_step(env, _PUSH_ACTION[av], reasoning={})
            snap_repeats(1)
        snap_repeats(fail_hold)
        res = env.reset()
        snap_repeats(8)
        for av in good0:
            res = safe_env_step(env, _PUSH_ACTION[av], reasoning={})
            snap_repeats(1)
        snap_repeats(level_hold)
        for plan in later_plans:
            for av in plan:
                res = safe_env_step(env, _PUSH_ACTION[av], reasoning={})
                snap_repeats(1)
            snap_repeats(level_hold)
    except _StepAbort as ex:
        step_abort = True
        if verbose:
            print(f"  {game_id}: pb03 GIF step abort ({ex})")

    snap_repeats(10)
    if step_abort and not images:
        res = env.reset()
        fr = _frame_layer0(res)
        if fr:
            append_frame_repeats(images, fr[0], 24)

    _cap_gif_frames(images, max_gif)

    if verbose:
        moves = len(fail0) + len(good0) + sum(len(p) for p in later_plans)
        print(
            f"  {game_id}: pb03 GIF (decoy fail + solve), {L} level(s), "
            f"{moves} moves, {len(images)} frames"
        )

    return res, images

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
    from registry_mechanic_gif import MECHANIC_SHOWCASE_STEMS, record_mechanic_showcase_gif

    if game_id in MECHANIC_SHOWCASE_STEMS:
        return record_mechanic_showcase_gif(
            game_id, root, overrides=o, verbose=verbose, seed=seed
        )
    if game_id == "pb03":
        return _record_pb03_gif(
            game_id, root, overrides=o, verbose=verbose, seed=seed
        )
    if game_id in PUSH_SOLVER_STEMS:
        return _record_push_puzzle_gif(
            game_id, root, overrides=o, verbose=verbose, seed=seed
        )
    if game_id in SWITCH_DOOR_MODE:
        return _record_switch_door_gif(
            game_id, root, overrides=o, verbose=verbose, seed=seed
        )
    if game_id in PORTAL_PAIR_STEMS:
        return _record_portal_pair_gif(
            game_id, root, overrides=o, verbose=verbose, seed=seed
        )
    if game_id in ICE_SLIDE_STEMS:
        return _record_ice_slide_gif(
            game_id, root, overrides=o, verbose=verbose, seed=seed
        )
    if game_id in VISIT_ALL_BLOCK_TAGS:
        return _record_visit_all_gif(
            game_id, root, overrides=o, verbose=verbose, seed=seed
        )
    if game_id == "mo01":
        from registry_mo_zq_hm_gif import record_mo01_registry_gif

        return record_mo01_registry_gif(
            game_id, root, overrides=o, verbose=verbose, seed=seed
        )
    if game_id == "zq01":
        from registry_mo_zq_hm_gif import record_zq01_registry_gif

        return record_zq01_registry_gif(
            game_id, root, overrides=o, verbose=verbose, seed=seed
        )
    if game_id == "hm01":
        from registry_mo_zq_hm_gif import record_hm01_registry_gif

        return record_hm01_registry_gif(
            game_id, root, overrides=o, verbose=verbose, seed=seed
        )
    if game_id == "ex01":
        from registry_ex_gp_lo_gif import record_ex01_registry_gif

        return record_ex01_registry_gif(
            game_id, root, overrides=o, verbose=verbose, seed=seed
        )
    if game_id == "gp01":
        from registry_ex_gp_lo_gif import record_gp01_registry_gif

        return record_gp01_registry_gif(
            game_id, root, overrides=o, verbose=verbose, seed=seed
        )
    if game_id == "lo01":
        from registry_ex_gp_lo_gif import record_lo01_registry_gif

        return record_lo01_registry_gif(
            game_id, root, overrides=o, verbose=verbose, seed=seed
        )
    if game_id == "lw01":
        from registry_lw_rp_ml_sf_gif import record_lw01_registry_gif

        return record_lw01_registry_gif(
            game_id, root, overrides=o, verbose=verbose, seed=seed
        )
    if game_id == "rp01":
        from registry_lw_rp_ml_sf_gif import record_rp01_registry_gif

        return record_rp01_registry_gif(
            game_id, root, overrides=o, verbose=verbose, seed=seed
        )
    if game_id == "ml01":
        from registry_lw_rp_ml_sf_gif import record_ml01_registry_gif

        return record_ml01_registry_gif(
            game_id, root, overrides=o, verbose=verbose, seed=seed
        )
    if game_id == "sf01":
        from registry_lw_rp_ml_sf_gif import record_sf01_registry_gif

        return record_sf01_registry_gif(
            game_id, root, overrides=o, verbose=verbose, seed=seed
        )
    target_levels = int(o.get("target_levels", 0))  # 0 = min(3, n_levels)
    max_total_steps = int(o.get("max_total_steps", 1400))
    max_idle = int(o.get("max_idle_between", 28))
    stagnation_trigger = int(o.get("stagnation_steps", 100))
    explore_steps = int(o.get("exploration_burst", 36))
    min_frames = int(o.get("min_frames", 36))

    arc = offline_arcade(root)
    env = arc.make(full_game_id_for_stem(game_id), seed=0, render_mode=None)
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
