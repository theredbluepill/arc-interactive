"""
Kaggle @kbench.task definitions for ARC-AGI-3 executive-style games.

Aligned with the Kaggle “Measuring Progress Toward AGI” cognitive-abilities track:
planning / sequencing (sk01), hazard avoidance + collection (tt01), resource
timing (sv01), plus ez01 as a minimal ACTION1–4 baseline (semantics are game-specific per ARC docs).
"""

from __future__ import annotations

import sys
from pathlib import Path

import kaggle_benchmarks as kbench

from arc_agi import Arcade, OperationMode

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_SCRIPTS = REPO_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
from env_resolve import full_game_id_for_stem  # noqa: E402

ENVIRONMENTS_DIR = str(REPO_ROOT / "environment_files")

_EZ01 = full_game_id_for_stem("ez01")
_SK01 = full_game_id_for_stem("sk01")
_TT01 = full_game_id_for_stem("tt01")
_SV01 = full_game_id_for_stem("sv01")

# Deterministic replays for MockLLM smoke tests (seed=0).
MOCK_SK01_L1_DIGITS = "224441422"
MOCK_TT01_L1_DIGITS = "22224114144"
# Greedy policy recording: completes sv01 level 1 (60 survival steps) on seed=0.
MOCK_SV01_L1_DIGITS = (
    "44555555555533445555551155555555114422555522245555552231555"
)

ARC_TASK_NAMES = (
    "arc_ez01_go_up",
    "arc_sk01_sokoban",
    "arc_tt01_collect",
    "arc_sv01_survive",
)


@kbench.task(name="arc_ez01_go_up")
def arc_ez01_go_up(llm, seed: int = 0, max_steps: int = 30):
    """Baseline: ez01 (Go Up). Reach the goal using this game's ACTION1–4 (IDs 1–4)."""
    from benchmarks.arc_game_wrapper import run_game_with_llm

    arc = Arcade(
        environments_dir=ENVIRONMENTS_DIR,
        operation_mode=OperationMode.OFFLINE,
    )
    levels_completed, _, _ = run_game_with_llm(
        arc=arc,
        game_id=_EZ01,
        llm=llm,
        seed=seed,
        max_steps=max_steps,
        grid_size=8,
    )
    kbench.assertions.assert_true(
        levels_completed >= 1,
        expectation="LLM should complete at least 1 level of ez01 (Go Up).",
    )


@kbench.task(name="arc_sk01_sokoban")
def arc_sk01_sokoban(llm, seed: int = 0, max_steps: int = 200):
    """Planning: sk01 Sokoban. Push blocks onto targets via ACTION1–4 (IDs 1–4)."""
    from benchmarks.arc_game_wrapper import run_game_with_llm

    arc = Arcade(
        environments_dir=ENVIRONMENTS_DIR,
        operation_mode=OperationMode.OFFLINE,
    )
    levels_completed, _, _ = run_game_with_llm(
        arc=arc,
        game_id=_SK01,
        llm=llm,
        seed=seed,
        max_steps=max_steps,
        grid_size=16,
    )
    kbench.assertions.assert_true(
        levels_completed >= 1,
        expectation="LLM should complete at least 1 level of sk01 (Sokoban).",
    )


@kbench.task(name="arc_tt01_collect")
def arc_tt01_collect(llm, seed: int = 0, max_steps: int = 200):
    """Executive control: tt01 — collect targets, avoid hazards via ACTION1–4 (IDs 1–4)."""
    from benchmarks.arc_game_wrapper import run_game_with_llm

    arc = Arcade(
        environments_dir=ENVIRONMENTS_DIR,
        operation_mode=OperationMode.OFFLINE,
    )
    levels_completed, _, _ = run_game_with_llm(
        arc=arc,
        game_id=_TT01,
        llm=llm,
        seed=seed,
        max_steps=max_steps,
        grid_size=24,
    )
    kbench.assertions.assert_true(
        levels_completed >= 1,
        expectation="LLM should complete at least 1 level of tt01 (collect targets).",
    )


@kbench.task(name="arc_sv01_survive")
def arc_sv01_survive(llm, seed: int = 0, max_steps: int = 80):
    """Timing / resource: sv01 — manage hunger and warmth (ACTION1–5; see game rules)."""
    from benchmarks.arc_game_wrapper import run_game_with_llm

    arc = Arcade(
        environments_dir=ENVIRONMENTS_DIR,
        operation_mode=OperationMode.OFFLINE,
    )
    levels_completed, _, _ = run_game_with_llm(
        arc=arc,
        game_id=_SV01,
        llm=llm,
        seed=seed,
        max_steps=max_steps,
        grid_size=24,
    )
    kbench.assertions.assert_true(
        levels_completed >= 1,
        expectation="LLM should survive at least 1 level of sv01 (60 steps per level).",
    )
