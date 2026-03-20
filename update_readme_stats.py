#!/usr/bin/env python3
"""Rewrite the README block between <!-- readme-stats:begin/end --> markers."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
README = ROOT / "README.md"
GAMES_MD = ROOT / "GAMES.md"
ENV_DIR = ROOT / "environment_files"

BEGIN = "<!-- readme-stats:begin -->"
END = "<!-- readme-stats:end -->"


def count_games_registry_rows() -> int:
    """Count data rows in the GAMES.md pipe table (after the --- separator)."""
    text = GAMES_MD.read_text(encoding="utf-8")
    lines = text.splitlines()
    past_sep = False
    n = 0
    for line in lines:
        stripped = line.strip()
        if not past_sep:
            if stripped.startswith("|") and "---" in stripped:
                past_sep = True
            continue
        if not stripped.startswith("|"):
            break
        cells = [c.strip() for c in line.split("|")]
        if len(cells) < 3:
            continue
        first = cells[1]
        if not first or first.lower() == "game":
            continue
        n += 1
    return n


def count_environment_packages() -> int:
    """Count game_id/version dirs that contain metadata.json."""
    if not ENV_DIR.is_dir():
        return 0
    n = 0
    for game_dir in sorted(ENV_DIR.iterdir()):
        if not game_dir.is_dir():
            continue
        for ver_dir in sorted(game_dir.iterdir()):
            if ver_dir.is_dir() and (ver_dir / "metadata.json").is_file():
                n += 1
    return n


def build_block(registry: int, packages: int) -> str:
    lines = [
        BEGIN,
        "",
        f"- **Games listed in [GAMES.md](GAMES.md):** {registry}",
        f"- **Runnable packages in `environment_files/`:** {packages} (`game_id` + version folder with `metadata.json`)",
    ]
    if registry != packages:
        lines.append(
            "- *Counts differ — sync the registry table with on-disk packages when you add or remove games.*"
        )
    lines.extend(["", END])
    return "\n".join(lines)


def main() -> int:
    if not README.is_file():
        print("README.md not found", file=sys.stderr)
        return 1
    text = README.read_text(encoding="utf-8")
    pattern = re.compile(
        re.escape(BEGIN) + r".*?" + re.escape(END),
        re.DOTALL,
    )
    if not pattern.search(text):
        print(f"Missing {BEGIN} … {END} in README.md", file=sys.stderr)
        return 1
    block = build_block(count_games_registry_rows(), count_environment_packages())
    new_text = pattern.sub(block, text, count=1)
    README.write_text(new_text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
