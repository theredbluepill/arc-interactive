#!/usr/bin/env python3
"""Record assets/ff01.gif: full episode (all 5 levels) with click ripple after each fill."""

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

_ff = load_stem_game_py("ff01", "ff01_gif")
Ff01UI = _ff.Ff01UI
LEVEL_CONFIGS = _ff.LEVEL_CONFIGS

OUTPUT = ROOT / "assets" / "ff01.gif"
ENV_DIR = str(ROOT / "environment_files")

A1 = GameAction.ACTION1

MS_OPEN = 400
MS_MOVE = 160
MS_HOLD = 180
MS_END = 500


def frame_to_image_layer(layer) -> Image.Image:
    arr = np.asarray(layer, dtype=np.uint8)
    h, w = arr.shape
    rgb = np.zeros((h, w, 3), dtype=np.uint8)
    for idx, hx in COLOR_MAP.items():
        rgb[arr == idx] = hex_to_rgb(hx)
    return Image.fromarray(rgb, "RGB")


def main() -> None:
    arc = Arcade(environments_dir=ENV_DIR, operation_mode=OperationMode.OFFLINE)
    env = arc.make(full_game_id_for_stem("ff01"), seed=0, include_frame_data=True)
    obs = env.reset()

    images: list[Image.Image] = []
    durations: list[int] = []

    def snap_all(ms: int) -> None:
        fr = getattr(obs, "frame", None) or []
        for layer in fr:
            images.append(frame_to_image_layer(layer))
            durations.append(ms)

    snap_all(MS_OPEN)

    def step_action(
        a: GameAction, data: dict[str, int] | None = None, ms: int = MS_MOVE
    ) -> None:
        nonlocal obs
        obs = env.step(a, reasoning={}, data=data if data is not None else {})
        snap_all(ms)

    n_levels = len(LEVEL_CONFIGS)
    for li in range(n_levels):
        g = env._game
        for enc in g._shapes:
            gx, gy = enc.interior[len(enc.interior) // 2]
            step_action(GameAction.ACTION6, {"x": gx, "y": gy}, MS_MOVE)
            for _ in range(Ff01UI.CLICK_ANIM_FRAMES):
                step_action(A1, None, MS_HOLD)

        if li < n_levels - 1:
            want = li + 1
            if env._game._current_level_index != want:
                raise RuntimeError(
                    f"after level {li + 1} expected level_index {want}, "
                    f"got {env._game._current_level_index}"
                )

    if obs.state != GameState.WIN:
        raise RuntimeError(f"expected WIN after {n_levels} levels, got {obs.state}")
    # FrameDataRaw often reports levels_completed==0 on terminal WIN; WIN alone is authoritative.

    last = images[-1]
    for _ in range(5):
        images.append(last.copy())
        durations.append(MS_END)

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
