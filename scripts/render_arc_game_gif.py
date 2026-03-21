#!/usr/bin/env python3
"""Single entry point for ARC preview GIFs under ``assets/``.

**Registry mode (default)** — multi-level capture, wall-bump “fails”, stem overrides:
  uv run python scripts/render_arc_game_gif.py --stem wl01
  uv run python scripts/render_arc_game_gif.py --from pb01 --through bn03
  uv run python scripts/render_arc_game_gif.py --game ez01 -v

Uses ``registry_gif_lib.record_registry_gif`` and ``registry_gif_overrides.json``.
Games should expose a **GIF-ready** ``RenderableUserDisplay`` (see skill
``.opencode/skills/generate-arc-game-gif/SKILL.md``).

**Pending mode** — quick GIF for empty/missing ``GAMES.md`` preview links:
  uv run python scripts/render_arc_game_gif.py --pending --all
  uv run python scripts/render_arc_game_gif.py --pending --game ju01 --fill-games-md
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from arcengine import GameState

from env_resolve import full_game_id_for_stem
from gif_common import append_frame_repeats, offline_arcade, repo_root, save_gif
from gif_inventory import parse_games_table
from registry_gif_lib import (
    bfs_next_action,
    goal_positions_set,
    load_overrides,
    record_registry_gif,
    run_showcase_fallback,
)


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


def _frame_layer0(res: object) -> list:
    return getattr(res, "frame", None) or []


def record_pending_gif(game_id: str, root: Path, *, verbose: bool = False) -> Path:
    """Short BFS + optional ACTION1–6 showcase; writes ``assets/{game_id}.gif``."""
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


def _run_registry(args: argparse.Namespace, root: Path) -> int:
    md_text = (root / "GAMES.md").read_text(encoding="utf-8")
    table_ids = [g for g, _ in parse_games_table(md_text)]

    if args.stem:
        gid = args.stem.strip().lower()
        if not re.match(r"^[a-z]{2}\d{2}$", gid):
            raise SystemExit("invalid --stem / --game (expected aa00)")
        stems = [gid]
    else:
        stems = _slice_ids(table_ids, args.from_id, args.through_id)

    overrides_all = load_overrides(root)
    failed: list[tuple[str, str]] = []

    for stem in stems:
        try:
            ovr = overrides_all.get(stem)
            ovr_dict = ovr if isinstance(ovr, dict) else None
            duration_ms = 150
            if ovr_dict and "gif_duration_ms" in ovr_dict:
                duration_ms = int(ovr_dict["gif_duration_ms"])
            _, images = record_registry_gif(
                stem,
                root,
                overrides=ovr_dict,
                verbose=args.verbose,
                seed=args.seed,
            )
            outp = root / "assets" / f"{stem}.gif"
            save_gif(outp, images, duration_ms=duration_ms)
            if args.verbose:
                print(f"  wrote {outp} ({len(images)} frames)")
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


def _run_pending(args: argparse.Namespace, root: Path) -> int:
    if args.pending_game:
        ids = [args.pending_game.strip().lower()]
    elif args.pending_all or args.pending_backfill:
        id_set: set[str] = set()
        if args.pending_all:
            id_set.update(_empty_preview_game_ids(root))
        if args.pending_backfill:
            id_set.update(_linked_but_missing_asset_ids(root))
        ids = sorted(id_set)
        if not ids:
            raise SystemExit("no game ids selected for pending mode")
    else:
        raise SystemExit("pending mode: pass --pending-all and/or --pending-backfill, or --pending-game ID")

    failed: list[tuple[str, str]] = []
    for gid in ids:
        try:
            record_pending_gif(gid, root, verbose=args.verbose)
            if not args.verbose:
                print(gid, "ok")
        except Exception as e:  # noqa: BLE001
            failed.append((gid, f"{type(e).__name__}: {e}"))
            print(gid, "FAIL", e, file=sys.stderr)

    if failed:
        return 1
    if args.fill_games_md:
        fill_empty_previews_in_games_md(root)
        if args.verbose:
            print("Updated GAMES.md preview column for previously empty cells")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pending",
        action="store_true",
        help="Pending/backfill mode (short GIF for empty or missing assets)",
    )
    parser.add_argument(
        "--pending-all",
        action="store_true",
        help="With --pending: every GAMES.md row with empty Preview cell",
    )
    parser.add_argument(
        "--pending-backfill",
        action="store_true",
        help="With --pending: rows that link a GIF but assets/{id}.gif is missing",
    )
    parser.add_argument("--pending-game", type=str, metavar="STEM", help="With --pending: single stem")
    parser.add_argument(
        "--fill-games-md",
        action="store_true",
        help="With --pending: set empty Preview cells to ![id](assets/id.gif)",
    )

    parser.add_argument(
        "--stem",
        "--game",
        dest="stem",
        metavar="STEM",
        help="Registry mode: single stem (e.g. wl01)",
    )
    parser.add_argument(
        "--from",
        dest="from_id",
        metavar="STEM",
        help="Registry mode: first stem in GAMES.md order (inclusive)",
    )
    parser.add_argument(
        "--through",
        dest="through_id",
        metavar="STEM",
        help="Registry mode: last stem in GAMES.md order (inclusive)",
    )
    parser.add_argument("--seed", type=int, default=0, help="Registry exploration RNG seed (default 0)")
    parser.add_argument("-v", "--verbose", action="store_true")

    args = parser.parse_args()
    root = repo_root()

    if args.pending:
        return _run_pending(args, root)

    if args.pending_all or args.pending_backfill or args.pending_game or args.fill_games_md:
        raise SystemExit("use --pending with --pending-all / --pending-backfill / --pending-game")

    return _run_registry(args, root)


if __name__ == "__main__":
    sys.exit(main())
