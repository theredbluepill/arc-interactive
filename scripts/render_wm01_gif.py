#!/usr/bin/env python3
"""Record a scripted whack-a-mole demo for wm01 and write assets/wm01.gif (64×64)."""

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


def _frame_to_rgb(frame: np.ndarray) -> Image.Image:
    flat = frame.astype(np.int16).clip(0, 15)
    rgb = _LUT[flat]
    return Image.fromarray(rgb, mode="RGB")


def _click_for_mole(mx: int, my: int) -> dict[str, int]:
    """Display coords for ACTION6; must match wm01.step grid_x = x // 2."""
    gx, gy = mx + 2, my + 2
    return {"x": gx * 2 + 1, "y": gy * 2 + 1}


def _step_auto(env, game) -> None:
    mp = game.get_mole_position()
    if mp:
        mx, my = mp
        env.step(GameAction.ACTION6, data=_click_for_mole(mx, my))
    else:
        env.step(GameAction.ACTION6, data={"x": 0, "y": 0})


def main() -> None:
    out = ROOT / "assets" / "wm01.gif"
    out.parent.mkdir(parents=True, exist_ok=True)

    # Enough steps to clear level 1 (difficulty 1) and show a few moles on level 2.
    max_steps = 72

    arc = Arcade(
        environments_dir=str(ROOT / "environment_files"),
        operation_mode=OperationMode.OFFLINE,
    )
    env = arc.make(full_game_id_for_stem("wm01"), seed=0, render_mode=None)
    res = env.reset()
    game = env._game

    images: list[Image.Image] = []

    def push_repeats(arr: np.ndarray, n: int) -> None:
        base = _frame_to_rgb(arr)
        for _ in range(n):
            images.append(base.copy())

    push_repeats(res.frame[0], 8)

    for _ in range(max_steps):
        _step_auto(env, game)
        res = env._last_response
        push_repeats(res.frame[0], 2)

    push_repeats(res.frame[0], 14)

    images[0].save(
        out,
        save_all=True,
        append_images=images[1:],
        duration=150,
        loop=0,
        optimize=False,
    )
    print(f"Wrote {out} ({len(images)} frames, {max_steps} steps, seed=0)")


if __name__ == "__main__":
    main()
