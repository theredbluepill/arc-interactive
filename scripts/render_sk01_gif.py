#!/usr/bin/env python3
"""BFS-solve sk01 levels 1–5 and record assets/sk01.gif (64×64)."""

from __future__ import annotations

from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

from arc_agi import Arcade, OperationMode
from arcengine import GameAction

ROOT = Path(__file__).resolve().parents[1]
import sys

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

_ACTIONS = {
    1: GameAction.ACTION1,
    2: GameAction.ACTION2,
    3: GameAction.ACTION3,
    4: GameAction.ACTION4,
}

_DELTAS = [(-1, 0, 1), (1, 0, 2), (0, -1, 3), (0, 1, 4)]


def _load_sk01_levels():
    return load_stem_game_py("sk01", "sk01_gif_mod").levels


def _parse_level(level):
    walls: set[tuple[int, int]] = set()
    targets: set[tuple[int, int]] = set()
    player: tuple[int, int] | None = None
    blocks: list[tuple[int, int]] = []
    gw, gh = level.grid_size
    for s in level.get_sprites():
        tgs = s.tags
        if "player" in tgs:
            player = (s.x, s.y)
        elif "wall" in tgs:
            walls.add((s.x, s.y))
        elif "target" in tgs:
            targets.add((s.x, s.y))
        elif "block" in tgs:
            blocks.append((s.x, s.y))
    assert player is not None
    return walls, targets, player, blocks, gw, gh


def _try_push(walls, gw, gh, px, py, blocks, dy, dx):
    nx, ny = px + dx, py + dy
    if not (0 <= nx < gw and 0 <= ny < gh):
        return None
    if (nx, ny) in walls:
        return None
    bl = list(blocks)
    if (nx, ny) not in bl:
        return (nx, ny, blocks)
    i = bl.index((nx, ny))
    bx, by = nx + dx, ny + dy
    if not (0 <= bx < gw and 0 <= by < gh):
        return None
    if (bx, by) in walls or (bx, by) in bl:
        return None
    bl[i] = (bx, by)
    return (nx, ny, tuple(sorted(bl)))


def _bfs_solve(level, max_nodes: int = 12_000_000) -> list[int] | None:
    walls, targets, (px, py), blocks, gw, gh = _parse_level(level)
    start_bl = tuple(sorted(blocks))
    if set(blocks) == targets:
        return []
    start = (px, py, start_bl)
    q = deque([start])
    came = {start: None}
    nodes = 0
    while q:
        nodes += 1
        if nodes > max_nodes:
            return None
        state = q.popleft()
        px, py, blks = state
        if set(blks) == targets:
            path = []
            cur = state
            while came[cur] is not None:
                prev, act = came[cur]
                path.append(act)
                cur = prev
            path.reverse()
            return path
        for dy, dx, act in _DELTAS:
            nxt = _try_push(walls, gw, gh, px, py, blks, dy, dx)
            if nxt is None:
                continue
            key = (nxt[0], nxt[1], nxt[2])
            if key not in came:
                came[key] = (state, act)
                q.append(key)
    return None


def _frame_to_rgb(frame: np.ndarray) -> Image.Image:
    flat = frame.astype(np.int16).clip(0, 15)
    rgb = _LUT[flat]
    return Image.fromarray(rgb, mode="RGB")


def main() -> None:
    out = ROOT / "assets" / "sk01.gif"
    out.parent.mkdir(parents=True, exist_ok=True)

    level_defs = _load_sk01_levels()
    plans = []
    for lv in level_defs:
        p = _bfs_solve(lv)
        if not p:
            raise RuntimeError("Unsolvable sk01 level in GIF script")
        plans.append(p)

    arc = Arcade(
        environments_dir=str(ROOT / "environment_files"),
        operation_mode=OperationMode.OFFLINE,
    )
    env = arc.make(full_game_id_for_stem("sk01"), seed=0, render_mode=None)
    res = env.reset()

    images: list[Image.Image] = []

    def push_repeats(arr: np.ndarray, n: int) -> None:
        base = _frame_to_rgb(arr)
        for _ in range(n):
            images.append(base.copy())

    push_repeats(res.frame[0], 10)

    for plan in plans:
        for act in plan:
            res = env.step(_ACTIONS[act])
            push_repeats(res.frame[0], 1)
        push_repeats(res.frame[0], 12)

    images[0].save(
        out,
        save_all=True,
        append_images=images[1:],
        duration=110,
        loop=0,
        optimize=False,
    )
    total_moves = sum(len(p) for p in plans)
    print(f"Wrote {out} ({len(images)} frames, {total_moves} moves)")


if __name__ == "__main__":
    main()
