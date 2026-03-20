"""
ARC-AGI-3 game wrapper for Kaggle benchmark tasks.

Provides utilities to run ARC games with an LLM agent: serialize game state
to text, parse LLM action responses, and run a full game loop.
"""

from __future__ import annotations

import re
from typing import Any

from arcengine import GameAction

# Map integer action IDs to GameAction
_ACTION_MAP: dict[int, GameAction] = {
    1: GameAction.ACTION1,
    2: GameAction.ACTION2,
    3: GameAction.ACTION3,
    4: GameAction.ACTION4,
    5: GameAction.ACTION5,
    6: GameAction.ACTION6,
    7: GameAction.ACTION7,
}


def default_action_help(available_actions: list[int]) -> str:
    """Human-readable action legend for LLM prompts.

    Per ARC-AGI-3, ACTION1–7 are abstract; 1–4 are often *described* as up/down/left/right
    in docs but each game defines what they do — see https://docs.arcprize.org/actions
    """
    avail = list(available_actions)
    if avail == [1, 2, 3, 4]:
        return (
            "Actions: use IDs 1–4 for this game's ACTION1–ACTION4. "
            "Their meaning is defined by the game (not necessarily up/down/left/right). "
            "Reply with a single digit (1-4)."
        )
    if avail == [1, 2, 3, 4, 5]:
        return (
            "Actions: use IDs 1–5 for this game's ACTION1–ACTION5. "
            "Semantics are game-specific (see description); 1–4 are not necessarily cardinal moves. "
            "Reply with a single digit (1-5)."
        )
    return (
        f"Available actions: {avail}. "
        "Reply with a single digit that is one of these action IDs."
    )


def serialize_frame_to_text(
    frame: list,
    grid_size: int = 8,
) -> str:
    """Convert frame grid to compact ASCII for LLM consumption.

    Args:
        frame: List of numpy arrays from FrameDataRaw.frame (typically 64x64).
        grid_size: Size of active game grid to extract (top-left region).

    Returns:
        Multi-line string with . for empty, digits for colored cells.
    """
    import numpy as np

    if not frame:
        return "(no frame)"
    arr = frame[0]
    if hasattr(arr, "tolist"):
        arr = np.asarray(arr)
    else:
        arr = np.array(arr)
    h, w = arr.shape
    # Crop to grid_size x grid_size from top-left
    crop_h = min(grid_size, h)
    crop_w = min(grid_size, w)
    region = arr[:crop_h, :crop_w]
    lines = []
    for row in region:
        chars = []
        for cell in row:
            val = int(cell)
            if val == 0:
                chars.append(".")
            elif val < 10:
                chars.append(str(val))
            else:
                chars.append(chr(ord("a") + val - 10))
        lines.append("".join(chars))
    return "\n".join(lines)


def parse_action_from_response(
    response: str,
    available_actions: list[int],
) -> GameAction | None:
    """Parse LLM response to extract next action.

    Looks for: single digit 1-8, ACTION1-ACTION8, or "action 1" style.

    Returns:
        GameAction if parseable and in available_actions, else None.
    """
    response = response.strip().upper()
    # Try "1" or "ACTION1" or "action 1"
    for pattern in [
        r"\bACTION([1-7])\b",
        r"\bACTION\s*([1-7])\b",
        r"\b([1-7])\b",
    ]:
        m = re.search(pattern, response, re.IGNORECASE)
        if m:
            num = int(m.group(1))
            if num in available_actions and num in _ACTION_MAP:
                return _ACTION_MAP[num]
    return None


def run_game_with_llm(
    arc: Any,
    game_id: str,
    llm: Any,
    seed: int = 0,
    max_steps: int = 50,
    grid_size: int = 8,
    action_help: str | None = None,
) -> tuple[int, int, Any]:
    """Run an ARC game with an LLM choosing actions each step.

    Args:
        arc: Arcade instance (from arc_agi.Arcade).
        game_id: Full game ID from package ``metadata.json`` (e.g. ``ez01-<8hex>``).
        llm: Kaggle benchmark LLM object with .prompt(text) -> str.
        seed: Random seed for environment.
        max_steps: Maximum steps before stopping.
        grid_size: Grid size for frame serialization (use max grid for multi-size games).
        action_help: Optional override for the action line in the prompt; if None, derived
            from ``available_actions`` via ``default_action_help``.

    Returns:
        (levels_completed, steps_used, final_obs).
    """
    env = arc.make(game_id, seed=seed, render_mode=None)
    if env is None:
        raise RuntimeError(f"Failed to create environment for {game_id}")

    obs = env.reset()
    if obs is None:
        raise RuntimeError(f"Failed to reset environment for {game_id}")

    info = getattr(env, "info", None)
    title = getattr(info, "title", game_id) if info else game_id
    description = getattr(info, "description", "Reach the goal.") if info else "Reach the goal."

    action_help_override = action_help

    steps_used = 0
    levels_completed = getattr(obs, "levels_completed", 0) or 0

    while steps_used < max_steps:
        state_name = getattr(getattr(obs, "state", None), "name", "UNKNOWN")
        if state_name == "WIN":
            break
        if state_name in ("LOSE", "LOST", "GAME_OVER"):
            break

        grid_text = serialize_frame_to_text(
            getattr(obs, "frame", []),
            grid_size=grid_size,
        )
        avail = getattr(obs, "available_actions", [1, 2, 3, 4])
        ah = (
            action_help_override
            if action_help_override is not None
            else default_action_help(list(avail))
        )
        prompt = f"""You are playing "{title}": {description}

Current grid (y increases downward, . = empty, numbers = objects):
{grid_text}

Step {steps_used + 1}/{max_steps}. Levels completed: {levels_completed}
{ah}"""

        response = llm.prompt(prompt)
        action = parse_action_from_response(response, avail)
        if action is None:
            action = _ACTION_MAP.get(avail[0] if avail else 1, GameAction.ACTION1)

        obs = env.step(action, reasoning={"step": steps_used + 1})
        steps_used += 1
        if obs is None:
            break
        levels_completed = getattr(obs, "levels_completed", levels_completed) or levels_completed

    return (levels_completed, steps_used, obs)
