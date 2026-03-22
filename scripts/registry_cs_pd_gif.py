"""Registry GIF capture for sequencing / strict click-order stems (sq04, sq05)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from arcengine import GameAction, GameState
from env_resolve import full_game_id_for_stem, load_stem_game_py
from gif_common import append_frame_repeats, grid_cell_center_display, offline_arcade
from registry_gif_lib import _cap_gif_frames, _frame_layer0, _StepAbort, safe_env_step


def _click6(env: Any, gx: int, gy: int) -> Any:
    level = env._game.current_level
    gw, gh = level.grid_size
    cx, cy = grid_cell_center_display(gx, gy, grid_w=gw, grid_h=gh)
    return safe_env_step(env, GameAction.ACTION6, reasoning={}, data={"x": cx, "y": cy})


def _noop6(env: Any) -> Any:
    """ACTION6 during sq04/sq05 end-frame tail (handled before click logic)."""
    return safe_env_step(env, GameAction.ACTION6, reasoning={}, data={"x": 32, "y": 32})


def record_sq04_registry_gif(
    game_id: str,
    root: Path,
    *,
    overrides: dict[str, Any] | None = None,
    verbose: bool = False,
    seed: int = 0,
) -> tuple[Any, list]:
    _ = seed
    o = dict(overrides or {})
    max_gif = int(o.get("max_gif_frames", 520))
    level_hold = int(o.get("sq04_level_hold_frames", 22))
    target_levels = int(o.get("target_levels", 0))

    mod = load_stem_game_py(game_id, f"{game_id}_registry_sq04")
    level_defs: list = mod.levels
    n_authored = len(level_defs)
    lc_goal = target_levels if target_levels > 0 else min(4, max(1, n_authored))

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
        for _guard in range(120):
            lc = getattr(res, "levels_completed", 0) or 0
            if lc >= lc_goal:
                break
            if res.state in (GameState.WIN, GameState.GAME_OVER):
                break
            level = env._game.current_level
            seq: list[str] = level.get_data("sequence")
            pos: dict[str, tuple[int, int]] = level.get_data("block_positions")
            if len(seq) >= 2 and seq[0] != seq[-1]:
                wx, wy = pos[seq[0]]
                res = _click6(env, wx, wy)
                snap_repeats(5)
            for idx in range(len(seq) - 1, -1, -1):
                cname = seq[idx]
                x, y = pos[cname]
                res = _click6(env, x, y)
                snap_repeats(4)
            snap_repeats(level_hold)
            lc_before = getattr(res, "levels_completed", 0) or 0
            for _ in range(28):
                lc2 = getattr(res, "levels_completed", 0) or 0
                if lc2 > lc_before:
                    break
                if getattr(env._game, "_end_frames", 0) or getattr(
                    env._game, "_ripple_tail", 0
                ):
                    res = _noop6(env)
                    snap_repeats(1)
                else:
                    break
    except _StepAbort as ex:
        step_abort = True
        if verbose:
            print(f"  {game_id}: sq04 GIF step abort ({ex})")

    snap_repeats(12)
    if step_abort and not images:
        res = env.reset()
        fr = _frame_layer0(res)
        if fr:
            append_frame_repeats(images, fr[0], 24)

    _cap_gif_frames(images, max_gif)
    if verbose:
        print(f"  {game_id}: sq04 registry GIF, {len(images)} frames")
    return res, images


def record_sq05_registry_gif(
    game_id: str,
    root: Path,
    *,
    overrides: dict[str, Any] | None = None,
    verbose: bool = False,
    seed: int = 0,
) -> tuple[Any, list]:
    _ = seed
    o = dict(overrides or {})
    max_gif = int(o.get("max_gif_frames", 520))
    level_hold = int(o.get("sq05_level_hold_frames", 22))
    target_levels = int(o.get("target_levels", 0))

    mod = load_stem_game_py(game_id, f"{game_id}_registry_sq05")
    level_defs: list = mod.levels
    n_authored = len(level_defs)
    lc_goal = target_levels if target_levels > 0 else min(4, max(1, n_authored))

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
        for _guard in range(120):
            lc = getattr(res, "levels_completed", 0) or 0
            if lc >= lc_goal:
                break
            if res.state in (GameState.WIN, GameState.GAME_OVER):
                break
            level = env._game.current_level
            seq: list[str] = level.get_data("sequence")
            pos: dict[str, tuple[int, int]] = level.get_data("block_positions")
            if len(seq) >= 2 and seq[-1] != seq[0]:
                wx, wy = pos[seq[-1]]
                res = _click6(env, wx, wy)
                snap_repeats(5)
            for cname in seq:
                x, y = pos[cname]
                res = _click6(env, x, y)
                snap_repeats(3)
                res = _click6(env, x, y)
                snap_repeats(4)
            snap_repeats(level_hold)
            lc_before = getattr(res, "levels_completed", 0) or 0
            for _ in range(28):
                lc2 = getattr(res, "levels_completed", 0) or 0
                if lc2 > lc_before:
                    break
                if getattr(env._game, "_end_frames", 0) or getattr(
                    env._game, "_ripple_tail", 0
                ):
                    res = _noop6(env)
                    snap_repeats(1)
                else:
                    break
    except _StepAbort as ex:
        step_abort = True
        if verbose:
            print(f"  {game_id}: sq05 GIF step abort ({ex})")

    snap_repeats(12)
    if step_abort and not images:
        res = env.reset()
        fr = _frame_layer0(res)
        if fr:
            append_frame_repeats(images, fr[0], 24)

    _cap_gif_frames(images, max_gif)
    if verbose:
        print(f"  {game_id}: sq05 registry GIF, {len(images)} frames")
    return res, images


# Scripted pipe placements: (grid_x, grid_y, repeat_clicks). h = 1st click, v = 2nd.
PD01_LEVEL_PLANS: list[list[tuple[int, int, int]]] = [
    [(x, 5, 1) for x in range(2, 8)],
    [(5, y, 2) for y in range(2, 8)],
    [(1, y, 2) for y in range(2, 8)] + [(x, 8, 1) for x in range(2, 8)],
    [(x, 5, 1) for x in range(3, 7)],
    [(1, y, 2) for y in range(7, 0, -1)] + [(x, 1, 1) for x in range(2, 8)],
]


def record_pd01_registry_gif(
    game_id: str,
    root: Path,
    *,
    overrides: dict[str, Any] | None = None,
    verbose: bool = False,
    seed: int = 0,
) -> tuple[Any, list]:
    _ = seed
    o = dict(overrides or {})
    max_gif = int(o.get("max_gif_frames", 520))
    level_hold = int(o.get("pd01_level_hold_frames", 22))
    target_levels = int(o.get("target_levels", 0))

    n_authored = len(PD01_LEVEL_PLANS)
    lc_goal = target_levels if target_levels > 0 else min(3, max(1, n_authored))

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
        for _guard in range(32):
            lc = getattr(res, "levels_completed", 0) or 0
            if lc >= lc_goal:
                break
            if res.state in (GameState.WIN, GameState.GAME_OVER):
                break
            li = env._game.level_index
            if li >= len(PD01_LEVEL_PLANS):
                break
            before_li = li
            plan = PD01_LEVEL_PLANS[li]
            if li == 0 and _guard == 0:
                res = _click6(env, 0, 5)
                snap_repeats(4)
            for gx, gy, reps in plan:
                for _ in range(reps):
                    res = _click6(env, gx, gy)
                    snap_repeats(5)
            snap_repeats(level_hold)
            if env._game.level_index == before_li:
                break
    except _StepAbort as ex:
        step_abort = True
        if verbose:
            print(f"  {game_id}: pd01 GIF step abort ({ex})")

    snap_repeats(12)
    if step_abort and not images:
        res = env.reset()
        fr = _frame_layer0(res)
        if fr:
            append_frame_repeats(images, fr[0], 24)

    _cap_gif_frames(images, max_gif)
    if verbose:
        print(f"  {game_id}: pd01 registry GIF, {len(images)} frames")
    return res, images
