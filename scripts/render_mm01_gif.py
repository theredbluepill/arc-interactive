#!/usr/bin/env python3
"""Record assets/mm01.gif: levels 1–3, slow pacing, 2–3 deliberate mismatches (flip-back), then full clears."""

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

_mm = load_stem_game_py("mm01", "mm01_gif")
LEVEL_DIMS = _mm.LEVEL_DIMS
LEVEL_LAYOUTS = _mm.LEVEL_LAYOUTS
_compute_tile_size_and_offsets = _mm._compute_tile_size_and_offsets

OUTPUT = ROOT / "assets" / "mm01.gif"
ENV_DIR = str(ROOT / "environment_files")

# Slower pacing so markdown previews read clearly
MS_OPEN = 480
MS_CLICK = 260
MS_FLIPBACK = 320  # two steps while wrong pair waits to hide — slightly longer to read
MS_AFTER_LEVEL = 420
MS_END_HOLD = 520
LEVELS_TO_SHOW = 3
# Wrong-pair → flip-back before solving (slots 0 & 1 differ on L1–3). Use 2 or 3 True’s.
MISMATCHES_PER_LEVEL: tuple[bool, ...] = (True, True, False)  # 2 fails; set L3 True for 3


def tile_center(level_index: int, row: int, col: int) -> tuple[int, int]:
    rows, cols = LEVEL_DIMS[level_index]
    ts, ox, oy = _compute_tile_size_and_offsets(rows, cols)
    return ox + col * ts + ts // 2, oy + row * ts + ts // 2


def pair_click_sequence(level_index: int) -> list[tuple[int, int]]:
    """Row/col per click: for each color pair, lower slot index then higher."""
    layout = LEVEL_LAYOUTS[level_index]
    _, cols = LEVEL_DIMS[level_index]
    by_color: dict[int, list[int]] = {}
    for idx, color in enumerate(layout):
        by_color.setdefault(color, []).append(idx)
    pairs: list[tuple[int, int]] = []
    for slots in by_color.values():
        assert len(slots) == 2
        a, b = sorted(slots)
        pairs.append((a, b))
    pairs.sort(key=lambda ab: ab[0])
    out: list[tuple[int, int]] = []
    for a, b in pairs:
        for slot in (a, b):
            r, c = divmod(slot, cols)
            out.append((r, c))
    return out


def slot_center(level_index: int, slot: int) -> tuple[int, int]:
    _, cols = LEVEL_DIMS[level_index]
    r, c = divmod(slot, cols)
    return tile_center(level_index, r, c)


def frame_to_image(frame) -> Image.Image:
    arr = np.asarray(frame[0], dtype=np.uint8)
    h, w = arr.shape
    rgb = np.zeros((h, w, 3), dtype=np.uint8)
    for idx, hx in COLOR_MAP.items():
        rgb[arr == idx] = hex_to_rgb(hx)
    return Image.fromarray(rgb, "RGB")


def main() -> None:
    arc = Arcade(environments_dir=ENV_DIR, operation_mode=OperationMode.NORMAL)
    env = arc.make(full_game_id_for_stem("mm01"), seed=0, include_frame_data=True)
    obs = env.reset()

    images: list[Image.Image] = []
    durations: list[int] = []

    def snap(ms: int) -> None:
        images.append(frame_to_image(obs.frame))
        durations.append(ms)

    snap(MS_OPEN)

    def step_click(x: int, y: int, ms: int = MS_CLICK) -> None:
        nonlocal obs
        obs = env.step(GameAction.ACTION6, data={"x": x, "y": y}, reasoning={})
        snap(ms)

    def step_idle(ms: int = MS_FLIPBACK) -> None:
        nonlocal obs
        obs = env.step(GameAction.ACTION6, data={"x": 0, "y": 0}, reasoning={})
        snap(ms)

    def hold_same(ms: int, times: int) -> None:
        for _ in range(times):
            snap(ms)

    def deliberate_mismatch(level_index: int, slot_a: int = 0, slot_b: int = 1) -> None:
        layout = LEVEL_LAYOUTS[level_index]
        if layout[slot_a] == layout[slot_b]:
            raise ValueError(f"L{level_index + 1}: slots {slot_a},{slot_b} same color")
        step_click(*slot_center(level_index, slot_a))
        step_click(*slot_center(level_index, slot_b))
        step_idle()
        step_idle()

    for level_index in range(LEVELS_TO_SHOW):
        if level_index < len(MISMATCHES_PER_LEVEL) and MISMATCHES_PER_LEVEL[level_index]:
            deliberate_mismatch(level_index)
        for row, col in pair_click_sequence(level_index):
            prev_lc = getattr(obs, "levels_completed", 0) or 0
            step_click(*tile_center(level_index, row, col))
            new_lc = getattr(obs, "levels_completed", 0) or 0
            if new_lc > prev_lc:
                hold_same(MS_AFTER_LEVEL, 3)

    if (getattr(obs, "levels_completed", 0) or 0) < LEVELS_TO_SHOW:
        raise RuntimeError(
            f"expected {LEVELS_TO_SHOW} levels cleared, got {getattr(obs, 'levels_completed', 0)}"
        )
    if obs.state != GameState.NOT_FINISHED:
        raise RuntimeError(f"expected still playing after L{LEVELS_TO_SHOW}, got {obs.state}")

    hold_same(MS_END_HOLD, 4)

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
