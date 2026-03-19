#!/usr/bin/env python3
"""Run arc_ez01_go_up task with a mock LLM (no Kaggle proxy required)."""

from arc_agi import Arcade, OperationMode

from benchmarks.arc_game_wrapper import run_game_with_llm


class MockLLM:
    """Always returns action 1 (up) - sufficient to beat ez01."""

    def prompt(self, text: str) -> str:
        return "1"


def main() -> None:
    arc = Arcade(
        environments_dir="environment_files",
        operation_mode=OperationMode.OFFLINE,
    )
    levels, steps, _ = run_game_with_llm(
        arc=arc,
        game_id="ez01-v1",
        llm=MockLLM(),
        seed=0,
        max_steps=30,
    )
    assert levels >= 1, "Task should complete at least 1 level"
    print(f"OK: {levels} level(s) completed in {steps} steps")


if __name__ == "__main__":
    main()
