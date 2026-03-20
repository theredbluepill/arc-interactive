"""Registry GIF recorders for ex01 (exit hold), gp01 (grid paint), lo01 (Lights Out).

Includes fail beats (wrong hold / bogus clicks) and multi-level scripted solves.
"""

from __future__ import annotations

from collections import deque
from pathlib import Path
from typing import Any

from arcengine import GameAction, GameState

from env_resolve import full_game_id_for_stem, load_stem_game_py
from gif_common import append_frame_repeats, offline_arcade
from registry_gif_lib import DELTA_TO_ACTION, _StepAbort, _cap_gif_frames, safe_env_step

A1, A2, A3, A4, A5, A6 = (
    GameAction.ACTION1,
    GameAction.ACTION2,
    GameAction.ACTION3,
    GameAction.ACTION4,
    GameAction.ACTION5,
    GameAction.ACTION6,
)


def _ex01_walk_plan(
    level: Any,
    start: tuple[int, int],
    goal: tuple[int, int],
) -> list[GameAction]:
    gw, gh = level.grid_size
    walls = {(s.x, s.y) for s in level.get_sprites() if "wall" in s.tags}
    q: deque[tuple[int, int]] = deque([start])
    parent: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    move_from: dict[tuple[int, int], GameAction] = {}
    while q:
        x, y = q.popleft()
        if (x, y) == goal:
            seq: list[GameAction] = []
            cur = (x, y)
            while cur != start:
                act = move_from[cur]
                seq.append(act)
                cur = parent[cur]  # type: ignore[assignment]
            seq.reverse()
            return seq
        for (dx, dy), act in DELTA_TO_ACTION.items():
            nx, ny = x + dx, y + dy
            if not (0 <= nx < gw and 0 <= ny < gh):
                continue
            if (nx, ny) in walls:
                continue
            if (nx, ny) not in parent:
                parent[(nx, ny)] = (x, y)
                move_from[(nx, ny)] = act
                q.append((nx, ny))
    raise RuntimeError(f"ex01: no walk from {start} to {goal}")


def _ex01_pad_pos(level: Any) -> tuple[int, int]:
    pads = level.get_sprites_by_tag("exit_pad")
    p = pads[0]
    return (p.x, p.y)


