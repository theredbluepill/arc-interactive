"""Registry GIF recorders for mm04 (peek memory), mm05 (sticky memory), fe02 (vote + ratify)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from arcengine import GameAction, GameState

from env_resolve import full_game_id_for_stem, load_stem_game_py
from gif_common import append_frame_repeats, offline_arcade
from registry_gif_lib import _cap_gif_frames, safe_env_step

A1, A2, A3, A4, A5, A6 = (
    GameAction.ACTION1,
    GameAction.ACTION2,
    GameAction.ACTION3,
    GameAction.ACTION4,
    GameAction.ACTION5,
    GameAction.ACTION6,
)


def _slot_center(mod: Any, level_index: int, slot_idx: int) -> tuple[int, int]:
    rows, cols = mod.LEVEL_DIMS[level_index]
    ts, ox, oy = mod._compute_tile_size_and_offsets(rows, cols)
    r, c = slot_idx // cols, slot_idx % cols
    return ox + c * ts + ts // 2, oy + r * ts + ts // 2


def _snap(res: Any, images: list, times: int) -> None:
    fr = getattr(res, "frame", None) or []
    if fr:
        append_frame_repeats(images, fr[0], times)


def _step(
    env: Any,
    res_holder: list,
    act: GameAction,
    *,
    data: dict[str, int] | None = None,
    images: list | None = None,
    repeat: int = 1,
) -> Any:
    r = safe_env_step(env, act, reasoning={}, data=data or {})
    res_holder[0] = r
    if images is not None:
        _snap(r, images, repeat)
    return r


def record_mm04_registry_gif(
    game_id: str,
    root: Path,
    *,
    overrides: dict[str, Any] | None,
    verbose: bool,
    seed: int,
) -> tuple[Any, list]:
    _ = verbose, seed
    o = dict(overrides or {})
    max_gif = int(o.get("max_gif_frames", 520))
    mod = load_stem_game_py(game_id, f"{game_id}_reg")
    arc = offline_arcade(root)
    env = arc.make(full_game_id_for_stem(game_id), seed=0, render_mode=None)
    res_box: list[Any] = [env.reset()]
    images: list = []
    _snap(res_box[0], images, 6)

    def stp(act: GameAction, *, data: dict[str, int] | None = None, rep: int = 2) -> None:
        _step(env, res_box, act, data=data, images=images, repeat=rep)

    # Level 1: peek then burn 5 steps while faces stay up (only [5,6] actions).
    stp(A5, rep=5)
    for _ in range(5):
        stp(A5, rep=3)

    # Clear L1 [8,9,9,8] — match corners (8) then edge (9).
    for slot in (0, 3, 1, 2):
        li = env._game.level_index
        x, y = _slot_center(mod, li, slot)
        stp(A6, data={"x": x, "y": y}, rep=3)

    _snap(res_box[0], images, 8)

    # Level 2: mismatch (8 vs 9) then clear [8, 11, 9, 9, 11, 8].
    if res_box[0].state not in (GameState.WIN, GameState.GAME_OVER):
        li = env._game.level_index
        x0, y0 = _slot_center(mod, li, 0)
        x2, y2 = _slot_center(mod, li, 2)
        stp(A6, data={"x": x0, "y": y0}, rep=2)
        stp(A6, data={"x": x2, "y": y2}, rep=2)
        for _ in range(4):
            stp(A5, rep=2)
        for slot in (0, 5, 1, 4, 2, 3):
            li = env._game.level_index
            x, y = _slot_center(mod, li, slot)
            stp(A6, data={"x": x, "y": y}, rep=3)
        _snap(res_box[0], images, 10)

    _cap_gif_frames(images, max_gif)
    return res_box[0], images


def record_mm05_registry_gif(
    game_id: str,
    root: Path,
    *,
    overrides: dict[str, Any] | None,
    verbose: bool,
    seed: int,
) -> tuple[Any, list]:
    _ = verbose, seed
    o = dict(overrides or {})
    max_gif = int(o.get("max_gif_frames", 520))
    mod = load_stem_game_py(game_id, f"{game_id}_reg")
    arc = offline_arcade(root)
    env = arc.make(full_game_id_for_stem(game_id), seed=0, render_mode=None)
    res_box: list[Any] = [env.reset()]
    images: list = []
    _snap(res_box[0], images, 6)

    def stp(act: GameAction, *, data: dict[str, int] | None = None, rep: int = 2) -> None:
        _step(env, res_box, act, data=data, images=images, repeat=rep)

    # L1: diagonal 8s then 9s.
    for slot in (0, 3, 1, 2):
        li = env._game.level_index
        x, y = _slot_center(mod, li, slot)
        stp(A6, data={"x": x, "y": y}, rep=3)
    _snap(res_box[0], images, 8)

    # L2: solve in an order valid under sticky edge-pair rule.
    if res_box[0].state not in (GameState.WIN, GameState.GAME_OVER):
        for slot in (0, 5, 2, 3, 1, 4):
            li = env._game.level_index
            x, y = _slot_center(mod, li, slot)
            stp(A6, data={"x": x, "y": y}, rep=3)
        _snap(res_box[0], images, 8)

    _cap_gif_frames(images, max_gif)
    return res_box[0], images


def record_fe02_registry_gif(
    game_id: str,
    root: Path,
    *,
    overrides: dict[str, Any] | None,
    verbose: bool,
    seed: int,
) -> tuple[Any, list]:
    _ = verbose, seed
    o = dict(overrides or {})
    max_gif = int(o.get("max_gif_frames", 520))
    target_levels = int(o.get("target_levels", 0)) or 3
    arc = offline_arcade(root)
    env = arc.make(full_game_id_for_stem(game_id), seed=0, render_mode=None)
    res_box: list[Any] = [env.reset()]
    images: list = []
    _snap(res_box[0], images, 6)

    def stp(act: GameAction, *, rep: int = 2) -> None:
        _step(env, res_box, act, images=images, repeat=rep)

    # Keeps a,b,c in 1..9 through 5 ratifications; repeats per level.
    vote_then_ratify = [
        (A3,),
        (A4,),
        (A3,),
        (A2,),
        (A1,),
    ]

    for _lv in range(min(target_levels, len(env._game._levels))):
        if res_box[0].state in (GameState.WIN, GameState.GAME_OVER):
            break
        for votes in vote_then_ratify:
            for v in votes:
                stp(v, rep=2)
            stp(A5, rep=4)
        _snap(res_box[0], images, 10)

    _cap_gif_frames(images, max_gif)
    return res_box[0], images
