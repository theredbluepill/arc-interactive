"""Resolve environment package dirs under ``environment_files/<stem>/<ver>/``.

Hand-authored games may use a single version directory (``v1`` or an 8-char git
prefix). Tools should use ``full_game_id_for_stem`` / ``sole_package_version``
instead of hardcoding ``-v1``.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def environment_dir() -> Path:
    return repo_root() / "environment_files"


def package_version_names(stem: str) -> list[str]:
    stem_path = environment_dir() / stem
    if not stem_path.is_dir():
        raise FileNotFoundError(f"No environment package for stem {stem!r}: {stem_path}")
    names: list[str] = []
    for d in sorted(stem_path.iterdir(), key=lambda p: p.name.lower()):
        if d.is_dir() and (d / "metadata.json").is_file():
            names.append(d.name)
    return names


def sole_package_version(stem: str) -> str:
    names = package_version_names(stem)
    if len(names) == 1:
        return names[0]
    if len(names) == 0:
        raise FileNotFoundError(f"{stem}: no version directory with metadata.json")
    raise ValueError(
        f"{stem}: multiple version dirs {names}; pass an explicit --version or a full game_id"
    )


def package_dir(stem: str, version: str | None = None) -> Path:
    ver = version if version is not None else sole_package_version(stem)
    p = environment_dir() / stem / ver
    if not p.is_dir():
        raise FileNotFoundError(p)
    return p


def full_game_id_for_stem(stem: str, version: str | None = None) -> str:
    ver = version if version is not None else sole_package_version(stem)
    meta = environment_dir() / stem / ver / "metadata.json"
    data = json.loads(meta.read_text(encoding="utf-8"))
    gid = data.get("game_id")
    if not isinstance(gid, str):
        raise ValueError(f"{meta}: missing string game_id")
    return gid


def load_stem_game_py(stem: str, module_qualname: str) -> ModuleType:
    path = package_dir(stem) / f"{stem}.py"
    spec = importlib.util.spec_from_file_location(module_qualname, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
