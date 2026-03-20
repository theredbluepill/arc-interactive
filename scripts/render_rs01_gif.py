#!/usr/bin/env python3
"""Record assets/rs01.gif: L1 + L2 full clear (rule cycle), win holds, short L3 teaser (2/3 levels passed)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(ROOT))

from env_resolve import full_game_id_for_stem, load_stem_game_py  # noqa: E402

import numpy as np
from PIL import Image

from arc_agi import Arcade, OperationMode
from arc_agi.rendering import COLOR_MAP, hex_to_rgb
from arcengine import GameAction, GameState

Rs01 = load_stem_game_py("rs01", "rs01_gif").Rs01

OUTPUT = ROOT / "assets" / "rs01.gif"
ENV_DIR = str(ROOT / "environment_files")

A1, A2, A3, A4 = (
    GameAction.ACTION1,
    GameAction.ACTION2,
    GameAction.ACTION3,
    GameAction.ACTION4,
)

# Level 1: both reds while safe=8 (detour avoids (5,3)/(3,5)); burn 7 steps to hit cycle 15; both greens.
LEVEL1: tuple[GameAction, ...] = (
    A4,
    A4,
    A2,
    A2,
    A4,
    A2,
    A4,
    A2,
    A3,
    A4,
    A3,
    A4,
    A3,
    A4,
    A3,
    A3,
    A4,
    A4,
    A1,
    A1,
)

# Level 2 (8x8): BFS-optimal path under 12-step rule cycle; safe colors [8,14,11].
LEVEL2: tuple[GameAction, ...] = (
    A1,
    A2,
    A1,
    A2,
    A2,
    A2,
    A4,
    A4,
    A2,
    A4,
    A2,
    A4,
    A1,
    A1,
    A1,
    A1,
    A1,
    A2,
    A2,
    A2,
    A2,
    A2,
    A3,
    A3,
    A1,
    A3,
    A1,
    A1,
    A4,
    A4,
)

# After L3 loads: empty-lane motion from (2,2) — no targets collected.
LEVEL3_TEASER: tuple[GameAction, ...] = (A4, A4, A4, A2, A2)

MS_OPEN = 440
MS_MOVE = 175
MS_HOLD = 200
MS_END = 520


def frame_to_image_layer(layer) -> Image.Image:
    arr = np.asarray(layer, dtype=np.uint8)
    h, w = arr.shape
    rgb = np.zeros((h, w, 3), dtype=np.uint8)
    for idx, hx in COLOR_MAP.items():
        rgb[arr == idx] = hex_to_rgb(hx)
    return Image.fromarray(rgb, "RGB")


def main() -> None:
    arc = Arcade(environments_dir=ENV_DIR, operation_mode=OperationMode.NORMAL)
    env = arc.make(full_game_id_for_stem("rs01"), seed=0, include_frame_data=True)
    obs = env.reset()

    images: list[Image.Image] = []
    durations: list[int] = []

    def snap_all(ms: int) -> None:
        fr = getattr(obs, "frame", None) or []
        for layer in fr:
            images.append(frame_to_image_layer(layer))
            durations.append(ms)

    snap_all(MS_OPEN)

    def step_action(a: GameAction, ms: int = MS_MOVE) -> None:
        nonlocal obs
        obs = env.step(a, reasoning={})
        snap_all(ms)

    for a in LEVEL1:
        step_action(a)

    g = env._game
    if len(g._targets) != 0:
        raise RuntimeError(f"L1 incomplete: {len(g._targets)} targets left")

    for _ in range(Rs01.WIN_HOLD_FRAMES):
        step_action(A1, MS_HOLD)

    if (getattr(obs, "levels_completed", 0) or 0) < 1:
        raise RuntimeError("expected level 1 scored after win hold")

    for a in LEVEL2:
        step_action(a)

    g = env._game
    if len(g._targets) != 0:
        raise RuntimeError(f"L2 incomplete: {len(g._targets)} targets left")

    for _ in range(Rs01.WIN_HOLD_FRAMES):
        step_action(A1, MS_HOLD)

    if (getattr(obs, "levels_completed", 0) or 0) < 2:
        raise RuntimeError("expected 2 levels scored after L2 win hold")

    for a in LEVEL3_TEASER:
        step_action(a)

    if obs.state != GameState.NOT_FINISHED:
        raise RuntimeError(obs.state)

    last = images[-1]
    for _ in range(4):
        images.append(last)
        durations.append(MS_END)

    images[0].save(
        OUTPUT,
        save_all=True,
        append_images=images[1:],
        duration=durations,
        loop=0,
        optimize=False,
    )
    print(f"Wrote {OUTPUT} ({len(images)} frames)")


if __name__ == "__main__":
    main()
