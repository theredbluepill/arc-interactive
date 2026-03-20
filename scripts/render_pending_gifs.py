#!/usr/bin/env python3
"""
Generate assets/{id}.gif for every GAMES.md row with an empty Preview cell.

Phase 1: greedy BFS toward goal-like cells (recomputed each step for dynamic doors).
Phase 2: if too few frames, reset and run a short mixed ACTION1–6 showcase (clicks use
letterboxed cell-centers). Not a full solve for every game, but produces readable motion.

See also: ``render_registry_gifs.py`` + ``registry_gif_lib.py`` for multi-level captures.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from arcengine import GameState
from gif_common import (
    append_frame_repeats,
    offline_arcade,
    repo_root,
    save_gif,
)

# Import table parser (same repo, scripts/ on sys.path when run as file)
from env_resolve import full_game_id_for_stem
from gif_inventory import parse_games_table
from registry_gif_lib import (
    bfs_next_action,
    goal_positions_set,
    run_showcase_fallback,
)


def _empty_preview_game_ids(root: Path) -> list[str]:
    text = (root / "GAMES.md").read_text(encoding="utf-8")
    out: list[str] = []
    for gid, preview in parse_games_table(text):
        if "![" not in preview:
            out.append(gid)
    return out


def _linked_but_missing_asset_ids(root: Path) -> list[str]:
    text = (root / "GAMES.md").read_text(encoding="utf-8")
    assets = root / "assets"
    out: list[str] = []
    for gid, preview in parse_games_table(text):
        if "![" not in preview:
            continue
        if not (assets / f"{gid}.gif").is_file():
            out.append(gid)
    return out


def fill_empty_previews_in_games_md(root: Path) -> None:
    """Set Preview to ``![id](assets/id.gif)`` for rows whose preview cell is empty."""
    md_path = root / "GAMES.md"
    lines_out: list[str] = []
    for line in md_path.read_text(encoding="utf-8").splitlines():
        if not line.strip().startswith("|") or line.strip().startswith("|-"):
            lines_out.append(line)
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 9 or parts[1] == "Game":
            lines_out.append(line)
            continue
        gid = parts[1]
        if not re.match(r"^[a-z]{2}\d{2}$", gid):
            lines_out.append(line)
            continue
        preview = parts[6] if len(parts) > 6 else ""
        if "![" in preview:
            lines_out.append(line)
            continue
        parts[6] = f"![{gid}](assets/{gid}.gif)"
        lines_out.append("| " + " | ".join(parts[1:-1]) + " |")
    md_path.write_text("\n".join(lines_out) + "\n", encoding="utf-8")


def _frame_layer0(res) -> list:
    return getattr(res, "frame", None) or []


def record_one(game_id: str, root: Path, *, verbose: bool = False) -> Path:
    out = root / "assets" / f"{game_id}.gif"
    arc = offline_arcade(root)
    env = arc.make(full_game_id_for_stem(game_id), seed=0, render_mode=None)
    res = env.reset()
    images: list = []

    def last_raster():
        fr = _frame_layer0(res)
        if not fr:
            raise RuntimeError(f"{game_id}: no frame after reset")
        return fr[0]

    raster = last_raster()

    def snap_repeats(times: int) -> None:
        nonlocal raster
        fr = _frame_layer0(res)
        if fr:
            raster = fr[0]
        append_frame_repeats(images, raster, times)

    snap_repeats(6)

    for _ in range(200):
        if res.state in (GameState.WIN, GameState.GAME_OVER):
            break
        if (getattr(res, "levels_completed", None) or 0) >= 1:
            break
        level = env._game.current_level
        goals = goal_positions_set(level)
        players = level.get_sprites_by_tag("player")
        if not players:
            break
        start = (players[0].x, players[0].y)
        act = bfs_next_action(level, start, goals) if goals else None
        if act is None:
            break
        res = env.step(act, reasoning={})
        snap_repeats(2)

    min_frames = 28
    if len(images) < min_frames:
        if verbose:
            print(f"  {game_id}: showcase fallback ({len(images)} frames)")
        res = run_showcase_fallback(env, res, images, snap_repeats)
        snap_repeats(12)

    save_gif(out, images, duration_ms=150)
    if verbose:
        print(f"  wrote {out} ({len(images)} frames)")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--all",
        action="store_true",
        help="Render every game with an empty Preview cell in GAMES.md",
    )
    parser.add_argument(
        "--backfill-linked",
        action="store_true",
        help="Also render rows that already link a GIF but assets/{id}.gif is missing",
    )
    parser.add_argument(
        "--fill-games-md",
        action="store_true",
        help="After rendering, set empty Preview cells to ![id](assets/id.gif)",
    )
    parser.add_argument("--game", type=str, help="Single game id (e.g. ju01)")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    root = repo_root()
    if args.game:
        ids = [args.game.strip().lower()]
    elif args.all or args.backfill_linked:
        id_set: set[str] = set()
        if args.all:
            id_set.update(_empty_preview_game_ids(root))
        if args.backfill_linked:
            id_set.update(_linked_but_missing_asset_ids(root))
        ids = sorted(id_set)
        if not ids:
            parser.error("no game ids selected")
    else:
        parser.error("pass --all and/or --backfill-linked, or --game ID")
    failed: list[tuple[str, str]] = []
    for gid in ids:
        try:
            record_one(gid, root, verbose=args.verbose)
            if not args.verbose:
                print(gid, "ok")
        except Exception as e:  # noqa: BLE001
            failed.append((gid, f"{type(e).__name__}: {e}"))
            print(gid, "FAIL", e, file=sys.stderr)
    if failed:
        sys.exit(1)
    if args.fill_games_md:
        fill_empty_previews_in_games_md(root)
        if args.verbose:
            print("Updated GAMES.md preview column for previously empty cells")


if __name__ == "__main__":
    main()
