#!/usr/bin/env python3
"""Record assets/sq01.gif: L1 clean; L2 one wrong-order tap (loses a life) then full sequence; win defers."""

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

SQ_LEVELS = load_stem_game_py("sq01", "sq01_gif").levels

OUTPUT = ROOT / "assets" / "sq01.gif"
ENV_DIR = str(ROOT / "environment_files")

# 12×12 camera → scale 5, pad 2 → cell center: gx * 5 + scale//2 + pad = gx*5 + 4
def cell_click_xy(top_left_gx: int, top_left_gy: int) -> tuple[int, int]:
    return top_left_gx * 5 + 4, top_left_gy * 5 + 4


def clicks_for_level(level_index: int) -> list[tuple[int, int]]:
    data = SQ_LEVELS[level_index].get_data("block_positions")
    seq = SQ_LEVELS[level_index].get_data("sequence")
    return [cell_click_xy(*data[c]) for c in seq]


MS_OPEN = 420
MS_RIPPLE = 95
MS_SINGLE = 200
MS_DEFER = 130
MS_END = 520

# Must match sq01 `_end_frames` after a level clear — extra steps run on the *next* level and count as real clicks.
WIN_DEFER_STEPS = 12

# In-bounds empty grid cell; only used while `_end_frames` > 0 (hit-test skipped). Avoids letterbox (0,0).
DEFER_XY = cell_click_xy(1, 1)


def frame_to_image_layer(layer) -> Image.Image:
    arr = np.asarray(layer, dtype=np.uint8)
    h, w = arr.shape
    rgb = np.zeros((h, w, 3), dtype=np.uint8)
    for idx, hx in COLOR_MAP.items():
        rgb[arr == idx] = hex_to_rgb(hx)
    return Image.fromarray(rgb, "RGB")


def main() -> None:
    arc = Arcade(environments_dir=ENV_DIR, operation_mode=OperationMode.NORMAL)
    env = arc.make(full_game_id_for_stem("sq01"), seed=0, include_frame_data=True)
    obs = env.reset()

    images: list[Image.Image] = []
    durations: list[int] = []

    def snap_all(ms_per: int) -> None:
        fr = getattr(obs, "frame", None) or []
        for layer in fr:
            images.append(frame_to_image_layer(layer))
            durations.append(ms_per)

    snap_all(MS_OPEN)

    def step_click(x: int, y: int) -> None:
        nonlocal obs
        obs = env.step(GameAction.ACTION6, data={"x": x, "y": y}, reasoning={})
        n = len(getattr(obs, "frame", None) or [])
        ms = MS_RIPPLE if n > 1 else MS_SINGLE
        snap_all(ms)

    def burn_defer(ms: int = MS_DEFER) -> None:
        """Advance win-defer frames; ACTION6 coords unused while `_end_frames` > 0."""
        nonlocal obs
        dx, dy = DEFER_XY
        obs = env.step(GameAction.ACTION6, data={"x": dx, "y": dy}, reasoning={})
        snap_all(ms)

    # --- Level 1: correct order only ---
    plan1 = clicks_for_level(0)
    for i, (cx, cy) in enumerate(plan1):
        step_click(cx, cy)
        if i == len(plan1) - 1:
            for _ in range(WIN_DEFER_STEPS):
                burn_defer()

    # --- Level 2: wrong color first (expected red, tap blue) → −1 life, reset; then red, blue, green ---
    plan2 = clicks_for_level(1)
    if len(plan2) >= 2:
        step_click(*plan2[1])
    for cx, cy in plan2:
        step_click(cx, cy)
    for _ in range(WIN_DEFER_STEPS):
        burn_defer()

    if (getattr(obs, "levels_completed", 0) or 0) < 2:
        raise RuntimeError(f"expected 2 levels cleared, got {getattr(obs, 'levels_completed', 0)}")
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
