"""Shared helpers for solvability inventory and verification."""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = Path(__file__).resolve().parent / "reports"
SCRIPTS = ROOT / "scripts"
GAMES_MD = ROOT / "GAMES.md"
ENV_DIR = ROOT / "environment_files"

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from env_resolve import (  # noqa: E402
    environment_dir,
    full_game_id_for_stem,
    package_version_names,
)

_STEM_ROW_RE = re.compile(r"^\|\s*([a-z]{2}[0-9]{2})\s*\|", re.MULTILINE)


def _is_hex8(name: str) -> bool:
    return len(name) == 8 and all(c in "0123456789abcdef" for c in name.lower())


def canonical_version_for_stem(stem: str) -> str:
    """Match ``similar_games_report`` default: prefer 8-char hex, else v1, else last."""
    names = package_version_names(stem)
    if len(names) == 1:
        return names[0]
    hexes = [v for v in names if _is_hex8(v)]
    if hexes:
        return sorted(hexes, key=lambda s: s.lower())[-1]
    if "v1" in names:
        return "v1"
    return sorted(names, key=lambda s: s.lower())[-1]


def full_game_id_canonical(stem: str) -> str:
    return full_game_id_for_stem(stem, canonical_version_for_stem(stem))


def parse_games_md_stems(path: Path | None = None) -> list[str]:
    text = (path or GAMES_MD).read_text(encoding="utf-8")
    stems: list[str] = []
    for m in _STEM_ROW_RE.finditer(text):
        stems.append(m.group(1))
    return stems


def parse_games_md_stems_line_range(
    start_line: int, end_line: int, path: Path | None = None
) -> list[str]:
    """1-based inclusive line numbers in ``GAMES.md`` (table rows with ``| stem |``)."""
    lines = (path or GAMES_MD).read_text(encoding="utf-8").splitlines()
    chunk = "\n".join(lines[start_line - 1 : end_line])
    return [m.group(1) for m in _STEM_ROW_RE.finditer(chunk)]


def list_environment_stems() -> list[str]:
    base = environment_dir()
    if not base.is_dir():
        return []
    out: list[str] = []
    for p in sorted(base.iterdir(), key=lambda x: x.name.lower()):
        if not p.is_dir():
            continue
        if any(
            (p / d / "metadata.json").is_file()
            for d in p.iterdir()
            if d.is_dir()
        ):
            out.append(p.name)
    return out


def load_stem_game_module(stem: str, version: str, qualname: str):
    """Load ``{stem}.py`` from ``environment_files/<stem>/<version>/``."""
    path = environment_dir() / stem / version / f"{stem}.py"
    if not path.is_file():
        raise FileNotFoundError(path)
    spec = importlib.util.spec_from_file_location(qualname, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def level_count_from_stem_module(stem: str, version: str | None = None) -> int | None:
    """Return ``len(levels)`` from the stem's game module, or None if missing."""
    ver = version if version is not None else canonical_version_for_stem(stem)
    try:
        mod = load_stem_game_module(stem, ver, f"_solvability_inv_{stem}")
    except Exception:
        return None
    levels = getattr(mod, "levels", None)
    if levels is None:
        return None
    try:
        return len(levels)
    except TypeError:
        return None


def games_md_level_column(stem: str, path: Path | None = None) -> str | None:
    """Raw Levels cell text from GAMES.md for one stem, if present."""
    text = (path or GAMES_MD).read_text(encoding="utf-8")
    for raw in text.splitlines():
        line = raw.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")]
        if len(cells) < 5:
            continue
        if cells[1] == stem:
            return cells[4]
    return None
