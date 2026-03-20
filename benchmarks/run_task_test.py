#!/usr/bin/env python3
"""Run arc_ez01_go_up task with a mock LLM (no Kaggle proxy required)."""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS = _ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
from env_resolve import full_game_id_for_stem  # noqa: E402

from arc_agi import Arcade, OperationMode

from benchmarks.arc_game_wrapper import run_game_with_llm


class MockLLM:
    """Always returns action ID 1 (ACTION1). For ez01 this is sufficient to win."""

    def prompt(self, text: str) -> str:
        return "1"


def main() -> None:
    arc = Arcade(
        environments_dir="environment_files",
        operation_mode=OperationMode.OFFLINE,
    )
    levels, steps, _ = run_game_with_llm(
        arc=arc,
        game_id=full_game_id_for_stem("ez01"),
        llm=MockLLM(),
        seed=0,
        max_steps=30,
    )
    assert levels >= 1, "Task should complete at least 1 level"
    print(f"OK: {levels} level(s) completed in {steps} steps")


if __name__ == "__main__":
    main()
