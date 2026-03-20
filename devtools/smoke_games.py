#!/usr/bin/env python3
"""Smoke-test games: load via Arcade + random ACTION1–5 steps (no render).

Used in CI for PRs that touch ``environment_files/``. Exits non-zero on
exceptions, missing metadata, or (optionally) a missing ``GAMES.md`` row.

Note: This does not prove solvability or correct win logic — only that the
environment runs. Human (or agent) review still covers design and edge cases.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import subprocess
import sys
from pathlib import Path

from arc_agi import Arcade, OperationMode
from arcengine import GameAction

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from env_resolve import sole_package_version  # noqa: E402

ENV_DIR = ROOT / "environment_files"
GAMES_MD = ROOT / "GAMES.md"

_ENV_PATH_RE = re.compile(
    r"^environment_files/(?P<gid>[a-z0-9]+)/(?P<ver>[^/]+)/",
    re.IGNORECASE,
)


def _pairs_from_git_diff(base: str, head: str) -> list[tuple[str, str]]:
    proc = subprocess.run(
        ["git", "diff", "--name-only", base, head],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    seen: set[tuple[str, str]] = set()
    out: list[tuple[str, str]] = []
    for line in proc.stdout.splitlines():
        m = _ENV_PATH_RE.match(line.strip())
        if not m:
            continue
        gid, ver = m.group("gid"), m.group("ver")
        key = (gid, ver)
        if key not in seen:
            seen.add(key)
            out.append(key)
    return sorted(out)


def _load_metadata(game_id: str, version: str) -> dict:
    path = ENV_DIR / game_id / version / "metadata.json"
    if not path.is_file():
        raise FileNotFoundError(f"Missing metadata: {path}")
    data = json.loads(path.read_text())
    for key in ("game_id", "title"):
        if key not in data:
            raise ValueError(f"{path}: missing required key {key!r}")
    return data


def _games_md_has_row(games_body: str, stem: str) -> bool:
    # Table rows look like: | ez01 | ...
    return bool(re.search(rf"^\| {re.escape(stem)} \|", games_body, re.MULTILINE))


def _smoke_arcade(full_game_id: str, steps: int, seed: int) -> None:
    arc = Arcade(
        environments_dir=str(ENV_DIR.relative_to(ROOT)),
        operation_mode=OperationMode.OFFLINE,
    )
    env = arc.make(full_game_id, seed=seed, render_mode=None)
    if env is None:
        raise RuntimeError(f"arc.make returned None for {full_game_id!r}")

    rng = random.Random(seed)
    pool = [
        GameAction.ACTION1,
        GameAction.ACTION2,
        GameAction.ACTION3,
        GameAction.ACTION4,
        GameAction.ACTION5,
    ]
    for i in range(steps):
        action = rng.choice(pool)
        env.step(action, reasoning={"smoke_test": i + 1, "game": full_game_id})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--git-range",
        nargs=2,
        metavar=("BASE", "HEAD"),
        help="Discover game:version dirs from git diff between two commits",
    )
    parser.add_argument(
        "--game",
        action="append",
        default=[],
        metavar="STEM",
        help="Game stem (directory name under environment_files/), e.g. ez01 (repeatable)",
    )
    parser.add_argument(
        "--version",
        default="auto",
        help="Version directory when using --game, or 'auto' for sole dir (default: auto)",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=50,
        help="Random steps per game (default: 50)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="RNG seed for action choice (default: 0)",
    )
    parser.add_argument(
        "--check-games-md",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Require a GAMES.md table row for each game stem (default: true)",
    )
    args = parser.parse_args()

    pairs: list[tuple[str, str]] = []
    if args.git_range:
        pairs = _pairs_from_git_diff(args.git_range[0], args.git_range[1])
    for stem in args.game:
        ver = args.version
        if ver == "auto":
            ver = sole_package_version(stem)
        pairs.append((stem, ver))

    if not pairs:
        print("smoke_games: no targets (no environment_files paths in diff, no --game). OK.")
        return 0

    games_body = GAMES_MD.read_text() if args.check_games_md and GAMES_MD.is_file() else ""

    failed = False
    for game_id, version in pairs:
        label = f"{game_id}/{version}"
        try:
            meta = _load_metadata(game_id, version)
            full = meta["game_id"]
            if args.check_games_md and games_body and not _games_md_has_row(
                games_body, game_id
            ):
                raise RuntimeError(
                    f"No GAMES.md table row starting with '| {game_id} |' "
                    f"(add a registry row per CONTRIBUTING.md)"
                )
            _smoke_arcade(full, args.steps, args.seed)
            print(f"OK  {label}  ({full})")
        except Exception as e:
            failed = True
            print(f"FAIL {label}: {e}", file=sys.stderr)

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
