#!/usr/bin/env python3
"""
Record sy01 levels 1–3: ACTION6 uses display pixel coords (0–63) at each mirrored
cell center — inverse of camera.display_to_grid per create-arc-game SKILL.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image

from arc_agi import Arcade, OperationMode
from arcengine import GameAction

ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
from env_resolve import full_game_id_for_stem, load_stem_game_py  # noqa: E402

_COLOR_HEX = {
    0: "#FFFFFFFF",
    1: "#CCCCCCFF",
    2: "#999999FF",
    3: "#666666FF",
    4: "#333333FF",
    5: "#000000FF",
    6: "#E53AA3FF",
    7: "#FF7BCCFF",
    8: "#F93C31FF",
    9: "#1E93FFFF",
    10: "#88D8F1FF",
    11: "#FFDC00FF",
    12: "#FF851BFF",
    13: "#921231FF",
    14: "#4FCC30FF",
    15: "#A356D6FF",
}

_LUT = np.zeros((256, 3), dtype=np.uint8)
for i, hx in _COLOR_HEX.items():
    r = int(hx[1:3], 16)
    g = int(hx[3:5], 16)
    b = int(hx[5:7], 16)
    _LUT[i] = (r, g, b)


def _load_sy01_module():
    return load_stem_game_py("sy01", "sy01_gif_mod")


def _grid_center_display(gw: int, gh: int, gx: int, gy: int) -> tuple[int, int]:
    """Match Sy01._grid_to_frame_pixel (cell center in 64×64 output)."""
    scale_x = int(64 / gw)
    scale_y = int(64 / gh)
    scale = min(scale_x, scale_y)
    x_pad = int((64 - (gw * scale)) / 2)
    y_pad = int((64 - (gh * scale)) / 2)
    px = gx * scale + scale // 2 + x_pad
    py = gy * scale + scale // 2 + y_pad
    return px, py


def _frame_to_rgb(frame: np.ndarray) -> Image.Image:
    flat = frame.astype(np.int16).clip(0, 15)
    rgb = _LUT[flat]
    return Image.fromarray(rgb, mode="RGB")


def main() -> None:
    out = ROOT / "assets" / "sy01.gif"
    out.parent.mkdir(parents=True, exist_ok=True)

    mod = _load_sy01_module()
    grid_w = mod.GRID_WIDTH
    grid_h = mod.GRID_WIDTH

    def mirror(px: int, py: int) -> tuple[int, int]:
        return (grid_w - 1 - px, py)

    arc = Arcade(
        environments_dir=str(ROOT / "environment_files"),
        operation_mode=OperationMode.OFFLINE,
    )
    env = arc.make(full_game_id_for_stem("sy01"), seed=0, render_mode=None)
    res = env.reset()

    images: list[Image.Image] = []

    def push_repeats(arr: np.ndarray, n: int) -> None:
        base = _frame_to_rgb(arr)
        for _ in range(n):
            images.append(base.copy())

    push_repeats(res.frame[0], 10)

    win_defer = 12
    levels_to_play = 3

    for li in range(levels_to_play):
        level = mod.levels[li]
        pattern = level.get_data("pattern_positions")
        targets = sorted(mirror(px, py) for px, py in pattern)

        for mx, my in targets:
            dx, dy = _grid_center_display(grid_w, grid_h, mx, my)
            res = env.step(GameAction.ACTION6, data={"x": dx, "y": dy})
            push_repeats(res.frame[0], 2)

        for _ in range(win_defer):
            res = env.step(GameAction.ACTION6, data={"x": 0, "y": 0})
            push_repeats(res.frame[0], 1)

        push_repeats(res.frame[0], 8)

        if res.state.name == "WIN":
            break

    images[0].save(
        out,
        save_all=True,
        append_images=images[1:],
        duration=120,
        loop=0,
        optimize=False,
    )
    print(f"Wrote {out} ({len(images)} frames)")


if __name__ == "__main__":
    main()