def record_ex01_registry_gif(
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
    mod = load_stem_game_py(game_id, f"{game_id}_reg")
    n_lv = len(mod.levels)
    L = int(o.get("target_levels", 0)) or min(4, n_lv)
    level_defs = mod.levels[: max(1, L)]

    arc = offline_arcade(root)
    env = arc.make(full_game_id_for_stem(game_id), seed=0, render_mode=None)
    res = env.reset()
    images: list = []

    def snap_repeats(times: int) -> None:
        fr = getattr(res, "frame", None) or []
        if fr:
            append_frame_repeats(images, fr[0], times)

    def step_act(
        act: GameAction, *, data: dict[str, int] | None = None, repeat: int = 1
    ) -> None:
        nonlocal res
        res = safe_env_step(env, act, reasoning={}, data=data or {})
        snap_repeats(repeat)

    snap_repeats(8)
    step_abort = False
    try:
        for li, lv_def in enumerate(level_defs):
            g = env._game
            if g.level_index != li:
                raise RuntimeError(f"ex01: want level_index {li}, got {g.level_index}")
            pl = g._player
            start = (pl.x, pl.y)
            pad = _ex01_pad_pos(lv_def)
            need = int(lv_def.get_data("hold_frames") or 4)

            if li == 0:
                # Fail 1: step off pad then ACTION5 (hold does not accumulate off-pad).
                if start == pad:
                    step_act(A4, repeat=1)
                for _ in range(2):
                    step_act(A5, repeat=1)
                # Fail 2: two good holds on pad then move off (walking resets hold).
                step_act(A3, repeat=1)
                step_act(A5, repeat=1)
                step_act(A5, repeat=1)
                step_act(A4, repeat=1)
                snap_repeats(6)

            for a in _ex01_walk_plan(lv_def, (g._player.x, g._player.y), pad):
                step_act(a, repeat=1)

            for _ in range(need):
                step_act(A5, repeat=1)
            snap_repeats(10 if li < len(level_defs) - 1 else 8)
            lc = getattr(res, "levels_completed", 0) or 0
            if li < len(level_defs) - 1 and lc != li + 1:
                raise RuntimeError(f"ex01: after L{li + 1} want lc {li + 1}, got {lc}")
        if (getattr(res, "levels_completed", 0) or 0) < len(level_defs):
            raise RuntimeError("ex01: episode incomplete")
    except _StepAbort as ex:
        step_abort = True
        if verbose:
            print(f"  {game_id}: ex01 step abort ({ex})")

    snap_repeats(8)
    if step_abort and not images:
        res = env.reset()
        fr = getattr(res, "frame", None) or []
        if fr:
            append_frame_repeats(images, fr[0], 24)
    _cap_gif_frames(images, max_gif)
    if verbose:
        print(f"  {game_id}: exit-hold GIF, {len(images)} frames")
    return res, images


def _burn_after_click(
    env: Any, res_holder: list[Any], snap_repeats, n_frames: int
) -> None:
    for _ in range(n_frames):
        res_holder[0] = safe_env_step(env, A1, reasoning={})
        snap_repeats(1)


def _gp01_click(
    env: Any, g: Any, gx: int, gy: int, res_holder: list[Any], snap_repeats, burn: int
) -> None:
    px, py = g._grid_to_frame_pixel(gx, gy)
    res_holder[0] = safe_env_step(env, A6, reasoning={}, data={"x": px, "y": py})
    snap_repeats(1)
    _burn_after_click(env, res_holder, snap_repeats, burn)


def _gp01_goal_cells(level: Any) -> set[tuple[int, int]]:
    raw = level.get_data("goal_cells") or []
    return {tuple(int(t) for t in p) for p in raw}


def record_gp01_registry_gif(
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
    mod = load_stem_game_py(game_id, f"{game_id}_reg")
    gp = mod.Gp01UI
    burn = int(o.get("click_burn_frames", gp.CLICK_ANIM_FRAMES))
    n_lv = len(mod.levels)
    L = int(o.get("target_levels", 0)) or min(4, n_lv)
    level_defs = mod.levels[: max(1, L)]

    arc = offline_arcade(root)
    env = arc.make(full_game_id_for_stem(game_id), seed=0, render_mode=None)
    res = env.reset()
    images: list = []
    res_box: list[Any] = [res]

    def snap_repeats(times: int) -> None:
        fr = getattr(res_box[0], "frame", None) or []
        if fr:
            append_frame_repeats(images, fr[0], times)

    snap_repeats(8)
    step_abort = False
    try:
        for li, lv_def in enumerate(level_defs):
            g = env._game
            if g.level_index != li:
                raise RuntimeError(f"gp01: want level {li}, got {g.level_index}")
            if li == 0:
                # Miss: coords that skip grid paint (ripple only).
                res_box[0] = safe_env_step(
                    env,
                    A6,
                    reasoning={},
                    data={"x": -40, "y": -40},
                )
                snap_repeats(2)
                _burn_after_click(env, res_box, snap_repeats, burn)
                # Spurious paint off-hint, then undo same cell.
                _gp01_click(env, g, 0, 0, res_box, snap_repeats, burn)
                _gp01_click(env, g, 0, 0, res_box, snap_repeats, burn)

            goal = _gp01_goal_cells(lv_def)
            for gx, gy in sorted(goal):
                if g.level_index != li:
                    break
                if (gx, gy) not in g._painted():
                    _gp01_click(env, g, gx, gy, res_box, snap_repeats, burn)
            res = res_box[0]
            st = getattr(res, "state", None)
            last_lv = li == len(level_defs) - 1
            advanced = g.level_index > li
            if not advanced and not (last_lv and st == GameState.WIN):
                if g._painted() != goal:
                    raise RuntimeError(f"gp01 L{li + 1}: paint mismatch")

            snap_repeats(10 if li < len(level_defs) - 1 else 8)
            res = res_box[0]
            lc = getattr(res, "levels_completed", 0) or 0
            if li < len(level_defs) - 1 and lc != li + 1:
                raise RuntimeError(f"gp01: after L{li + 1} want lc {li + 1}, got {lc}")
        if (getattr(res_box[0], "levels_completed", 0) or 0) < len(level_defs):
            raise RuntimeError("gp01: incomplete")
    except _StepAbort as ex:
        step_abort = True
        if verbose:
            print(f"  {game_id}: gp01 step abort ({ex})")

    snap_repeats(8)
    if step_abort and not images:
        res_box[0] = env.reset()
        fr = getattr(res_box[0], "frame", None) or []
        if fr:
            append_frame_repeats(images, fr[0], 24)
    _cap_gif_frames(images, max_gif)
    if verbose:
        print(f"  {game_id}: grid-paint GIF, {len(images)} frames")
    return res_box[0], images


def _lo_toggle_effect(
    lit: frozenset[tuple[int, int]],
    gx: int,
    gy: int,
    walls: set[tuple[int, int]],
    gw: int,
    gh: int,
) -> frozenset[tuple[int, int]]:
    if (gx, gy) in walls:
        return lit
    s = set(lit)
    for tx, ty in ((gx, gy), (gx - 1, gy), (gx + 1, gy), (gx, gy - 1), (gx, gy + 1)):
        if not (0 <= tx < gw and 0 <= ty < gh):
            continue
        if (tx, ty) in walls:
            continue
        p = (tx, ty)
        if p in s:
            s.remove(p)
        else:
            s.add(p)
    return frozenset(s)


def _lo01_solve_from(
    start: frozenset[tuple[int, int]],
    walls: set[tuple[int, int]],
    gw: int,
    gh: int,
) -> list[tuple[int, int]]:
    goal = frozenset()
    cells = [
        (x, y)
        for y in range(gh)
        for x in range(gw)
        if (x, y) not in walls
    ]
    q: deque[frozenset[tuple[int, int]]] = deque([start])
    parent: dict[frozenset[tuple[int, int]], frozenset[tuple[int, int]] | None] = {
        start: None
    }
    move_from: dict[frozenset[tuple[int, int]], tuple[int, int]] = {}
    while q:
        cur = q.popleft()
        if cur == goal:
            rev: list[tuple[int, int]] = []
            c = cur
            while c != start:
                rev.append(move_from[c])
                c = parent[c]  # type: ignore[assignment]
            rev.reverse()
            return rev
        for gx, gy in cells:
            nxt = _lo_toggle_effect(cur, gx, gy, walls, gw, gh)
            if nxt not in parent:
                parent[nxt] = cur
                move_from[nxt] = (gx, gy)
                q.append(nxt)
    raise RuntimeError("lo01: unsolvable from this configuration")


def record_lo01_registry_gif(
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
    mod = load_stem_game_py(game_id, f"{game_id}_reg")
    lo = mod.Lo01UI
    burn = int(o.get("click_burn_frames", lo.CLICK_ANIM_FRAMES))
    n_lv = len(mod.levels)
    L = int(o.get("target_levels", 0)) or min(4, n_lv)
    level_defs = mod.levels[: max(1, L)]

    arc = offline_arcade(root)
    env = arc.make(full_game_id_for_stem(game_id), seed=0, render_mode=None)
    res = env.reset()
    images: list = []
    res_box: list[Any] = [res]

    def snap_repeats(times: int) -> None:
        fr = getattr(res_box[0], "frame", None) or []
        if fr:
            append_frame_repeats(images, fr[0], times)

    snap_repeats(8)
    step_abort = False
    try:
        for li, lv_def in enumerate(level_defs):
            g = env._game
            if g.level_index != li:
                raise RuntimeError(f"lo01: want level {li}, got {g.level_index}")
            gw, gh = lv_def.grid_size
            walls = {(s.x, s.y) for s in lv_def.get_sprites() if "wall" in s.tags}

            if li == 0:
                res_box[0] = safe_env_step(
                    env,
                    A6,
                    reasoning={},
                    data={"x": -50, "y": -50},
                )
                snap_repeats(2)
                _burn_after_click(env, res_box, snap_repeats, burn)
                # Bad toggle: center cell on 3×3 makes extra lights.
                cx, cy = gw // 2, gh // 2
                if (cx, cy) not in walls:
                    _gp01_click(env, g, cx, cy, res_box, snap_repeats, burn)

            start_lit = frozenset(env._game._lit)
            moves = _lo01_solve_from(start_lit, walls, gw, gh)
            for gx, gy in moves:
                _gp01_click(env, g, gx, gy, res_box, snap_repeats, burn)

            snap_repeats(10 if li < len(level_defs) - 1 else 8)
            res = res_box[0]
            lc = getattr(res, "levels_completed", 0) or 0
            if li < len(level_defs) - 1 and lc != li + 1:
                raise RuntimeError(f"lo01: after L{li + 1} want lc {li + 1}, got {lc}")
        if (getattr(res_box[0], "levels_completed", 0) or 0) < len(level_defs):
            raise RuntimeError("lo01: incomplete")
    except _StepAbort as ex:
        step_abort = True
        if verbose:
            print(f"  {game_id}: lo01 step abort ({ex})")

    snap_repeats(8)
    if step_abort and not images:
        res_box[0] = env.reset()
        fr = getattr(res_box[0], "frame", None) or []
        if fr:
            append_frame_repeats(images, fr[0], 24)
    _cap_gif_frames(images, max_gif)
    if verbose:
        print(f"  {game_id}: lights-out GIF, {len(images)} frames")
    return res_box[0], images
