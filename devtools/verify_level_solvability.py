#!/usr/bin/env python3
"""Strict per-level solvability report using real ``Arcade`` transitions.

Writes JSON (and optional Markdown) under ``devtools/reports/``.

Examples::

    uv run python devtools/verify_level_solvability.py --stem co01
    uv run python devtools/verify_level_solvability.py --all --md
"""

from __future__ import annotations

import argparse
import json
import logging
import multiprocessing
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEVTOOLS = Path(__file__).resolve().parent
SCRIPTS = ROOT / "scripts"
REPORTS_DIR = DEVTOOLS / "reports"

for p in (str(ROOT), str(SCRIPTS), str(DEVTOOLS)):
    if p not in sys.path:
        sys.path.insert(0, p)

from arc_agi import Arcade, OperationMode  # noqa: E402
from solvability_common import (  # noqa: E402
    canonical_version_for_stem,
    full_game_id_canonical,
    level_count_from_stem_module,
    list_environment_stems,
    parse_games_md_stems,
)
from solvers.engine_bfs import engine_bfs_single_level  # noqa: E402
from solvers.extra_state import extra_state_key_for_stem  # noqa: E402
from solvers.partial_obs import partial_obs_verdict  # noqa: E402
from solvers.push_switch import verify_push_stem, verify_switch_stem  # noqa: E402
from solvers.registry import (  # noqa: E402
    LATTICE_TOGGLE_NOTE,
    LATTICE_TOGGLE_TOOLING_STEMS,
    PLANNER_NOTE,
    SIMULATION_NOTE,
    STOCHASTIC_NOTE,
    SolverKind,
    engine_bfs_limits,
    solver_kind_for_stem,
)
from solvers.survival_wave3 import WAVE3_REFLEX_NOTE  # noqa: E402
from solvers.types import LevelVerdict, VerdictStatus  # noqa: E402


