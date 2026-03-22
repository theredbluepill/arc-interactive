#!/usr/bin/env python3
"""Inventory: GAMES.md stems vs ``environment_files/`` and ``len(levels)`` from each module.

Writes ``devtools/reports/solvability_inventory.json`` by default.

Example::

    uv run python devtools/solvability_inventory.py
    uv run python devtools/solvability_inventory.py --json -  # stdout
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from solvability_common import (
    REPORTS_DIR,
    canonical_version_for_stem,
    games_md_level_column,
    level_count_from_stem_module,
    list_environment_stems,
    parse_games_md_stems,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=REPORTS_DIR / "solvability_inventory.json",
        help="Output JSON path (default: devtools/reports/solvability_inventory.json)",
    )
    parser.add_argument(
        "--json",
        metavar="PATH",
        nargs="?",
        const="-",
        default=None,
        help="Also print JSON to PATH or stdout when '-'",
    )
    args = parser.parse_args()

    games_stems = set(parse_games_md_stems())
    env_stems = set(list_environment_stems())
    rows: list[dict[str, object]] = []
    for stem in sorted(games_stems | env_stems, key=str.lower):
        ver = None
        n_levels = None
        err = None
        try:
            ver = canonical_version_for_stem(stem)
            n_levels = level_count_from_stem_module(stem, ver)
        except Exception as e:
            err = f"{type(e).__name__}: {e}"
        rows.append(
            {
                "stem": stem,
                "in_games_md": stem in games_stems,
                "in_environment_files": stem in env_stems,
                "canonical_version": ver,
                "levels_in_module": n_levels,
                "games_md_levels_cell": games_md_level_column(stem),
                "inventory_error": err,
            }
        )

    payload = {
        "games_md_stem_count": len(games_stems),
        "environment_stem_count": len(env_stems),
        "only_games_md": sorted(games_stems - env_stems, key=str.lower),
        "only_environment_files": sorted(env_stems - games_stems, key=str.lower),
        "stems": rows,
    }

    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text, encoding="utf-8")
    print(f"wrote {args.out}")
    if args.json is not None:
        if args.json == "-":
            sys.stdout.write(text)
        else:
            Path(args.json).write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
