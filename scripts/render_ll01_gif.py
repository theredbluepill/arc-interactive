#!/usr/bin/env python3
"""Record assets/ll01.gif: place target 2×2 still-life blocks, then Conway steps per level."""

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

_ll = load_stem_game_py("ll01", "ll01_gif")

OUTPUT = ROOT / "assets" / "ll01.gif"
ENV_DIR = str(ROOT / "environment_files")

CAM_W = CAM_H = 32

MS_OPEN = 420
MS_TOGGLE = 100
MS_STEP = 220
MS_LEVEL_HOLD = 380
MS_END = 550

A1 = GameAction.ACTION1
A5 = GameAction.ACTION5
A6 = GameAction.ACTION6


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
    env = arc.make(full_game_id_for_stem("ll01"), seed=0, include_frame_data=True)
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
        a: GameAction, data: dict[str, int] | None = None, ms: int = MS_TOGGLE
    ) -> None:
        nonlocal obs
        obs = env.step(a, reasoning={}, data=data if data is not None else {})
        snap_all(ms)

    snap_all(MS_OPEN)

    n_levels = len(_ll.levels)
    for li, lv in enumerate(_ll.levels):
        raw = lv.get_data("target_cells") or []
        cells = sorted(tuple(int(t) for t in p) for p in raw)
        need = int(lv.get_data("need_generations") or 1)

        for gx, gy in cells:
            x, y = grid_to_display(gx, gy)
            step_action(A6, {"x": x, "y": y}, MS_TOGGLE)

        for _ in range(need):
            step_action(A5, None, MS_STEP)
            for _ in range(2):
                step_action(A1, None, 90)

        hold_last(MS_LEVEL_HOLD, 4 if li < n_levels - 1 else 5)

    if obs.state != GameState.WIN:
        raise RuntimeError(f"expected WIN after {n_levels} levels, got {obs.state}")

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
