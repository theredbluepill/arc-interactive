"""Registry GIF recorders for lw01, rp01, ml01, sf01 (path / relay / laser / stencil)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from arcengine import GameAction, GameState

from env_resolve import full_game_id_for_stem, load_stem_game_py
from gif_common import (
    append_frame_repeats,
    append_frame_repeats_each_layer,
    append_frame_repeats_latest,
    append_registry_click_ripple,
    grid_cell_center_display,
    observation_frame_layers,
    offline_arcade,
)
from registry_gif_lib import _StepAbort, _cap_gif_frames, safe_env_step

A1, A2, A3, A4, A5, A6 = (
    GameAction.ACTION1,
    GameAction.ACTION2,
    GameAction.ACTION3,
    GameAction.ACTION4,
    GameAction.ACTION5,
    GameAction.ACTION6,
)


def _click6(env: Any, g: Any, gx: int, gy: int, res_box: list[Any]) -> Any:
    grid_fn = getattr(g, "_grid_to_frame_pixel", None)
    if callable(grid_fn):
        px, py = grid_fn(gx, gy)
    else:
        level = g.current_level
        gw, gh = level.grid_size
        px, py = grid_cell_center_display(gx, gy, grid_w=gw, grid_h=gh)
    r = safe_env_step(env, A6, reasoning={}, data={"x": px, "y": py})
    res_box[0] = r
    return r


def record_lw01_registry_gif(
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
    L = int(o.get("target_levels", 0)) or 2
    mod = load_stem_game_py(game_id, f"{game_id}_reg")
    level_defs = mod.levels[: max(1, min(L, len(mod.levels)))]

    arc = offline_arcade(root)
    env = arc.make(full_game_id_for_stem(game_id), seed=0, render_mode=None)
    res = env.reset()
    images: list = []
    res_box: list[Any] = [res]

    def snap(times: int) -> None:
        append_frame_repeats_latest(images, res_box[0], times)

    snap(8)
    step_abort = False
    try:
        for li, _lv in enumerate(level_defs):
            g = env._game
            if g.level_index != li:
                raise RuntimeError(f"lw01: level_index {g.level_index} != {li}")

            if li == 0:
                _click6(env, g, 0, 0, res_box)
                snap(2)
                _click6(env, g, 5, 5, res_box)
                snap(2)

            pairs = g._pairs
            paths = g._paths
            level_advanced = False
            for ci in range(len(pairs)):
                if level_advanced:
                    break
                while g._active != ci:
                    res_box[0] = safe_env_step(env, A2, reasoning={})
                    snap(1)
                st, en = pairs[ci]
                cur = paths[ci][-1]
                if cur != st:
                    raise RuntimeError("lw01: path tip not at start")
                cx, cy = cur
                ex, ey = en
                while (cx, cy) != (ex, ey):
                    if cx != ex:
                        nx = cx + (1 if ex > cx else -1)
                        ny = cy
                    else:
                        nx = cx
                        ny = cy + (1 if ey > cy else -1)
                    _click6(env, g, nx, ny, res_box)
                    snap(1)
                    cx, cy = nx, ny
                    g = env._game
                    # Winning click calls next_level() and resets _paths; do not compare
                    # to the new level's tip.
                    if g.level_index != li:
                        level_advanced = True
                        break
                    if (cx, cy) != g._paths[ci][-1]:
                        raise RuntimeError("lw01: path did not extend")

            snap(10 if li < len(level_defs) - 1 else 8)
            lc = getattr(res_box[0], "levels_completed", 0) or 0
            if li < len(level_defs) - 1 and lc != li + 1:
                raise RuntimeError(f"lw01: expected lc {li + 1}, got {lc}")
        if (getattr(res_box[0], "levels_completed", 0) or 0) < len(level_defs):
            raise RuntimeError("lw01: incomplete")
    except _StepAbort as ex:
        step_abort = True
        if verbose:
            print(f"  {game_id}: lw01 abort ({ex})")

    snap(8)
    if step_abort and not images:
        res_box[0] = env.reset()
        append_frame_repeats_latest(images, res_box[0], 24)
    _cap_gif_frames(images, max_gif)
    if verbose:
        print(f"  {game_id}: line-weave GIF, {len(images)} frames")
    return res_box[0], images


def _record_rp_row_relay_registry_gif(
    game_id: str,
    root: Path,
    *,
    overrides: dict[str, Any] | None,
    verbose: bool,
    seed: int,
) -> tuple[Any, list]:
    """Shared capture for **rp01** / **rp02** when L0 is a straight east relay run."""
    _ = seed
    o = dict(overrides or {})
    max_gif = int(o.get("max_gif_frames", 900))
    L = int(o.get("target_levels", 0)) or 1
    mod = load_stem_game_py(game_id, f"{game_id}_reg")
    level_defs = mod.levels[: max(1, min(L, len(mod.levels)))]

    arc = offline_arcade(root)
    env = arc.make(full_game_id_for_stem(game_id), seed=0, render_mode=None)
    res = env.reset()
    images: list = []
    res_box: list[Any] = [res]

    def snap(times: int) -> None:
        append_frame_repeats_latest(images, res_box[0], times)

    snap(8)
    step_abort = False
    try:
        for li, _lv in enumerate(level_defs):
            g = env._game
            if g.level_index != li:
                raise RuntimeError(f"{game_id}: level_index {g.level_index} != {li}")

            if li == 0:
                res_box[0] = safe_env_step(env, A5, reasoning={})
                snap(3)

            sx, sy = g._src
            lamps = g._lamps
            walls = {
                (s.x, s.y)
                for s in g.current_level.get_sprites()
                if "wall" in s.tags
            }

            def wall_at(x: int, y: int) -> bool:
                return (x, y) in walls

            targets = set(lamps)
            # All lamps on the source row, east of the source (single-row tutorial + L0).
            if targets and all(ly == sy for _, ly in targets) and all(
                lx > sx for lx, ly in targets
            ):
                y_line = sy
                max_x = max(lx for lx, ly in targets)
                for x in range(sx + 1, max_x + 1):
                    if wall_at(x, y_line):
                        continue
                    if (x, y_line) == (sx, sy):
                        continue
                    g = env._game
                    sp0 = g.current_level.get_sprite_at(
                        x, y_line, ignore_collidable=True
                    )
                    if sp0 and "relay" in sp0.tags:
                        continue
                    _click6(env, g, x, y_line, res_box)
                    snap(1)
            else:
                raise RuntimeError(
                    f"{game_id}: registry GIF needs a scripted layout for this level"
                )

            res_box[0] = safe_env_step(env, A5, reasoning={})
            snap(8)

            lc = getattr(res_box[0], "levels_completed", 0) or 0
            st = getattr(res_box[0], "state", None)
            g = env._game
            if li < len(level_defs) - 1:
                if lc < li + 1:
                    raise RuntimeError(f"{game_id}: expected level advance after fire")
            elif len(level_defs) >= len(mod.levels):
                if st != GameState.WIN:
                    raise RuntimeError(f"{game_id}: last level not won")
            elif lc < li + 1 and g.level_index <= li:
                raise RuntimeError(f"{game_id}: scripted level not cleared")

            snap(6 if li < len(level_defs) - 1 else 8)
    except _StepAbort as ex:
        step_abort = True
        if verbose:
            print(f"  {game_id}: relay GIF abort ({ex})")

    snap(8)
    if step_abort and not images:
        res_box[0] = env.reset()
        append_frame_repeats_latest(images, res_box[0], 24)
    _cap_gif_frames(images, max_gif)
    if verbose:
        print(f"  {game_id}: relay GIF, {len(images)} frames")
    return res_box[0], images


def record_rp01_registry_gif(
    game_id: str,
    root: Path,
    *,
    overrides: dict[str, Any] | None,
    verbose: bool,
    seed: int,
) -> tuple[Any, list]:
    return _record_rp_row_relay_registry_gif(
        game_id, root, overrides=overrides, verbose=verbose, seed=seed
    )


def record_rp02_registry_gif(
    game_id: str,
    root: Path,
    *,
    overrides: dict[str, Any] | None,
    verbose: bool,
    seed: int,
) -> tuple[Any, list]:
    return _record_rp_row_relay_registry_gif(
        game_id, root, overrides=overrides, verbose=verbose, seed=seed
    )


def record_ml01_registry_gif(
    game_id: str,
    root: Path,
    *,
    overrides: dict[str, Any] | None,
    verbose: bool,
    seed: int,
) -> tuple[Any, list]:
    _ = seed
    o = dict(overrides or {})
    max_gif = int(o.get("max_gif_frames", 600))
    L = int(o.get("target_levels", 0)) or 1

    arc = offline_arcade(root)
    env = arc.make(full_game_id_for_stem(game_id), seed=0, render_mode=None)
    res = env.reset()
    images: list = []
    res_box: list[Any] = [res]

    def snap(times: int) -> None:
        append_frame_repeats_latest(images, res_box[0], times)

    snap(10)
    step_abort = False
    try:
        for li in range(max(1, min(L, 5))):
            g = env._game
            if g.level_index != li:
                raise RuntimeError(f"ml01: level_index {g.level_index} != {li}")

            if li == 0:
                _click6(env, g, 10, 10, res_box)
                ly = observation_frame_layers(res_box[0])
                if ly:
                    fcx, fcy = g._grid_to_frame_pixel(10, 10)
                    append_registry_click_ripple(images, ly[-1], fcx, fcy)
                append_frame_repeats_latest(images, res_box[0], 2)
                res_box[0] = safe_env_step(env, A5, reasoning={})
                append_frame_repeats_each_layer(images, res_box[0], 6)
            else:
                raise RuntimeError("ml01: add scripted plan for deeper levels in registry")

            lc = getattr(res_box[0], "levels_completed", 0) or 0
            if li < L - 1 and lc != li + 1:
                raise RuntimeError(f"ml01: expected level advance at {li}")
        st = getattr(res_box[0], "state", None)
        lc = getattr(res_box[0], "levels_completed", 0) or 0
        if lc < L and st != GameState.WIN:
            raise RuntimeError("ml01: episode not cleared")
    except _StepAbort as ex:
        step_abort = True
        if verbose:
            print(f"  {game_id}: ml01 abort ({ex})")

    snap(12)
    if step_abort and not images:
        res_box[0] = env.reset()
        append_frame_repeats_latest(images, res_box[0], 24)
    _cap_gif_frames(images, max_gif)
    if verbose:
        print(f"  {game_id}: laser GIF, {len(images)} frames")
    return res_box[0], images


def record_sf01_registry_gif(
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
    L = int(o.get("target_levels", 0)) or 2
    mod = load_stem_game_py(game_id, f"{game_id}_reg")
    level_defs = mod.levels[: max(1, min(L, len(mod.levels)))]

    arc = offline_arcade(root)
    env = arc.make(full_game_id_for_stem(game_id), seed=0, render_mode=None)
    res = env.reset()
    images: list = []
    res_box: list[Any] = [res]

    def snap(times: int) -> None:
        append_frame_repeats_latest(images, res_box[0], times)

    def burn_move(act: GameAction, times: int = 1) -> None:
        res_box[0] = safe_env_step(env, act, reasoning={})
        snap(times)

    snap(12)
    step_abort = False
    try:
        for li, _lv in enumerate(level_defs):
            g = env._game
            if g.level_index != li:
                raise RuntimeError(f"sf01: level_index {g.level_index} != {li}")

            if li == 0:
                for _ in range(8):
                    burn_move(A3, 1)
                for _ in range(8):
                    burn_move(A1, 1)
                res_box[0] = safe_env_step(env, A5, reasoning={})
                snap(3)
                for _ in range(8):
                    burn_move(A2, 1)
                for _ in range(8):
                    burn_move(A4, 1)

            gw, gh = g.current_level.grid_size
            stn = g.ST
            while g.level_index == li and not (g._goal <= g._painted()):
                miss = g._goal - g._painted()
                gx = min(x for x, y in miss)
                gy = min(y for x, y in miss if x == gx)
                sx = max(0, min(gx - stn + 1, gw - stn))
                sy = max(0, min(gy - stn + 1, gh - stn))
                while g.level_index == li and g._sx > sx:
                    burn_move(A3, 1)
                while g.level_index == li and g._sx < sx:
                    burn_move(A4, 1)
                while g.level_index == li and g._sy > sy:
                    burn_move(A1, 1)
                while g.level_index == li and g._sy < sy:
                    burn_move(A2, 1)
                if g.level_index != li:
                    break
                res_box[0] = safe_env_step(env, A5, reasoning={})
                snap(4)
                if len(images) > max_gif * 2:
                    raise RuntimeError("sf01: paint loop too long")

            snap(14 if li < len(level_defs) - 1 else 12)
            lc = getattr(res_box[0], "levels_completed", 0) or 0
            if li < len(level_defs) - 1 and lc != li + 1:
                raise RuntimeError(f"sf01: expected lc {li + 1}, got {lc}")
        if (getattr(res_box[0], "levels_completed", 0) or 0) < len(level_defs):
            st = getattr(res_box[0], "state", None)
            if st != GameState.WIN:
                raise RuntimeError("sf01: incomplete")
    except _StepAbort as ex:
        step_abort = True
        if verbose:
            print(f"  {game_id}: sf01 abort ({ex})")

    snap(12)
    if step_abort and not images:
        res_box[0] = env.reset()
        append_frame_repeats_latest(images, res_box[0], 24)
    _cap_gif_frames(images, max_gif)
    if verbose:
        print(f"  {game_id}: stencil GIF, {len(images)} frames")
    return res_box[0], images


REGISTRY_RECORDERS = {
    "lw01": record_lw01_registry_gif,
    "rp01": record_rp01_registry_gif,
    "rp02": record_rp02_registry_gif,
    "ml01": record_ml01_registry_gif,
    "sf01": record_sf01_registry_gif,
}
