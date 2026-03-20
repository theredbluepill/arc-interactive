#!/usr/bin/env python3
"""Record assets/ms01.gif: BFS clear level 1, then level 2 — walk east into a mine (GAME_OVER)."""

from __future__ import annotations

import sys
from collections import deque
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
from arcengine import GameAction, GameState, Level

MS_LEVELS = load_stem_game_py("ms01", "ms01_gif").levels

OUTPUT = ROOT / "assets" / "ms01.gif"
ENV_DIR = str(ROOT / "environment_files")

MS_OPEN = 480
MS_MOVE = 230
MS_DEATH_TICK = 130  # sub-frames inside one step (mine burst animation)
MS_AFTER_LEVEL = 450
MS_END_HOLD = 560
# Level 2 start (0,5): three rights → (3,5), a mine (see ms01.make_ms level 2).
L2_DEATH_MOVES: tuple[GameAction, ...] = (
    GameAction.ACTION4,
    GameAction.ACTION4,
    GameAction.ACTION4,
)

ACTION_BY_DELTA: dict[tuple[int, int], GameAction] = {
    (0, -1): GameAction.ACTION1,
    (0, 1): GameAction.ACTION2,
    (-1, 0): GameAction.ACTION3,
    (1, 0): GameAction.ACTION4,
}


def bfs_actions(level: Level) -> list[GameAction]:
    w, h = level.grid_size
    start = (level.get_sprites_by_tag("player")[0].x, level.get_sprites_by_tag("player")[0].y)
    goal = (level.get_sprites_by_tag("goal")[0].x, level.get_sprites_by_tag("goal")[0].y)
    mines = {(m.x, m.y) for m in level.get_sprites_by_tag("mine")}
    walls = {(s.x, s.y) for s in level.get_sprites_by_tag("wall")}
    if start in mines or goal in mines:
        raise ValueError("start or goal on mine")

    q: deque[tuple[int, int]] = deque([start])
    prev: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    while q:
        x, y = q.popleft()
        if (x, y) == goal:
            break
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nx, ny = x + dx, y + dy
            if not (0 <= nx < w and 0 <= ny < h):
                continue
            if (nx, ny) in mines or (nx, ny) in walls:
                continue
            if (nx, ny) not in prev:
                prev[(nx, ny)] = (x, y)
                q.append((nx, ny))

    if goal not in prev:
        raise RuntimeError(f"no safe path for level {level.name!r}")

    seg: list[tuple[tuple[int, int], tuple[int, int]]] = []
    cur = goal
    while cur != start:
        p = prev[cur]
        assert p is not None
        seg.append((p, cur))
        cur = p
    seg.reverse()

    out: list[GameAction] = []
    for (x, y), (nx, ny) in seg:
        d = (nx - x, ny - y)
        out.append(ACTION_BY_DELTA[d])
    return out


def frame_to_image_layer(layer) -> Image.Image:
    arr = np.asarray(layer, dtype=np.uint8)
    h, w = arr.shape
    rgb = np.zeros((h, w, 3), dtype=np.uint8)
    for idx, hx in COLOR_MAP.items():
        rgb[arr == idx] = hex_to_rgb(hx)
    return Image.fromarray(rgb, "RGB")


def main() -> None:
    arc = Arcade(environments_dir=ENV_DIR, operation_mode=OperationMode.NORMAL)
    env = arc.make(full_game_id_for_stem("ms01"), seed=0, include_frame_data=True)
    obs = env.reset()

    images: list[Image.Image] = []
    durations: list[int] = []

    def snap_all(ms: int) -> None:
        fr = getattr(obs, "frame", None) or []
        if not fr:
            return
        for layer in fr:
            images.append(frame_to_image_layer(layer))
            durations.append(ms)

    snap_all(MS_OPEN)

    def step_action(
        action: GameAction, ms: int = MS_MOVE, *, death_burst: bool = False
    ) -> None:
        nonlocal obs
        obs = env.step(action, reasoning={})
        tick_ms = MS_DEATH_TICK if death_burst else ms
        snap_all(tick_ms)

    def hold_same(ms: int, times: int) -> None:
        if not images:
            return
        last = images[-1]
        for _ in range(times):
            images.append(last)
            durations.append(ms)

    plan_l1 = bfs_actions(MS_LEVELS[0])
    for a in plan_l1:
        prev_lc = getattr(obs, "levels_completed", 0) or 0
        step_action(a)
        new_lc = getattr(obs, "levels_completed", 0) or 0
        if new_lc > prev_lc:
            hold_same(MS_AFTER_LEVEL, 3)

    if (getattr(obs, "levels_completed", 0) or 0) < 1:
        raise RuntimeError("expected level 1 clear")

    for i, a in enumerate(L2_DEATH_MOVES):
        step_action(a, death_burst=(i == len(L2_DEATH_MOVES) - 1))

    if obs.state != GameState.GAME_OVER:
        raise RuntimeError(f"expected GAME_OVER after mine, got {obs.state}")

    hold_same(MS_END_HOLD, 5)

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
