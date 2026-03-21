#!/usr/bin/env python3
"""Record assets/ll01.gif: full 5-level clear (toggle target 2×2 blocks, then N Conway steps).

Strategy (verified against ``Ll01``): each level’s target is a union of 2×2 still-lifes; toggling
those cells on then applying exactly ``need_generations`` ACTION5 steps leaves the pattern
unchanged and matches the target on the final check. ``next_level()`` loads a fresh board.

Uses only the **last** raster per env step so the GIF clearly shows level-to-level progression.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(ROOT))

from env_resolve import full_game_id_for_stem, load_stem_game_py  # noqa: E402
from gif_common import frame_to_rgb, observation_frame_layers, repo_root  # noqa: E402

from arc_agi import Arcade, OperationMode
from arcengine import GameAction, GameState

_ll = load_stem_game_py("ll01", "ll01_gif")

OUTPUT = repo_root() / "assets" / "ll01.gif"
ENV_DIR = str(repo_root() / "environment_files")

CAM_W = CAM_H = 32

MS_OPEN = 480
MS_TOGGLE = 140
MS_AFTER_PATTERN = 260
MS_STEP = 280
MS_LEVEL_BREAK = 520
MS_END = 600

A5 = GameAction.ACTION5
A6 = GameAction.ACTION6


def grid_to_display(gx: int, gy: int) -> tuple[int, int]:
    """Center of cell in ACTION6 64×64 space (matches ``Camera.display_to_grid`` inverse)."""
    scale = min(64 // CAM_W, 64 // CAM_H)
    pad = (64 - CAM_W * scale) // 2
    return gx * scale + scale // 2 + pad, gy * scale + scale // 2 + pad


def main() -> None:
    arc = Arcade(environments_dir=ENV_DIR, operation_mode=OperationMode.OFFLINE)
    env = arc.make(full_game_id_for_stem("ll01"), seed=0, include_frame_data=True)
    obs = env.reset()
    if obs is None:
        raise RuntimeError("reset returned None")

    images: list[Image.Image] = []
    durations: list[int] = []

    def snap_latest(ms: int) -> None:
        layers = observation_frame_layers(obs)
        if not layers:
            return
        images.append(frame_to_rgb(layers[-1]))
        durations.append(ms)

    def hold_last(ms: int, times: int) -> None:
        if not images:
            return
        last = images[-1]
        for _ in range(times):
            images.append(last.copy())
            durations.append(ms)

    def step_action(
        a: GameAction,
        data: dict[str, int] | None = None,
        *,
        ms: int,
    ) -> None:
        nonlocal obs
        nxt = env.step(a, reasoning={}, data=data if data is not None else {})
        if nxt is None:
            raise RuntimeError("env.step returned None")
        obs = nxt
        snap_latest(ms)

    snap_latest(MS_OPEN)

    n_levels = len(_ll.levels)
    for li, lv in enumerate(_ll.levels):
        raw = lv.get_data("target_cells") or []
        cells = sorted(tuple(int(t) for t in p) for p in raw)
        need = int(lv.get_data("need_generations") or 1)

        for gx, gy in cells:
            dx, dy = grid_to_display(gx, gy)
            step_action(A6, {"x": dx, "y": dy}, ms=MS_TOGGLE)

        hold_last(MS_AFTER_PATTERN, 2)

        for _ in range(need):
            step_action(A5, None, ms=MS_STEP)

        if obs.state == GameState.GAME_OVER:
            raise RuntimeError(f"GAME_OVER after level {li + 1} (scripted solution should pass)")
        if li < n_levels - 1 and obs.state not in (GameState.NOT_FINISHED,):
            raise RuntimeError(f"unexpected state {obs.state} after level {li + 1}")

        hold_last(MS_LEVEL_BREAK, 1 if li < n_levels - 1 else 2)

    if obs.state != GameState.WIN:
        raise RuntimeError(f"expected WIN after {n_levels} levels, got {obs.state}")

    hold_last(MS_END, 8)

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
