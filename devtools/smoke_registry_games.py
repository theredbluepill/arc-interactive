#!/usr/bin/env python3
"""Smoke-test registry games: load via Arcade, random ACTION1–6 steps (no render).

Scans [GAMES.md](GAMES.md) table order. Use ``--from`` / ``--through`` to limit rows
(e.g. post-rs01 slice ``pb01`` … ``bn03``). Resolves ``metadata.json`` via the sole
version dir under each stem (or ``--version``).

Exit non-zero on exceptions. Random ACTION6 uses letterboxed cell centers (same as GIF scripts).
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from arc_agi import Arcade, OperationMode  # noqa: E402
from arcengine import GameAction, GameState  # noqa: E402
from gif_common import grid_cell_center_display  # noqa: E402
from env_resolve import sole_package_version  # noqa: E402
from gif_inventory import parse_games_table  # noqa: E402

GAMES_MD = ROOT / "GAMES.md"
ENV_DIR = ROOT / "environment_files"


def _slice_ids(all_ids: list[str], from_id: str | None, through_id: str | None) -> list[str]:
    if from_id is None and through_id is None:
        return list(all_ids)
    if from_id is not None and from_id not in all_ids:
        raise SystemExit(f"--from {from_id!r} not found in GAMES.md table order")
    if through_id is not None and through_id not in all_ids:
        raise SystemExit(f"--through {through_id!r} not found in GAMES.md table order")
    i0 = 0 if from_id is None else all_ids.index(from_id)
    i1 = len(all_ids) - 1 if through_id is None else all_ids.index(through_id)
    if i1 < i0:
        raise SystemExit("--through must not come before --from in table order")
    return all_ids[i0 : i1 + 1]


def _load_full_game_id(stem: str, version: str) -> str:
    if version == "auto":
        version = sole_package_version(stem)
    meta = ENV_DIR / stem / version / "metadata.json"
    if not meta.is_file():
        raise FileNotFoundError(f"Missing metadata: {meta}")
    data = json.loads(meta.read_text(encoding="utf-8"))
    gid = data.get("game_id")
    if not isinstance(gid, str):
        raise ValueError(f"{meta}: missing string game_id")
    return gid


def _pick_action(
    rng,
    level,
    *,
    move_weight: int,
    a5_weight: int,
    a6_weight: int,
) -> tuple[GameAction, dict[str, int]]:
    gw, gh = level.grid_size
    total = move_weight * 4 + a5_weight + a6_weight
    r = rng.randint(1, total)
    if r <= move_weight * 4:
        k = (r - 1) // move_weight
        return (
            (GameAction.ACTION1, GameAction.ACTION2, GameAction.ACTION3, GameAction.ACTION4)[k],
            {},
        )
    r -= move_weight * 4
    if r <= a5_weight:
        return GameAction.ACTION5, {}
    gx = rng.randrange(0, gw)
    gy = rng.randrange(0, gh)
    cx, cy = grid_cell_center_display(gx, gy, grid_w=gw, grid_h=gh)
    return GameAction.ACTION6, {"x": cx, "y": cy}


def smoke_one(
    stem: str,
    *,
    version: str,
    steps: int,
    seed: int,
    arcade: Arcade,
) -> tuple[str, str | None]:
    """Returns (label, error or None)."""
    label = f"{stem}/{version}"
    try:
        full = _load_full_game_id(stem, version)
        env = arcade.make(full, seed=seed, render_mode=None)
        if env is None:
            return label, "arc.make returned None"
        env.reset()
        rng = random.Random(seed + sum(ord(c) for c in stem) * 31)
        for i in range(steps):
            level = env._game.current_level
            act, data = _pick_action(
                rng,
                level,
                move_weight=7,
                a5_weight=2,
                a6_weight=2,
            )
            res = env.step(act, reasoning={"smoke_registry": i + 1, "game": full}, data=data)
            if res.state in (GameState.WIN, GameState.GAME_OVER):
                break
        return label, None
    except Exception as e:  # noqa: BLE001
        return label, f"{type(e).__name__}: {e}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--from",
        dest="from_id",
        metavar="STEM",
        help="First game id in GAMES.md table order (inclusive)",
    )
    parser.add_argument(
        "--through",
        dest="through_id",
        metavar="STEM",
        help="Last game id in GAMES.md table order (inclusive)",
    )
    parser.add_argument(
        "--version",
        default="auto",
        help="Version dir under environment_files/{stem}/, or 'auto' for sole dir (default: auto)",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=80,
        help="Random steps per game (default: 80)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="RNG base seed (default: 0)",
    )
    parser.add_argument(
        "--require-games-md-row",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Require each stem to appear in GAMES.md (default: true)",
    )
    args = parser.parse_args()

    md_text = GAMES_MD.read_text(encoding="utf-8")
    table_ids = [g for g, _ in parse_games_table(md_text)]
    stems = _slice_ids(table_ids, args.from_id, args.through_id)

    games_body = md_text if args.require_games_md_row else ""

    arc = Arcade(
        environments_dir=str(ENV_DIR),
        operation_mode=OperationMode.OFFLINE,
    )

    failed = False
    for stem in stems:
        if args.require_games_md_row and games_body:
            if not re.search(rf"^\| {re.escape(stem)} \|", games_body, re.MULTILINE):
                print(f"FAIL {stem}: no GAMES.md row", file=sys.stderr)
                failed = True
                continue
        label, err = smoke_one(
            stem,
            version=args.version,
            steps=args.steps,
            seed=args.seed,
            arcade=arc,
        )
        if err:
            failed = True
            print(f"FAIL {label}: {err}", file=sys.stderr)
        else:
            print(f"OK  {label}")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
