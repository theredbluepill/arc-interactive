#!/usr/bin/env python3
"""Validate environment_files packages vs GAMES.md (stdlib only; fast in CI).

- Every ``environment_files/<stem>/<ver>/metadata.json`` must have required keys
  and consistent ``game_id`` / ``local_dir`` (unless stem is in the omission set).
- Stems not in the omission set must appear in the GAMES.md table.
- Every GAMES.md game id must have at least one version dir with ``metadata.json``.
- Duplicate game ids in GAMES.md fail the check.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_DIR = ROOT / "environment_files"
GAMES_MD = ROOT / "GAMES.md"

# Reference / legacy packages kept out of the public registry table.
STEMS_OMITTED_FROM_GAMES = frozenset({"vc33", "ls20", "ft09"})

REQUIRED_METADATA_KEYS = frozenset({"game_id", "title"})


def _parse_games_md_game_ids(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    ids: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")]
        if len(cells) < 3:
            continue
        gid = cells[1]
        if not gid or gid.lower() == "game":
            continue
        if set(gid) <= {"-", ":"}:
            continue
        ids.append(gid)
    return ids


def _discover_packages() -> list[tuple[str, str, Path]]:
    """(stem, version_dir_name, path_to_metadata)."""
    out: list[tuple[str, str, Path]] = []
    if not ENV_DIR.is_dir():
        return out
    for stem_path in sorted(ENV_DIR.iterdir(), key=lambda p: p.name.lower()):
        if not stem_path.is_dir():
            continue
        stem = stem_path.name
        for ver_path in sorted(stem_path.iterdir(), key=lambda p: p.name.lower()):
            if not ver_path.is_dir():
                continue
            meta = ver_path / "metadata.json"
            if meta.is_file():
                out.append((stem, ver_path.name, meta))
    return out


def _validate_metadata(stem: str, ver: str, meta_path: Path) -> list[str]:
    errs: list[str] = []
    try:
        data = json.loads(meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"{meta_path}: invalid JSON ({e})"]
    if not isinstance(data, dict):
        return [f"{meta_path}: metadata root must be an object"]
    missing = REQUIRED_METADATA_KEYS - data.keys()
    if missing:
        errs.append(f"{meta_path}: missing keys {sorted(missing)}")
    game_id = data.get("game_id")
    if isinstance(game_id, str):
        expected_id = f"{stem}-{ver}"
        if game_id != expected_id:
            errs.append(f"{meta_path}: game_id {game_id!r} expected {expected_id!r}")
    local_dir = data.get("local_dir")
    expected_local = f"environment_files/{stem}/{ver}".replace("\\", "/")
    if isinstance(local_dir, str):
        if local_dir.replace("\\", "/") != expected_local:
            errs.append(
                f"{meta_path}: local_dir {local_dir!r} expected {expected_local!r}"
            )
    elif "local_dir" in data:
        errs.append(f"{meta_path}: local_dir must be a string")
    return errs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    args = parser.parse_args()
    del args

    errors: list[str] = []

    if not GAMES_MD.is_file():
        errors.append(f"Missing {GAMES_MD}")
        print("\n".join(errors), file=sys.stderr)
        return 1

    game_ids_ordered = _parse_games_md_game_ids(GAMES_MD)
    counts = Counter(game_ids_ordered)
    dupes = [g for g, n in counts.items() if n > 1]
    if dupes:
        errors.append(f"GAMES.md: duplicate game id row(s): {', '.join(sorted(dupes))}")

    games_set = set(game_ids_ordered)

    for gid in sorted(games_set):
        gdir = ENV_DIR / gid
        if not gdir.is_dir():
            errors.append(f"GAMES.md lists {gid!r} but {gdir} is missing")
            continue
        has_meta = any(
            (v / "metadata.json").is_file()
            for v in gdir.iterdir()
            if v.is_dir()
        )
        if not has_meta:
            errors.append(f"GAMES.md lists {gid!r} but no */metadata.json under {gdir}")

    for stem, ver, meta_path in _discover_packages():
        errors.extend(_validate_metadata(stem, ver, meta_path))
        if stem in STEMS_OMITTED_FROM_GAMES:
            continue
        if stem not in games_set:
            errors.append(
                f"{meta_path}: stem {stem!r} has no GAMES.md table row "
                f"(add a row or extend STEMS_OMITTED_FROM_GAMES in check_registry.py)"
            )

    if errors:
        print("check_registry: FAILED", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print(
        f"check_registry: OK ({len(_discover_packages())} packages, "
        f"{len(games_set)} games in GAMES.md)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