def _verify_one_level(
    arc: Arcade,
    stem: str,
    version: str,
    full_game_id: str,
    level_index: int,
    num_levels: int,
    *,
    quick: bool = False,
    full_bfs: bool = False,
) -> LevelVerdict:
    t0 = time.perf_counter()
    kind = solver_kind_for_stem(stem)

    if kind == SolverKind.PARTIAL_OBS:
        return partial_obs_verdict(stem, level_index)

    if kind == SolverKind.TOOLING_GAP:
        if stem in LATTICE_TOGGLE_TOOLING_STEMS:
            return LevelVerdict(
                stem=stem,
                level_index=level_index,
                status=VerdictStatus.TOOLING_GAP,
                solver="lattice_toggle_skip",
                notes=LATTICE_TOGGLE_NOTE,
            )
        return LevelVerdict(
            stem=stem,
            level_index=level_index,
            status=VerdictStatus.TOOLING_GAP,
            solver="wave3_reflex",
            notes=WAVE3_REFLEX_NOTE,
        )

    env = arc.make(full_game_id, seed=0, render_mode=None)
    if env is None:
        return LevelVerdict(
            stem=stem,
            level_index=level_index,
            status=VerdictStatus.ERROR,
            solver="load",
            notes="arc.make returned None",
        )

    if kind == SolverKind.STOCHASTIC_GAP:
        return LevelVerdict(
            stem=stem,
            level_index=level_index,
            status=VerdictStatus.TOOLING_GAP,
            solver="stochastic",
            notes=STOCHASTIC_NOTE,
        )

    if kind == SolverKind.PLANNER_GAP:
        return LevelVerdict(
            stem=stem,
            level_index=level_index,
            status=VerdictStatus.TOOLING_GAP,
            solver="planner_skip",
            notes=PLANNER_NOTE,
        )

    if kind == SolverKind.SIMULATION_GAP:
        return LevelVerdict(
            stem=stem,
            level_index=level_index,
            status=VerdictStatus.TOOLING_GAP,
            solver="simulation_skip",
            notes=SIMULATION_NOTE,
        )

    if kind == SolverKind.PUSH:
        ok, msg = verify_push_stem(env, stem, version, level_index, variant="default")
        dt = time.perf_counter() - t0
        return LevelVerdict(
            stem=stem,
            level_index=level_index,
            status=VerdictStatus.PROVED if ok else VerdictStatus.COUNTEREXAMPLE,
            solver="push_puzzle_plan",
            notes=msg,
            extra={"seconds": dt},
        )

    if kind == SolverKind.PB03:
        ok, msg = verify_push_stem(env, stem, version, level_index, variant="pb03")
        dt = time.perf_counter() - t0
        return LevelVerdict(
            stem=stem,
            level_index=level_index,
            status=VerdictStatus.PROVED if ok else VerdictStatus.COUNTEREXAMPLE,
            solver="pb03_safe_plan",
            notes=msg,
            extra={"seconds": dt},
        )

    if kind == SolverKind.SWITCH_ALL:
        ok, msg = verify_switch_stem(env, stem, version, level_index, mode="all")
        dt = time.perf_counter() - t0
        return LevelVerdict(
            stem=stem,
            level_index=level_index,
            status=VerdictStatus.PROVED if ok else VerdictStatus.COUNTEREXAMPLE,
            solver="switch_door_all",
            notes=msg,
            extra={"seconds": dt},
        )

    if kind == SolverKind.SWITCH_OR:
        ok, msg = verify_switch_stem(env, stem, version, level_index, mode="or")
        dt = time.perf_counter() - t0
        return LevelVerdict(
            stem=stem,
            level_index=level_index,
            status=VerdictStatus.PROVED if ok else VerdictStatus.COUNTEREXAMPLE,
            solver="switch_door_or",
            notes=msg,
            extra={"seconds": dt},
        )

    if kind == SolverKind.SWITCH_K:
        ok, msg = verify_switch_stem(env, stem, version, level_index, mode="k_of_n")
        dt = time.perf_counter() - t0
        return LevelVerdict(
            stem=stem,
            level_index=level_index,
            status=VerdictStatus.PROVED if ok else VerdictStatus.COUNTEREXAMPLE,
            solver="switch_door_k_of_n",
            notes=msg,
            extra={"seconds": dt},
        )

    # ENGINE_BFS variants
    env = arc.make(full_game_id, seed=0, render_mode=None)
    if env is None:
        return LevelVerdict(
            stem=stem,
            level_index=level_index,
            status=VerdictStatus.ERROR,
            solver="engine_bfs",
            notes="arc.make returned None",
        )
    env.reset()
    env._game.set_level(level_index)
    avail = set(env.observation_space.available_actions)
    if 7 in avail:
        return LevelVerdict(
            stem=stem,
            level_index=level_index,
            status=VerdictStatus.TOOLING_GAP,
            solver="engine_bfs",
            notes="ACTION7 present: undo/extra semantics not modeled in BFS",
        )

    gw, gh = env._game.current_level.grid_size
    cells = max(0, gw) * max(0, gh)
    if (
        kind == SolverKind.ENGINE_BFS
        and 6 in avail
        and cells > 12 * 12
    ):
        return LevelVerdict(
            stem=stem,
            level_index=level_index,
            status=VerdictStatus.TOOLING_GAP,
            solver="engine_bfs",
            notes=(
                f"large grid ({gw}×{gh}) with ACTION6: branch factor too high for "
                "generic engine BFS; use ENGINE_BFS_ACTION6_ONLY stem mapping or a "
                "dedicated solver."
            ),
        )

    max_nodes, max_depth, max_click = engine_bfs_limits(
        stem, quick=quick, full=full_bfs
    )
    allowed = {6} if kind == SolverKind.ENGINE_BFS_ACTION6_ONLY else None

    bfs = engine_bfs_single_level(
        env,
        level_index=level_index,
        max_nodes=max_nodes,
        max_depth=max_depth,
        max_click_cells=max_click,
        allowed_action_ids=allowed,
        extra_state_key=extra_state_key_for_stem(stem),
    )
    dt = time.perf_counter() - t0
    if bfs.ok:
        return LevelVerdict(
            stem=stem,
            level_index=level_index,
            status=VerdictStatus.PROVED,
            solver="engine_bfs",
            notes=bfs.reason,
            nodes_expanded=bfs.nodes,
            depth=bfs.depth,
            extra={"seconds": dt},
        )
    if "exceeds" in (bfs.reason or "") or "max_nodes" in (bfs.reason or ""):
        return LevelVerdict(
            stem=stem,
            level_index=level_index,
            status=VerdictStatus.TOOLING_GAP,
            solver="engine_bfs",
            notes=bfs.reason,
            nodes_expanded=bfs.nodes,
            extra={"seconds": dt, "hint": "increase limits or add stem-specific solver"},
        )
    return LevelVerdict(
        stem=stem,
        level_index=level_index,
        status=VerdictStatus.COUNTEREXAMPLE,
        solver="engine_bfs",
        notes=bfs.reason,
        nodes_expanded=bfs.nodes,
        extra={"seconds": dt},
    )


def _verdict_to_dict(v: LevelVerdict) -> dict:
    d = {
        "stem": v.stem,
        "level_index": v.level_index,
        "status": v.status.value,
        "solver": v.solver,
        "notes": v.notes,
        "nodes_expanded": v.nodes_expanded,
        "depth": v.depth,
    }
    if v.extra:
        d["extra"] = v.extra
    return d


def _verify_stem_job(stem: str, quick: bool, full_bfs: bool) -> list[LevelVerdict]:
    """Process-pool entry: one Arcade instance per stem."""
    arc = Arcade(
        environments_dir=str(ROOT / "environment_files"),
        operation_mode=OperationMode.OFFLINE,
    )
    out: list[LevelVerdict] = []
    try:
        version = canonical_version_for_stem(stem)
        gid = full_game_id_canonical(stem)
        n = level_count_from_stem_module(stem, version)
        if n is None:
            return [
                LevelVerdict(
                    stem=stem,
                    level_index=-1,
                    status=VerdictStatus.ERROR,
                    solver="inventory",
                    notes="could not read levels from module",
                )
            ]
        for li in range(n):
            out.append(
                _verify_one_level(
                    arc,
                    stem,
                    version,
                    gid,
                    li,
                    n,
                    quick=quick,
                    full_bfs=full_bfs,
                )
            )
    except Exception as e:
        out.append(
            LevelVerdict(
                stem=stem,
                level_index=-1,
                status=VerdictStatus.ERROR,
                solver="exception",
                notes=f"{type(e).__name__}: {e}",
            )
        )
    return out


