#!/usr/bin/env python3
"""Record a scripted playthrough of ul01 and write assets/ul01.gif (64×64)."""

from __future__ import annotations

from PIL import Image

from env_resolve import full_game_id_for_stem
from gif_common import (
    ACTIONS_UDLR,
    append_frame_repeats,
    offline_arcade,
    repo_root,
    save_gif,
)


def main() -> None:
    root = repo_root()
    out = root / "assets" / "ul01.gif"

    # Full solution (all 5 levels); L4/L5 need correct key-before-door ordering.
    seq = (
        "RRDDRRRUU"  # L1
        + "RRRRDDDDRRUU"  # L2
        + "RRRDDDRRRDDD"  # L3
        + "RRRDDDRRRRUUU"  # L4: (0,0)->(3,3)->(7,0)
        + "UUUUUUURRRRRRRDDDDDDD"  # L5: (0,7)->(7,0)->(7,7)
    )

    m = ACTIONS_UDLR

    arc = offline_arcade(root)
    env = arc.make(full_game_id_for_stem("ul01"), seed=0, render_mode=None)
    res = env.reset()

    images: list[Image.Image] = []

    append_frame_repeats(images, res.frame[0], 6)

    for ch in seq:
        res = env.step(m[ch])
        append_frame_repeats(images, res.frame[0], 2)

    append_frame_repeats(images, res.frame[0], 12)

    save_gif(out, images, duration_ms=150)
    print(f"Wrote {out} ({len(images)} frames)")


if __name__ == "__main__":
    main()
