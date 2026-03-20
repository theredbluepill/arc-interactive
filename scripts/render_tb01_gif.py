#!/usr/bin/env python3
"""
Record tb01 levels 1–5 into assets/tb01.gif.
Action plans are hand-authored to match environment_files/tb01/<ver>/tb01.py (no search).
ACTION1–4 = U,D,L,R; ("c", gx, gy) = ACTION6 at cell center in display space.
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
from env_resolve import full_game_id_for_stem  # noqa: E402

TB_GRID_W = TB_GRID_H = 24

U, D, L, R = 1, 2, 3, 4


def C(gx: int, gy: int) -> tuple[str, int, int]:
    return ("c", gx, gy)


# fmt: off
LEVEL_PLANS: list[list[int | tuple[str, int, int]]] = [
    # L1: straight east
    [C(x, 12) for x in range(6, 17)] + [R] * 13,
    # L2: three islands on y=12
    [C(x, 12) for x in range(6, 11)]
    + [R] * 7
    + [C(x, 12) for x in range(14, 19)]
    + [R] * 8,
    # L3: east along y=4, south to middle, east+south to goal
    [C(x, 4) for x in range(6, 12)]
    + [R] * 7
    + [C(11, y) for y in range(5, 11)]
    + [D] * 7
    + [R, R, D]
    + [C(x, 12) for x in range(14, 19)]
    + [R] * 5
    + [C(18, y) for y in range(13, 20)]
    + [D] * 7
    + [R],
    # L4: three stops on y=8, then south on x=20 (need (20,8) before column)
    [C(x, 8) for x in range(6, 11)]
    + [R] * 7
    + [C(x, 8) for x in range(14, 19)]
    + [R] * 9
    + [C(20, y) for y in range(9, 20)]
    + [D] * 11,
    # L5: same east–east row as L2 (extra islands / reefs are off the channel)
    [C(x, 12) for x in range(6, 11)]
    + [R] * 7
    + [C(x, 12) for x in range(14, 19)]
    + [R] * 8,
]
# fmt: on

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

_ACTIONS = {1: GameAction.ACTION1, 2: GameAction.ACTION2, 3: GameAction.ACTION3, 4: GameAction.ACTION4}


def _grid_center_display(gx: int, gy: int) -> tuple[int, int]:
    scale = min(64 // TB_GRID_W, 64 // TB_GRID_H)
    pad = int((64 - TB_GRID_W * scale) / 2)
    return (
        gx * scale + scale // 2 + pad,
        gy * scale + scale // 2 + pad,
    )


def _frame_to_rgb(frame: np.ndarray) -> Image.Image:
    flat = frame.astype(np.int16).clip(0, 15)
    rgb = _LUT[flat]
    return Image.fromarray(rgb, mode="RGB")


def main() -> None:
    out = ROOT / "assets" / "tb01.gif"
    out.parent.mkdir(parents=True, exist_ok=True)

    arc = Arcade(
        environments_dir=str(ROOT / "environment_files"),
        operation_mode=OperationMode.OFFLINE,
    )
    env = arc.make(full_game_id_for_stem("tb01"), seed=0, render_mode=None)
    res = env.reset()

    images: list[Image.Image] = []

    def push_repeats(arr: np.ndarray, n: int) -> None:
        base = _frame_to_rgb(arr)
        for _ in range(n):
            images.append(base.copy())

    push_repeats(res.frame[0], 10)

    for plan in LEVEL_PLANS:
        push_repeats(res.frame[0], 6)
        for act in plan:
            if isinstance(act, tuple) and act[0] == "c":
                cx, cy = _grid_center_display(act[1], act[2])
                res = env.step(GameAction.ACTION6, data={"x": cx, "y": cy})
                push_repeats(res.frame[0], 2)
            else:
                res = env.step(_ACTIONS[int(act)])
                push_repeats(res.frame[0], 1)
        push_repeats(res.frame[0], 14)

    images[0].save(
        out,
        save_all=True,
        append_images=images[1:],
        duration=115,
        loop=0,
        optimize=False,
    )
    print(f"Wrote {out} ({len(images)} frames), {len(LEVEL_PLANS)} levels")


if __name__ == "__main__":
    main()
