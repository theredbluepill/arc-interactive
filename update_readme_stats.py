#!/usr/bin/env python3
"""Rewrite README stats block and static terminal-style SVG (VT323, no animation)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
README = ROOT / "README.md"
GAMES_MD = ROOT / "GAMES.md"
ASSETS = ROOT / "assets"
SVG_PATH = ASSETS / "readme-registry-count.svg"

BEGIN = "<!-- readme-stats:begin -->"
END = "<!-- readme-stats:end -->"

# Terminal-style banner: VT323 (OFL, closest Google-font match to chunky PC / BigBlue-style text).
BANNER_FILL = "#58A6FF"
PANEL_FILL = "#0d1117"


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


def _xml_escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def write_registry_svg(registry: int) -> None:
    """Write assets/readme-registry-count.svg (font loaded from assets/fonts/)."""
    ASSETS.mkdir(exist_ok=True)
    label = f"{registry} games in Game Registry"
    safe = _xml_escape(label)
    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="640" height="64" viewBox="0 0 640 64">
  <defs>
    <style type="text/css"><![CDATA[
      @font-face {{
        font-family: 'VT323';
        src: url('fonts/VT323-Regular.ttf') format('truetype');
        font-weight: normal;
        font-style: normal;
      }}
      .t {{
        font-family: 'VT323', ui-monospace, monospace;
        font-size: 44px;
        fill: {BANNER_FILL};
      }}
    ]]></style>
  </defs>
  <rect x="32" y="6" width="576" height="52" rx="6" fill="{PANEL_FILL}"/>
  <text x="320" y="44" text-anchor="middle" class="t">{safe}</text>
</svg>
"""
    SVG_PATH.write_text(svg, encoding="utf-8")


def build_block(registry: int) -> str:
    alt = f"{registry} games in Game Registry"
    return "\n".join(
        [
            BEGIN,
            "",
            "<!-- Static SVG: VT323 + terminal blue (assets/fonts/VT323-Regular.ttf, OFL). -->",
            '<p align="center">',
            f'  <img src="assets/readme-registry-count.svg" width="640" height="64" alt="{alt}" />',
            "</p>",
            "",
            END,
        ]
    )


def main() -> int:
    if not README.is_file():
        print("README.md not found", file=sys.stderr)
        return 1
    registry = count_games_registry_rows()
    write_registry_svg(registry)
    text = README.read_text(encoding="utf-8")
    pattern = re.compile(
        re.escape(BEGIN) + r".*?" + re.escape(END),
        re.DOTALL,
    )
    if not pattern.search(text):
        print(f"Missing {BEGIN} … {END} in README.md", file=sys.stderr)
        return 1
    block = build_block(registry)
    new_text = pattern.sub(block, text, count=1)
    README.write_text(new_text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
