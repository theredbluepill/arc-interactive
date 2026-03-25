"""Registry GIF for ng01 (Nonogram lite): scripted ACTION6 fills from level data."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from arcengine import GameAction, GameState

from env_resolve import full_game_id_for_stem, load_stem_game_py
from gif_common import append_frame_repeats, grid_cell_center_display, offline_arcade
from registry_gif_lib import _cap_gif_frames, safe_env_step

OFF = 2
GW = GH = 8


def _frame0(res: Any) -> list:
    return getattr(res, "frame", None) or []


def _click_grid(
    env: Any,
    res: Any,
    images: list,
    gx: int,
    gy: int,
    *,
    repeats: int,
) -> Any:
    level = env._game.current_level
    gw, gh = level.grid_size
    cx, cy = grid_cell_center_display(gx, gy, grid_w=gw, grid_h=gh)
    res = safe_env_step(
        env, GameAction.ACTION6, reasoning={}, data={"x": cx, "y": cy}
    )
    fr = _frame0(res)
    if fr:
        append_frame_repeats(images, fr[0], repeats)
    return res


def record_ng01_registry_gif(
    game_id: str,
    root: Path,
    *,
    overrides: dict[str, Any] | None = None,
    verbose: bool = False,
    seed: int = 0,
) -> tuple[Any, list]:
    _ = seed
    o = dict(overrides or {})
    mod = load_stem_game_py(game_id, "ng01_registry_levels")
    n_authored = len(mod.levels)
    target = int(o.get("target_levels", 0))
    L = target if target > 0 else min(4, max(1, n_authored))
    L = min(L, n_authored)
    click_rep = int(o.get("ng01_click_repeat", 2))
    level_hold = int(o.get("ng01_level_hold_frames", 16))
    max_gif = int(o.get("max_gif_frames", 520))

    arc = offline_arcade(root)
    env = arc.make(
        full_game_id_for_stem(game_id), seed=0, render_mode=None
    )
    res = env.reset()
    images: list = []

    fr = _frame0(res)
    if not fr:
        raise RuntimeError("ng01 registry: no frame after reset")
    append_frame_repeats(images, fr[0], 8)

    for level_i in range(L):
        li0 = env._game.level_index
        level = env._game.current_level
        sol: list[list[int]] = level.get_data("solution")
        if not sol or len(sol) != GH or any(len(row) != GW for row in sol):
            raise RuntimeError("ng01 registry: bad solution shape")

        if level_i == 0:
            wrong: tuple[int, int] | None = None
            for y in range(GH):
                for x in range(GW):
                    if sol[y][x] == 0:
                        wrong = (x, y)
                        break
                if wrong:
                    break
            if wrong is not None:
                wx, wy = wrong
                gx, gy = OFF + wx, OFF + wy
                res = _click_grid(env, res, images, gx, gy, repeats=click_rep + 2)
                res = _click_grid(env, res, images, gx, gy, repeats=click_rep)
                res = _click_grid(env, res, images, gx, gy, repeats=click_rep)
        elif level_i == 1:
            wrong2: tuple[int, int] | None = None
            for y in range(GH):
                for x in range(GW):
                    if sol[y][x] == 0:
                        wrong2 = (x, y)
                        break
                if wrong2:
                    break
            if wrong2 is not None:
                wx, wy = wrong2
                gx, gy = OFF + wx, OFF + wy
                res = _click_grid(env, res, images, gx, gy, repeats=click_rep + 1)
                res = _click_grid(env, res, images, gx, gy, repeats=click_rep)
                res = _click_grid(env, res, images, gx, gy, repeats=click_rep)

        filled: list[tuple[int, int]] = [
            (x, y)
            for y in range(GH)
            for x in range(GW)
            if sol[y][x] == 1
        ]
        filled.sort()
        for x, y in filled:
            gx, gy = OFF + x, OFF + y
            res = _click_grid(env, res, images, gx, gy, repeats=click_rep)

        fr2 = _frame0(res)
        if fr2:
            append_frame_repeats(images, fr2[0], level_hold)

        if res.state in (GameState.WIN, GameState.GAME_OVER):
            break
        if (getattr(res, "levels_completed", 0) or 0) >= L:
            break
        if env._game.level_index == li0 and level_i < L - 1:
            if verbose:
                print(f"  {game_id}: level {level_i} did not advance (unexpected)")

    fr3 = _frame0(res)
    if fr3:
        append_frame_repeats(images, fr3[0], 12)

    _cap_gif_frames(images, max_gif)
    return res, images


REGISTRY_RECORDERS: dict[str, Any] = {
    "ng01": record_ng01_registry_gif,
}
