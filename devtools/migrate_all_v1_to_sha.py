#!/usr/bin/env python3
"""Bulk-rename ``environment_files/<stem>/v1/`` → ``<stem>/<git-short-8>/`` (except skip set).

Uses the same copy + ``metadata.json`` patch + rmtree flow as
``bump_env_versions.bump_stem``. Default destination name is
``git rev-parse --short=8 HEAD`` at run time (it may differ from the commit that
lands this tree; CI will retag on the next PR that touches a game).

Stdlib + import of ``devtools/bump_env_versions.py`` (no package install).
"""

from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_bump():
    spec = importlib.util.spec_from_file_location(
        "bump_env_versions",
        ROOT / "devtools" / "bump_env_versions.py",
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _git_short8(ref: str = "HEAD") -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "--short=8", ref],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    out = proc.stdout.strip()
    if len(out) != 8 or any(c not in "0123456789abcdef" for c in out):
        raise SystemExit(f"unexpected short sha {out!r} from git rev-parse")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--sha",
        metavar="HEX8",
        help="8-char hex destination dir (default: git rev-parse --short=8 HEAD)",
    )
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    sha = args.sha or _git_short8("HEAD")
    bump = _load_bump()
    env = bump.ENV
    any_change = False

    for stem_path in sorted(env.iterdir(), key=lambda p: p.name.lower()):
        if not stem_path.is_dir():
            continue
        stem = stem_path.name
        if stem in bump.STEMS_SKIP_BUMP:
            continue
        v1 = stem_path / "v1"
        if not v1.is_dir() or not (v1 / "metadata.json").is_file():
            continue
        any_change = True
        if args.dry_run:
            print(f"{stem}: v1 -> {sha} (dry-run)")
            continue
        bump.bump_stem(stem, "v1", sha, dry_run=False)

    if not any_change:
        print("migrate_all_v1_to_sha: nothing to do (no v1 packages in scope)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
