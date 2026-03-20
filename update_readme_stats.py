#!/usr/bin/env python3
"""Rewrite the README block between <!-- readme-stats:begin/end --> markers."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import urlencode

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


def typing_svg_banner_url(registry: int, packages: int) -> str:
    """Animated typing banner (SVG as image; loops on GitHub README via img tag).

    Uses ``multiline=true`` so each sentence types on its own row and **stays**
    visible (no backspace-wipe between lines). readme-typing-svg only loads
    Google Fonts; **VT323** approximates a chunky PC terminal (BigBlue Terminal
    is not on Google Fonts).
    """
    text_lines = [
        f"{registry} games in GAMES.md",
        f"{packages} runnable packages in environment_files/",
    ]
    if registry != packages:
        text_lines.append("Counts differ — sync GAMES.md with disk")
    joined = ";".join(text_lines)
    size = 28
    line_gap = 5
    n = len(text_lines)
    height = n * (size + line_gap) + 28
    params = {
        "lines": joined,
        "font": "VT323",
        "size": str(size),
        "pause": "700",
        "duration": "2200",
        "color": "58A6FF",
        "center": "true",
        "vCenter": "true",
        "width": "600",
        "height": str(height),
        "multiline": "true",
        "repeat": "true",
    }
    return f"https://readme-typing-svg.demolab.com/?{urlencode(params)}"


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
    banner = typing_svg_banner_url(registry, packages)
    alt = (
        f"{registry} games in GAMES.md; {packages} runnable packages in environment_files/"
        + (
            "; registry and disk counts differ"
            if registry != packages
            else ""
        )
    )
    lines = [
        BEGIN,
        "",
        "<!-- Typing animation: readme-typing-svg.demolab.com (external); multiline stack (no wipe). -->",
        '<p align="center">',
        f'  <img src="{banner}" alt="{alt}" />',
        "</p>",
        "",
        END,
    ]
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
