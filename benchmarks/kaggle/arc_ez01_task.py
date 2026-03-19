"""
Kaggle benchmark task: ARC-AGI-3 ez01 (Go Up).

Play ez01 turn-by-turn. The LLM receives the game grid and must output
the next action (1-4). Success = complete at least 1 level.
"""

from __future__ import annotations

from pathlib import Path

import kaggle_benchmarks as kbench

from arc_agi import Arcade, OperationMode

# Resolve environment_files relative to repo root
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ENVIRONMENTS_DIR = str(REPO_ROOT / "environment_files")


@kbench.task(name="arc_ez01_go_up")
def arc_ez01_go_up(llm, seed: int = 0, max_steps: int = 30):
    """Play ARC-AGI-3 ez01 (Go Up): reach the target by moving up.

    Output action 1-4 each turn. 1=up, 2=down, 3=left, 4=right.
    Success = complete at least 1 level within the step limit.
    """
    from benchmarks.arc_game_wrapper import run_game_with_llm

    arc = Arcade(
        environments_dir=ENVIRONMENTS_DIR,
        operation_mode=OperationMode.OFFLINE,
    )
    levels_completed, steps_used, _ = run_game_with_llm(
        arc=arc,
        game_id="ez01-v1",
        llm=llm,
        seed=seed,
        max_steps=max_steps,
        grid_size=8,
    )
    kbench.assertions.assert_true(
        levels_completed >= 1,
        expectation="LLM should complete at least 1 level of ez01 (Go Up).",
    )


if __name__ == "__main__":
    arc_ez01_go_up.run(llm=kbench.llm, seed=0, max_steps=30)
