"""Push-puzzle and floor-switch plans via ``scripts/registry_gif_lib`` (replay in real env)."""

from __future__ import annotations

import sys
from pathlib import Path

from arcengine import GameAction, GameState

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from registry_gif_lib import (  # noqa: E402
    _pb03_safe_plan,
    push_puzzle_plan,
    switch_door_plan,
)

from solvability_common import load_stem_game_module  # noqa: E402

_INT_TO_ACT: dict[int, GameAction] = {
    1: GameAction.ACTION1,
    2: GameAction.ACTION2,
    3: GameAction.ACTION3,
    4: GameAction.ACTION4,
}


def replay_int_plan(env, plan: list[int]) -> bool:
    from arcengine import GameState

    for a in plan:
        act = _INT_TO_ACT.get(a)
        if act is None:
            return False
        res = env.step(act, reasoning={})
        if res is None or res.state == GameState.GAME_OVER:
            return False
    return True


def verify_push_stem(
    env,
    stem: str,
    version: str,
    level_index: int,
    *,
    variant: str = "default",
) -> tuple[bool, str]:
    """Return (solved_next_level, message)."""
    mod = load_stem_game_module(stem, version, f"_solv_push_{stem}")
    levels = getattr(mod, "levels", None)
    if not levels or level_index >= len(levels):
        return False, "missing levels"
    level = levels[level_index]
    if variant == "pb03":
        plan = _pb03_safe_plan(level)
    else:
        plan = push_puzzle_plan(level)
    if plan is None:
        return False, "push_puzzle_plan returned None"
    g = env._game
    env.reset()
    g.set_level(level_index)
    start_li = level_index
    if not replay_int_plan(env, plan):
        return False, "replay hit GAME_OVER or bad action"
    if g.level_index > start_li or env.observation_space.state == GameState.WIN:
        return True, "ok"
    return False, "plan did not advance level"


def verify_switch_stem(
    env,
    stem: str,
    version: str,
    level_index: int,
    *,
    mode: str,
) -> tuple[bool, str]:
    mod = load_stem_game_module(stem, version, f"_solv_sw_{stem}")
    levels = getattr(mod, "levels", None)
    if not levels or level_index >= len(levels):
        return False, "missing levels"
    level = levels[level_index]
    plan = switch_door_plan(level, mode)
    if plan is None:
        return False, "switch_door_plan returned None"
    g = env._game
    env.reset()
    g.set_level(level_index)
    start_li = level_index
    if not replay_int_plan(env, plan):
        return False, "replay hit GAME_OVER or bad action"
    if g.level_index > start_li or env.observation_space.state == GameState.WIN:
        return True, "ok"
    return False, "plan did not advance level"
