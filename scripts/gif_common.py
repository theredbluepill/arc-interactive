#!/usr/bin/env python3
"""Shared helpers for scripts/render_*_gif.py (palette, frames, GIF IO, Arcade bootstrap)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

import numpy as np
from PIL import Image

from arc_agi import Arcade, OperationMode
from arcengine import GameAction

# Terminal palette (arc-agi rendering.py / AGENTS.md) — index 0–15 -> RGBA hex, GIF uses RGB
TERMINAL_COLOR_HEX: dict[int, str] = {
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

_PALETTE_LUT: np.ndarray | None = None


def repo_root() -> Path:
    """arc-interactive root (parent of ``scripts/``)."""
    return Path(__file__).resolve().parents[1]


def palette_lut() -> np.ndarray:
    """256×3 uint8 LUT; indices 0–15 match TERMINAL_COLOR_HEX (rest zero)."""
    global _PALETTE_LUT
    if _PALETTE_LUT is None:
        lut = np.zeros((256, 3), dtype=np.uint8)
        for i, hx in TERMINAL_COLOR_HEX.items():
            lut[i] = (
                int(hx[1:3], 16),
                int(hx[3:5], 16),
                int(hx[5:7], 16),
            )
        _PALETTE_LUT = lut
    return _PALETTE_LUT


def frame_to_rgb(frame: np.ndarray | Any) -> Image.Image:
    """Convert a single H×W palette-index layer (values 0–15) to a PIL RGB image."""
    arr = np.asarray(frame)
    flat = arr.astype(np.int16).clip(0, 15)
    rgb = palette_lut()[flat]
    return Image.fromarray(rgb, mode="RGB")


def append_frame_repeats(
    images: list[Image.Image],
    frame: np.ndarray | Any,
    times: int,
) -> None:
    """Append ``times`` copies of ``frame`` as RGB stills (common GIF pacing)."""
    base = frame_to_rgb(frame)
    for _ in range(times):
        images.append(base.copy())


def observation_frame_layers(obs: Any) -> list[Any]:
    """Rasters from a reset/step observation. One action can yield multiple layers (e.g. level advance)."""
    fr = getattr(obs, "frame", None) or []
    return list(fr) if fr else []


def append_frame_repeats_latest(
    images: list[Image.Image],
    obs: Any,
    times: int,
) -> None:
    """Append ``times`` copies of the **last** layer — use this after ``env.step`` / ``env.reset``."""
    layers = observation_frame_layers(obs)
    if not layers:
        return
    append_frame_repeats(images, layers[-1], times)


def append_frame_repeats_each_layer(
    images: list[Image.Image],
    obs: Any,
    times_per_layer: int,
) -> None:
    """Append every sub-frame from ``obs.frame`` (shows mid-action transitions in GIFs)."""
    for layer in observation_frame_layers(obs):
        append_frame_repeats(images, layer, times_per_layer)


def _registry_ring_rgb(
    rgb: np.ndarray, h: int, w: int, cx: int, cy: int, r: int, col: np.ndarray
) -> None:
    if r <= 0:
        return
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if max(abs(dx), abs(dy)) != r:
                continue
            px, py = cx + dx, cy + dy
            if 0 <= px < w and 0 <= py < h:
                rgb[py, px] = col


def _registry_plus_rgb(
    rgb: np.ndarray, h: int, w: int, cx: int, cy: int, arm: int, col: np.ndarray
) -> None:
    if 0 <= cx < w and 0 <= cy < h:
        rgb[cy, cx] = col
    for a in range(1, arm + 1):
        for px, py in (
            (cx - a, cy),
            (cx + a, cy),
            (cx, cy - a),
            (cx, cy + a),
        ):
            if 0 <= px < w and 0 <= py < h:
                rgb[py, px] = col


def append_registry_click_ripple(
    images: list[Image.Image],
    base_palette_frame: np.ndarray | Any,
    cx: int,
    cy: int,
    *,
    phase_count: int = 14,
    repeats_per_phase: int = 2,
) -> None:
    """
    Chebyshev ring + plus at ``(cx,cy)`` in 64×64 **display** space, ff01/sq01-style.
    Used only when building **preview GIFs** — not part of shipped game logic.
    """
    lut = palette_lut()
    frozen = np.asarray(frame_to_rgb(base_palette_frame), dtype=np.uint8).copy()
    h, w = frozen.shape[:2]
    white = lut[0]
    yellow = lut[11]
    orange = lut[12]

    for phase in range(phase_count):
        layer = frozen.copy()
        if phase < 8:
            ring_r = phase + 1 if phase < 4 else 8 - phase
            if ring_r > 0:
                ring_col = white if ring_r >= 4 else (yellow if ring_r == 3 else orange)
                _registry_ring_rgb(layer, h, w, cx, cy, ring_r, ring_col)
        arm = 2 if phase < 10 else 1
        plus_col = white if phase < 2 else orange
        _registry_plus_rgb(layer, h, w, cx, cy, arm, plus_col)
        pil = Image.fromarray(layer)
        for _ in range(repeats_per_phase):
            images.append(pil.copy())


def save_gif(
    path: Path | str,
    images: Sequence[Image.Image],
    *,
    duration_ms: int | Sequence[int] = 150,
    loop: int = 0,
) -> None:
    """Write an animated GIF; ``duration_ms`` may be one int or one per frame."""
    outp = Path(path)
    outp.parent.mkdir(parents=True, exist_ok=True)
    if not images:
        raise ValueError("save_gif: no frames")
    duration: int | list[int]
    if isinstance(duration_ms, int):
        duration = duration_ms
    else:
        d = list(duration_ms)
        if len(d) != len(images):
            raise ValueError(
                f"duration_ms length {len(d)} != images length {len(images)}"
            )
        duration = d
    images[0].save(
        outp,
        save_all=True,
        append_images=list(images[1:]),
        duration=duration,
        loop=loop,
        optimize=False,
    )


def offline_arcade(root: Path | None = None) -> Arcade:
    """Arcade in OFFLINE mode with ``environment_files`` under repo root."""
    r = root or repo_root()
    return Arcade(
        environments_dir=str(r / "environment_files"),
        operation_mode=OperationMode.OFFLINE,
    )


# ACTION1–4 = up / down / left / right (matches most render scripts and GAMES.md)
ACTIONS_UDLR: dict[str, GameAction] = {
    "U": GameAction.ACTION1,
    "D": GameAction.ACTION2,
    "L": GameAction.ACTION3,
    "R": GameAction.ACTION4,
}

ACTIONS_BY_INT: dict[int, GameAction] = {
    1: GameAction.ACTION1,
    2: GameAction.ACTION2,
    3: GameAction.ACTION3,
    4: GameAction.ACTION4,
}


def grid_cell_center_display(
    gx: int,
    gy: int,
    *,
    grid_w: int,
    grid_h: int,
    frame_size: int = 64,
) -> tuple[int, int]:
    """
    Display pixel at the center of cell (gx, gy) for a square letterboxed grid
    in a ``frame_size``×``frame_size`` frame (same math as tb01 render script).
    """
    scale = min(frame_size // grid_w, frame_size // grid_h)
    pad = int((frame_size - grid_w * scale) / 2)
    return (
        gx * scale + scale // 2 + pad,
        gy * scale + scale // 2 + pad,
    )