def _write_markdown(path: Path, rows: list[LevelVerdict]) -> None:
    lines = [
        "# Level solvability report",
        "",
        "| stem | level | status | solver | notes |",
        "|------|-------|--------|--------|-------|",
    ]
    for v in rows:
        note = (v.notes or "").replace("|", "\\|").replace("\n", " ")[:200]
        lines.append(
            f"| {v.stem} | {v.level_index} | {v.status.value} | {v.solver} | {note} |"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    for _name in ("arc_agi", "arcengine"):
        logging.getLogger(_name).setLevel(logging.WARNING)

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stem", action="append", default=[], metavar="STEM")
    parser.add_argument(
        "--all",
        action="store_true",
        help="All stems in GAMES.md that exist under environment_files/",
    )
    parser.add_argument(
        "--out-json",
        type=Path,
        default=REPORTS_DIR / "level_solvability.json",
    )
    parser.add_argument("--md", action="store_true", help="Also write level_solvability.md")
    parser.add_argument(
        "--fail-on",
        choices=("counterexample", "counterexample_or_error", "any_non_proved"),
        default="counterexample_or_error",
        help="Exit non-zero if any row matches (default: counterexample_or_error)",
    )
    parser.add_argument(
        "--jobs",
        type=int,
        default=1,
        help="Parallel processes (one stem per worker; default: 1)",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Lower BFS node/depth caps (faster, more tooling_gap exhaust hits)",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Raise BFS node/depth caps (slower, fewer false exhaust/tooling hits)",
    )
    args = parser.parse_args()

    if args.all:
        games = set(parse_games_md_stems())
        envs = set(list_environment_stems())
        stems = sorted(games & envs, key=str.lower)
    elif args.stem:
        stems = sorted(set(args.stem), key=str.lower)
    else:
        parser.error("pass --all or one or more --stem")

    rows: list[LevelVerdict] = []
    if args.jobs <= 1:
        arc = Arcade(
            environments_dir=str(ROOT / "environment_files"),
            operation_mode=OperationMode.OFFLINE,
        )
        for stem in stems:
            try:
                version = canonical_version_for_stem(stem)
                gid = full_game_id_canonical(stem)
                n = level_count_from_stem_module(stem, version)
                if n is None:
                    rows.append(
                        LevelVerdict(
                            stem=stem,
                            level_index=-1,
                            status=VerdictStatus.ERROR,
                            solver="inventory",
                            notes="could not read levels from module",
                        )
                    )
                    print(f"[solvability] {stem} inventory_error", flush=True)
                    continue
                for li in range(n):
                    rows.append(
                        _verify_one_level(
                            arc,
                            stem,
                            version,
                            gid,
                            li,
                            n,
                            quick=args.quick,
                            full_bfs=args.full,
                        )
                    )
                print(f"[solvability] {stem} ok ({n} levels)", flush=True)
            except Exception as e:
                rows.append(
                    LevelVerdict(
                        stem=stem,
                        level_index=-1,
                        status=VerdictStatus.ERROR,
                        solver="exception",
                        notes=f"{type(e).__name__}: {e}",
                    )
                )
    else:
        ctx = multiprocessing.get_context("spawn")
        with ProcessPoolExecutor(max_workers=args.jobs, mp_context=ctx) as ex:
            futs = {
                ex.submit(_verify_stem_job, stem, args.quick, args.full): stem
                for stem in stems
            }
            stem_results: dict[str, list[LevelVerdict]] = {}
            for fut in as_completed(futs):
                stem = futs[fut]
                try:
                    stem_results[stem] = fut.result()
                except Exception as e:
                    stem_results[stem] = [
                        LevelVerdict(
                            stem=stem,
                            level_index=-1,
                            status=VerdictStatus.ERROR,
                            solver="worker",
                            notes=f"{type(e).__name__}: {e}",
                        )
                    ]
        for stem in stems:
            rows.extend(stem_results.get(stem, []))

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "stems": stems,
        "rows": [_verdict_to_dict(v) for v in rows],
        "summary": {
            s.value: sum(1 for v in rows if v.status == s)
            for s in VerdictStatus
        },
    }
    args.out_json.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"wrote {args.out_json}")
    if args.md:
        md_path = args.out_json.with_suffix(".md")
        _write_markdown(md_path, rows)
        print(f"wrote {md_path}")

    bad = False
    for v in rows:
        if args.fail_on == "counterexample" and v.status == VerdictStatus.COUNTEREXAMPLE:
            bad = True
        elif args.fail_on == "counterexample_or_error" and v.status in (
            VerdictStatus.COUNTEREXAMPLE,
            VerdictStatus.ERROR,
        ):
            bad = True
        elif args.fail_on == "any_non_proved" and v.status != VerdictStatus.PROVED:
            bad = True
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
