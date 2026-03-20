#!/usr/bin/env python3
"""Record an auto-played sv01 demo (levels 1–3) and write assets/sv01.gif (64×64)."""

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

_DIRS = [
    ((0, -1), GameAction.ACTION1),
    ((0, 1), GameAction.ACTION2),
    ((-1, 0), GameAction.ACTION3),
    ((1, 0), GameAction.ACTION4),
]


def _frame_to_rgb(frame: np.ndarray) -> Image.Image:
    flat = frame.astype(np.int16).clip(0, 15)
    rgb = _LUT[flat]
    return Image.fromarray(rgb, mode="RGB")


def _jiggle_warm(
    pos: tuple[int, int],
    warm: set[tuple[int, int]],
    gw: int,
    gh: int,
) -> GameAction:
    px, py = pos
    for (dx, dy), act in _DIRS:
        nx, ny = px + dx, py + dy
        if 0 <= nx < gw and 0 <= ny < gh and (nx, ny) in warm:
            return act
    return GameAction.ACTION4


def _warm_or_jiggle(
    pos: tuple[int, int],
    in_warm: bool,
    warm: set[tuple[int, int]],
    gw: int,
    gh: int,
) -> GameAction:
    if in_warm:
        return GameAction.ACTION5
    return _jiggle_warm(pos, warm, gw, gh)


def _bfs_first_action(
    start: tuple[int, int],
    goals: set[tuple[int, int]],
    grid_w: int,
    grid_h: int,
) -> GameAction | None:
    if start in goals:
        return None
    q = deque([(start[0], start[1], None)])
    seen = {start}
    while q:
        x, y, first = q.popleft()
        for (dx, dy), aid in _DIRS:
            nx, ny = x + dx, y + dy
            if not (0 <= nx < grid_w and 0 <= ny < grid_h):
                continue
            if (nx, ny) in seen:
                continue
            seen.add((nx, ny))
            nf = aid if first is None else first
            if (nx, ny) in goals:
                return nf
            q.append((nx, ny, nf))
    return GameAction.ACTION1


def _policy(game) -> GameAction:
    level = game.current_level
    gw, gh = level.grid_size
    px, py = game._player.x, game._player.y
    warm = {(s.x, s.y) for s in level.get_sprites_by_tag("warm_zone")}
    food = {(s.x, s.y) for s in level.get_sprites_by_tag("food")}
    h, w = game._hunger, game._warmth
    pos = (px, py)
    in_warm = pos in warm
    if w <= 40 or (not in_warm and w <= 60):
        return _bfs_first_action(pos, warm, gw, gh) or _warm_or_jiggle(
            pos, in_warm, warm, gw, gh
        )
    if h <= 50 and food:
        return _bfs_first_action(pos, food, gw, gh) or _warm_or_jiggle(
            pos, in_warm, warm, gw, gh
        )
    if not in_warm:
        return _bfs_first_action(pos, warm, gw, gh) or _warm_or_jiggle(
            pos, in_warm, warm, gw, gh
        )
    if h <= 75 and food:
        return _bfs_first_action(pos, food, gw, gh) or GameAction.ACTION5
    return GameAction.ACTION5


def main() -> None:
    out = ROOT / "assets" / "sv01.gif"
    out.parent.mkdir(parents=True, exist_ok=True)

    # Three survival blocks (8→12→16); bot is tuned for these sizes.
    max_steps = 180

    arc = Arcade(
        environments_dir=str(ROOT / "environment_files"),
        operation_mode=OperationMode.OFFLINE,
    )
    env = arc.make(full_game_id_for_stem("sv01"), seed=0, render_mode=None)
    res = env.reset()
    game = env._game

    images: list[Image.Image] = []

    def push_repeats(arr: np.ndarray, n: int) -> None:
        base = _frame_to_rgb(arr)
        for _ in range(n):
            images.append(base.copy())

    push_repeats(res.frame[0], 6)

    for _ in range(max_steps):
        res = env.step(_policy(game))
        push_repeats(res.frame[0], 1)
        if res.state.name not in ("NOT_FINISHED",):
            break

    push_repeats(res.frame[0], 12)

    images[0].save(
        out,
        save_all=True,
        append_images=images[1:],
        duration=90,
        loop=0,
        optimize=False,
    )
    print(f"Wrote {out} ({len(images)} frames, seed=0)")


if __name__ == "__main__":
    main()
