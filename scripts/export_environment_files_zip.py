#!/usr/bin/env python3
"""Build ``environment_files.zip`` containing the tree plus registry ``metadata.json``.

The JSON mirrors the human-edited **GAMES.md** games table: columns **Game**, **Category**,
**Grid**, **Levels**, **Description**, **Preview**, **Actions** (see that file for semantics).
The zip root includes ``metadata.json`` and a top-level ``environment_files/`` directory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from gif_inventory import GAMES_MD_COLUMNS, parse_games_table_full


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _games_md_footer_after_table(md: str) -> str | None:
    """Return non-table trailing prose after the last registry data row (e.g. GAMES.md footnote)."""
    lines = md.splitlines()
    last_data = -1
    for i, line in enumerate(lines):
        s = line.strip()
        if not s.startswith("|") or s.startswith("|-") or s.startswith("|--"):
            continue
        parts = [p.strip() for p in s.split("|")]
        if len(parts) < 9 or parts[1] == "Game":
            continue
        if re.match(r"^[a-z]{2}\d{2}$", parts[1]):
            last_data = i
    if last_data < 0:
        return None
    tail = "\n".join(lines[last_data + 1 :]).strip()
    return tail or None


def build_registry_metadata(games_md_path: Path) -> dict[str, object]:
    text = games_md_path.read_text(encoding="utf-8")
    games = parse_games_table_full(text)
    h = hashlib.sha256(text.encode("utf-8")).hexdigest()
    footer = _games_md_footer_after_table(text)
    meta: dict[str, object] = {
        "schema": "arc-interactive.environment_files_bundle",
        "schema_version": 1,
        "generated_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "registry_source": "GAMES.md",
        "registry_source_sha256": h,
        "registry_columns": list(GAMES_MD_COLUMNS),
        "games": games,
    }
    if footer is not None:
        meta["registry_trailing_note"] = footer
    return meta


def write_environment_files_zip(
    *,
    repo_root: Path,
    out_zip: Path,
    games_md: Path,
) -> None:
    env_dir = repo_root / "environment_files"
    if not env_dir.is_dir():
        raise FileNotFoundError(f"Missing environments directory: {env_dir}")
    bundle = build_registry_metadata(games_md)
    payload = json.dumps(bundle, ensure_ascii=False, indent=2) + "\n"
    payload_bytes = payload.encode("utf-8")

    out_zip.parent.mkdir(parents=True, exist_ok=True)
    skip_names = {"__pycache__", ".DS_Store"}

    def _skip(path: Path) -> bool:
        if path.name in skip_names:
            return True
        if "__pycache__" in path.parts:
            return True
        if path.suffix in {".pyc", ".pyo"}:
            return True
        return False

    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("metadata.json", payload_bytes)
        for path in sorted(env_dir.rglob("*")):
            if not path.is_file() or _skip(path):
                continue
            arc = Path("environment_files") / path.relative_to(env_dir)
            zf.write(path, arc.as_posix())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output zip path (default: <repo>/environment_files.zip)",
    )
    parser.add_argument(
        "--games-md",
        type=Path,
        default=None,
        help="Override path to GAMES.md (default: <repo>/GAMES.md)",
    )
    args = parser.parse_args()
    root = _repo_root()
    games_md = args.games_md if args.games_md is not None else root / "GAMES.md"
    if not games_md.is_file():
        print(f"GAMES.md not found: {games_md}", file=sys.stderr)
        sys.exit(1)
    out = args.output if args.output is not None else root / "environment_files.zip"
    write_environment_files_zip(repo_root=root, out_zip=out, games_md=games_md)
    print(f"Wrote {out} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
