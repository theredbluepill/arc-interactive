#!/usr/bin/env python3
"""Record a scripted playthrough of tt01 and write assets/tt01.gif (64×64)."""

from __future__ import annotations

import sys
from collections import deque
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

_MOVE_CHARS = {
    "U": (0, -1),
    "D": (0, 1),
    "L": (-1, 0),
    "R": (1, 0),
}


def _load_tt01_levels():
    return load_stem_game_py("tt01", "tt01_levels").levels


def _bfs_path(
    start: tuple[int, int],
    goal: tuple[int, int],
    grid_w: int,
    grid_h: int,
    blocked: set[tuple[int, int]],
) -> str | None:
    sx, sy = start
    gx, gy = goal
    if (gx, gy) in blocked:
        return None
    q = deque([(sx, sy, "")])
    seen = {(sx, sy)}
    while q:
        x, y, path = q.popleft()
        if (x, y) == (gx, gy):
            return path
        for ch, (dx, dy) in _MOVE_CHARS.items():
            nx, ny = x + dx, y + dy
            if not (0 <= nx < grid_w and 0 <= ny < grid_h):
                continue
            if (nx, ny) in blocked:
                continue
            if (nx, ny) not in seen:
                seen.add((nx, ny))
                q.append((nx, ny, path + ch))
    return None


def _greedy_collect_path(level) -> str:
    gw, gh = level.grid_size
    blocked: set[tuple[int, int]] = set()
    targets: list[tuple[int, int]] = []
    start: tuple[int, int] | None = None
    for sp in level.get_sprites():
        tags = sp.tags
        if "player" in tags:
            start = (sp.x, sp.y)
        elif "wall" in tags or "hazard" in tags:
            blocked.add((sp.x, sp.y))
        elif "target" in tags:
            targets.append((sp.x, sp.y))
    assert start is not None
    pos = start
    out = ""
    remaining = list(targets)
    while remaining:
        best_path: str | None = None
        best_goal: tuple[int, int] | None = None
        for g in remaining:
            p = _bfs_path(pos, g, gw, gh, blocked)
            if p is None:
                raise RuntimeError(f"Unreachable target {g} from {pos}")
            if best_path is None or len(p) < len(best_path):
                best_path = p
                best_goal = g
        assert best_path is not None and best_goal is not None
        out += best_path
        pos = best_goal
        remaining.remove(best_goal)
    return out


def _frame_to_rgb(frame: np.ndarray) -> Image.Image:
    flat = frame.astype(np.int16).clip(0, 15)
    rgb = _LUT[flat]
    return Image.fromarray(rgb, mode="RGB")


def main() -> None:
    out = ROOT / "assets" / "tt01.gif"
    out.parent.mkdir(parents=True, exist_ok=True)

    seq = "".join(_greedy_collect_path(lv) for lv in _load_tt01_levels())

    m = {
        "U": GameAction.ACTION1,
        "D": GameAction.ACTION2,
        "L": GameAction.ACTION3,
        "R": GameAction.ACTION4,
    }

    arc = Arcade(
        environments_dir=str(ROOT / "environment_files"),
        operation_mode=OperationMode.OFFLINE,
    )
    env = arc.make(full_game_id_for_stem("tt01"), seed=0, render_mode=None)
    res = env.reset()

    images: list[Image.Image] = []

    def push_repeats(arr: np.ndarray, n: int) -> None:
        base = _frame_to_rgb(arr)
        for _ in range(n):
            images.append(base.copy())

    push_repeats(res.frame[0], 6)

    for ch in seq:
        res = env.step(m[ch])
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
    print(f"Wrote {out} ({len(images)} frames, {len(seq)} moves)")


if __name__ == "__main__":
    main()
