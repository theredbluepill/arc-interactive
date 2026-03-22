"""Registry GIF helpers for tk01–sr01 batch (fc01 chain, optional others)."""

from __future__ import annotations

import random
from pathlib import Path
from typing import Any

from arcengine import GameAction, GameState
from env_resolve import full_game_id_for_stem
from gif_common import append_frame_repeats, offline_arcade
from registry_gif_lib import (
    _StepAbort,
    _cap_gif_frames,
    _frame_layer0,
    safe_env_step,
)

_MOVE_ACTIONS = (
    GameAction.ACTION1,
    GameAction.ACTION2,
    GameAction.ACTION3,
    GameAction.ACTION4,
)


def record_gc01_registry_gif(
    game_id: str,
    root: Path,
    *,
    overrides: dict[str, Any] | None = None,
    verbose: bool = False,
    seed: int = 0,
) -> tuple[Any, list]:
    """Spreading coral makes the generic BFS recorder impractically slow; use showcase tour."""
    _ = seed
    o = dict(overrides or {})
    max_gif = int(o.get("max_gif_frames", 520))

    arc = offline_arcade(root)
    env = arc.make(full_game_id_for_stem(game_id), seed=0, render_mode=None)
    res = env.reset()
    images: list = []

    def snap_repeats(times: int) -> None:
        fr = _frame_layer0(res)
        if fr:
            append_frame_repeats(images, fr[0], times)

    snap_repeats(8)
    from registry_gif_lib import run_showcase_fallback

    try:
        res = run_showcase_fallback(env, res, images, snap_repeats)
    except _StepAbort:
        res = env.reset()
        fr = _frame_layer0(res)
        if fr:
            append_frame_repeats(images, fr[0], 24)
    rng = random.Random(seed + 41)
    extra = int(o.get("gc01_extra_random_steps", 96))
    for _ in range(extra):
        if len(images) > max_gif * 2:
            break
        act = rng.choice(_MOVE_ACTIONS)
        try:
            res = safe_env_step(env, act, reasoning={}, data={})
        except _StepAbort:
            break
        fr = _frame_layer0(res)
        if fr:
            append_frame_repeats(images, fr[0], 1)
        if res.state in (GameState.WIN, GameState.GAME_OVER):
            append_frame_repeats(images, fr[0], 12)
            res = env.reset()
            fr = _frame_layer0(res)
            if fr:
                append_frame_repeats(images, fr[0], 8)
    snap_repeats(12)
    _cap_gif_frames(images, max_gif)
    if verbose:
        print(f"  {game_id}: gc01 showcase registry GIF, {len(images)} frames")
    return res, images


def record_fc01_registry_gif(
    game_id: str,
    root: Path,
    *,
    overrides: dict[str, Any] | None = None,
    verbose: bool = False,
    seed: int = 0,
) -> tuple[Any, list]:
    """Random valid moves with periodic reset on win/lose for chain-follow GIF."""
    o = dict(overrides or {})
    max_gif = int(o.get("max_gif_frames", 520))
    rng = random.Random(seed + 17)
    n_steps = int(o.get("fc01_registry_steps", 380))

    arc = offline_arcade(root)
    env = arc.make(full_game_id_for_stem(game_id), seed=0, render_mode=None)
    res = env.reset()
    images: list = []

    def snap(times: int = 1) -> None:
        fr = _frame_layer0(res)
        if fr:
            append_frame_repeats(images, fr[0], times)

    snap(10)
    step_abort = False
    try:
        for _ in range(n_steps):
            if len(images) > max_gif * 2:
                break
            act = rng.choice(_MOVE_ACTIONS)
            try:
                res = safe_env_step(env, act, reasoning={}, data={})
            except _StepAbort:
                step_abort = True
                break
            snap(1)
            if res.state in (GameState.WIN, GameState.GAME_OVER):
                snap(14)
                res = env.reset()
                snap(8)
    except _StepAbort as ex:
        step_abort = True
        if verbose:
            print(f"  {game_id}: fc01 GIF step abort ({ex})")

    snap(10)
    if step_abort and len(images) < 24:
        res = env.reset()
        fr = _frame_layer0(res)
        if fr:
            append_frame_repeats(images, fr[0], 32)

    _cap_gif_frames(images, max_gif)
    if verbose:
        print(f"  {game_id}: fc01 registry GIF, {len(images)} frames")
    return res, images
