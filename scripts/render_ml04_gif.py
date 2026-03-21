#!/usr/bin/env python3
"""Record assets/ml04.gif: BFS-derived clears for all 7 levels (ACTION5 bolt + ACTION6 cycle)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(ROOT))

from env_resolve import full_game_id_for_stem  # noqa: E402

import numpy as np
from PIL import Image

from arc_agi import Arcade, OperationMode
from arc_agi.rendering import COLOR_MAP, hex_to_rgb
from arcengine import GameAction, GameState

OUTPUT = ROOT / "assets" / "ml04.gif"
ENV_DIR = str(ROOT / "environment_files")

# Game grid is 10×10; ARCBaseGame resizes the camera to match (not the 16 passed in Ml04.__init__).
CAM_W = CAM_H = 10

MS_OPEN = 420
MS_MOVE = 120
MS_LEVEL_HOLD = 320
MS_END = 550

A5 = GameAction.ACTION5
A6 = GameAction.ACTION6

# Per-level plans: '5' = ACTION5, (gx,gy) = ACTION6 cell center in grid coords
PLANS: list[list[tuple[int, int] | str]] = [
    ["5", "5", "5", "5", (5, 5), (5, 5), "5", "5", "5"],
    ["5", "5", "5", (4, 5), "5", "5", "5", "5"],
    [
        "5",
        (2, 5),
        "5",
        "5",
        (4, 5),
        (4, 5),
        "5",
        (5, 5),
        "5",
        "5",
        (7, 5),
        (7, 5),
        "5",
    ],
    ["5", "5", (5, 4), (5, 4), "5", "5", (5, 6), "5", "5"],
    ["5", "5", "5", (4, 5), "5", "5", "5", "5"],
    [
        "5",
        "5",
        (3, 5),
        (3, 5),
        "5",
        (4, 5),
        "5",
        "5",
        (6, 5),
        (6, 5),
        "5",
        "5",
    ],
    ["5", "5", "5", (5, 5), (5, 5), "5", (6, 5), "5", "5"],
]


def grid_to_display(gx: int, gy: int) -> tuple[int, int]:
    scale = min(64 // CAM_W, 64 // CAM_H)
    pad = (64 - CAM_W * scale) // 2
    return gx * scale + scale // 2 + pad, gy * scale + scale // 2 + pad


def frame_to_image_layer(layer) -> Image.Image:
    arr = np.asarray(layer, dtype=np.uint8)
    h, w = arr.shape
    rgb = np.zeros((h, w, 3), dtype=np.uint8)
    for idx, hx in COLOR_MAP.items():
        rgb[arr == idx] = hex_to_rgb(hx)
    return Image.fromarray(rgb, "RGB")


def main() -> None:
    arc = Arcade(environments_dir=ENV_DIR, operation_mode=OperationMode.OFFLINE)
    env = arc.make(full_game_id_for_stem("ml04"), seed=0, include_frame_data=True)
    obs = env.reset()

    images: list[Image.Image] = []
    durations: list[int] = []

    def snap_all(ms: int) -> None:
        fr = getattr(obs, "frame", None) or []
        for layer in fr:
            images.append(frame_to_image_layer(layer))
            durations.append(ms)

    def hold_last(ms: int, times: int) -> None:
        if not images:
            return
        last = images[-1]
        for _ in range(times):
            images.append(last.copy())
            durations.append(ms)

    def step_action(
        a: GameAction, data: dict[str, int] | None = None, ms: int = MS_MOVE
    ) -> None:
        nonlocal obs
        obs = env.step(a, reasoning={}, data=data if data is not None else {})
        snap_all(ms)

    snap_all(MS_OPEN)

    for li, plan in enumerate(PLANS):
        for item in plan:
            if item == "5":
                step_action(A5, None, MS_MOVE)
            else:
                gx, gy = item
                x, y = grid_to_display(gx, gy)
                step_action(A6, {"x": x, "y": y}, MS_MOVE)
        hold_last(MS_LEVEL_HOLD, 3 if li < len(PLANS) - 1 else 4)

    if obs.state != GameState.WIN:
        raise RuntimeError(f"expected WIN after 7 levels, got {obs.state}")

    hold_last(MS_END, 6)

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
