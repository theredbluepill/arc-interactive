#!/usr/bin/env python3
"""Regenerate preview GIFs using registry_gif_lib (multi-level + wall-bump fails).

Slices [GAMES.md](GAMES.md) table order via ``--from`` / ``--through``.
Per-game options: [scripts/registry_gif_overrides.json](registry_gif_overrides.json).

Example::

    uv run python scripts/render_registry_gifs.py --from pb01 --through bn03 -v
"""

from __future__ import annotations

import argparse
import re
import sys

from gif_common import repo_root, save_gif
from gif_inventory import parse_games_table
from registry_gif_lib import load_overrides, record_registry_gif


def _slice_ids(all_ids: list[str], from_id: str | None, through_id: str | None) -> list[str]:
    if from_id is None and through_id is None:
        return list(all_ids)
    if from_id is not None and from_id not in all_ids:
        raise SystemExit(f"--from {from_id!r} not in GAMES.md table order")
    if through_id is not None and through_id not in all_ids:
        raise SystemExit(f"--through {through_id!r} not in GAMES.md table order")
    i0 = 0 if from_id is None else all_ids.index(from_id)
    i1 = len(all_ids) - 1 if through_id is None else all_ids.index(through_id)
    if i1 < i0:
        raise SystemExit("--through must not come before --from in table order")
    return all_ids[i0 : i1 + 1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--from",
        dest="from_id",
        metavar="STEM",
        help="First game id in GAMES.md order (inclusive)",
    )
    parser.add_argument(
        "--through",
        dest="through_id",
        metavar="STEM",
        help="Last game id in GAMES.md order (inclusive)",
    )
    parser.add_argument(
        "--game",
        type=str,
        help="Single stem (e.g. pb01); ignores --from/--through",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Exploration RNG seed offset (default: 0)",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    root = repo_root()
    md_text = (root / "GAMES.md").read_text(encoding="utf-8")
    table_ids = [g for g, _ in parse_games_table(md_text)]

    if args.game:
        gid = args.game.strip().lower()
        if not re.match(r"^[a-z]{2}\d{2}$", gid):
            parser.error("invalid --game id")
        stems = [gid]
    else:
        stems = _slice_ids(table_ids, args.from_id, args.through_id)

    overrides_all = load_overrides(root)
    failed: list[tuple[str, str]] = []

    for stem in stems:
        try:
            ovr = overrides_all.get(stem)
            ovr_dict = ovr if isinstance(ovr, dict) else None
            _, images = record_registry_gif(
                stem,
                root,
                overrides=ovr_dict,
                verbose=args.verbose,
                seed=args.seed,
            )
            out = root / "assets" / f"{stem}.gif"
            save_gif(out, images, duration_ms=150)
            if args.verbose:
                print(f"  wrote {out} ({len(images)} frames)")
            else:
                print(stem, "ok", len(images), "frames")
        except Exception as e:  # noqa: BLE001
            failed.append((stem, f"{type(e).__name__}: {e}"))
            print(stem, "FAIL", e, file=sys.stderr)

    if failed:
        for g, err in failed:
            print(f"{g}: {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
