#!/usr/bin/env python3
"""Rewrite README <!-- readme-stats:begin/end --> with shields badges (game count + contribute)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"
GAMES_MD = ROOT / "GAMES.md"

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


def build_block(registry: int) -> str:
    games_badge = (
        f"https://img.shields.io/badge/{registry}-INTERACTIVE_GAME-58A6FF?style=for-the-badge"
    )
    contribute_badge = (
        "https://img.shields.io/badge/Contributing-Add_an_interactive_game-238636?style=for-the-badge"
    )
    return "\n".join(
        [
            BEGIN,
            "",
            '<p align="center">',
            f'  <a href="GAMES.md"><img src="{games_badge}" alt="{registry} interactive games in registry" /></a>',
            "  &nbsp;",
            f'  <a href="CONTRIBUTING.md#creating-a-new-game"><img src="{contribute_badge}" alt="Contributing: add an interactive game" /></a>',
            "</p>",
            "",
            END,
        ]
    )


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
    block = build_block(count_games_registry_rows())
    new_text = pattern.sub(block, text, count=1)
    README.write_text(new_text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
