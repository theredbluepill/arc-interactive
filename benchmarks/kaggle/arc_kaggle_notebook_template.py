"""
Kaggle notebook template for ARC benchmark tasks (ez01, sk01, tt01, sv01).

Copy cells from this file into a new task notebook at:
https://www.kaggle.com/benchmarks/tasks/new

Paste the **bootstrap** from ``notebooks/README.md`` (``pip`` / ``uv run`` for
Python 3.11 papermill) above or below this task code in the Kaggle notebook.
Optionally run ``python3 benchmarks/kaggle/rebuild_kaggle_notebooks.py`` to emit
``notebooks/*.ipynb`` (markdown + embedded task + bootstrap).

Prerequisites:
  1. Add a dataset that includes the full ``environment_files/`` tree (or at least
     the game folders you reference: ez01, sk01, tt01, sv01 each with one version dir).
  2. Publish the dataset, then attach it via "+ Add data". It mounts as
     ``/kaggle/input/datasets/<user>/<dataset>/`` (e.g. ``…/poonszesen/arc-interactive``).

For multiple tasks, duplicate the notebook or add cells that call each
``@kbench.task`` (see ``benchmarks/kaggle/arc_tasks.py`` in the repo).
"""

# --- Cell 1: Install dependencies (run first) ---
# Kaggle Benchmark bootstrap: see benchmarks/kaggle/notebooks/README.md
# Worker deps: see PIP_PKGS_KAGGLE_WORKER in rebuild_kaggle_notebooks.py.
# !pip install -q arc-agi arcengine

# --- Cell 2: Task and wrapper ---
import sys
from pathlib import Path


def _resolve_kaggle_dataset_root() -> Path:
    """Find a mounted Kaggle input dir that contains ``environment_files/``.

    Tries this repo’s published dataset first, then other common layouts.
    """
    kaggle_in = Path("/kaggle/input")
    preferred = (
        Path("/kaggle/input/datasets/poonszesen/arc-interactive"),
        Path("/kaggle/input/arc-interactive"),
        Path("/kaggle/input/arc-interactive-games"),
    )
    for root in preferred:
        ef = root / "environment_files"
        if ef.is_dir() and any(ef.iterdir()):
            return root
    datasets_root = Path("/kaggle/input/datasets")
    if datasets_root.is_dir():
        for user_dir in sorted(datasets_root.iterdir()):
            if not user_dir.is_dir():
                continue
            for child in sorted(user_dir.iterdir()):
                if not child.is_dir():
                    continue
                ef = child / "environment_files"
                if ef.is_dir() and any(ef.iterdir()):
                    return child
    if kaggle_in.is_dir():
        for child in sorted(kaggle_in.iterdir()):
            if not child.is_dir() or child.name == "datasets":
                continue
            ef = child / "environment_files"
            if ef.is_dir() and any(ef.iterdir()):
                return child
    for root in preferred:
        if root.is_dir():
            return root
    return preferred[0]


INPUT_DIR = _resolve_kaggle_dataset_root()
ENVIRONMENTS_DIR = str(INPUT_DIR / "environment_files")
_ef = Path(ENVIRONMENTS_DIR)
if not _ef.is_dir():
    names = [p.name for p in kaggle_in.iterdir()] if (kaggle_in := Path("/kaggle/input")).is_dir() else []
    raise RuntimeError(
        f"environment_files missing at {ENVIRONMENTS_DIR}. "
        "On the task notebook use **+ Add data** and attach a dataset whose root contains "
        "an **environment_files/** tree (zip your repo’s environment_files or full repo). "
        f"/kaggle/input: {names!r}"
    )
if not any(_ef.iterdir()):
    raise RuntimeError(
        f"environment_files is empty at {_ef}. Re-upload the dataset with game folders (one dir per stem with metadata.json)."
    )

import json


def _full_game_id(stem: str) -> str:
    base = _ef / stem
    if not base.is_dir():
        raise RuntimeError(f"missing {base}")
    found: list[str] = []
    for d in sorted(base.iterdir(), key=lambda p: p.name.lower()):
        if not d.is_dir():
            continue
        mp = d / "metadata.json"
        if not mp.is_file():
            continue
        data = json.loads(mp.read_text(encoding="utf-8"))
        gid = data.get("game_id")
        if isinstance(gid, str):
            found.append(gid)
    if len(found) == 1:
        return found[0]
    if len(found) == 0:
        raise RuntimeError(f"{base}: no metadata.json with game_id")
    raise RuntimeError(f"{base}: multiple version dirs; disambiguate in dataset")


sys.path.insert(0, str(INPUT_DIR))

import kaggle_benchmarks as kbench
from arc_agi import Arcade, OperationMode

# Copy of run_game_with_llm and helpers (inline for Kaggle)
import re
from arcengine import GameAction

_ACTION_MAP = {
    1: GameAction.ACTION1, 2: GameAction.ACTION2, 3: GameAction.ACTION3,
    4: GameAction.ACTION4, 5: GameAction.ACTION5, 6: GameAction.ACTION6,
    7: GameAction.ACTION7,
}


def default_action_help(available_actions):
    avail = list(available_actions)
    if avail == [1, 2, 3, 4]:
        return (
            "Actions: use IDs 1–4 for this game's ACTION1–ACTION4. "
            "Their meaning is defined by the game (not necessarily up/down/left/right; "
            "see https://docs.arcprize.org/actions). Reply with a single digit (1-4)."
        )
    if avail == [1, 2, 3, 4, 5]:
        return (
            "Actions: use IDs 1–5 for this game's ACTION1–ACTION5. "
            "Semantics are game-specific; 1–4 are not necessarily cardinal moves. "
            "Reply with a single digit (1-5)."
        )
    return (
        f"Available actions: {avail}. "
        "Reply with a single digit that is one of these action IDs."
    )


def serialize_frame_to_text(frame, grid_size=8):
    import numpy as np
    if not frame:
        return "(no frame)"
    arr = np.asarray(frame[0])
    region = arr[:min(grid_size, arr.shape[0]), :min(grid_size, arr.shape[1])]
    lines = []
    for row in region:
        chars = []
        for cell in row:
            val = int(cell)
            chars.append("." if val == 0 else (str(val) if val < 10 else chr(ord("a") + val - 10)))
        lines.append("".join(chars))
    return "\n".join(lines)


def parse_action(response, available_actions):
    for pattern in [r"\bACTION([1-7])\b", r"\bACTION\s*([1-7])\b", r"\b([1-7])\b"]:
        m = re.search(pattern, response.strip().upper(), re.IGNORECASE)
        if m:
            num = int(m.group(1))
            if num in available_actions and num in _ACTION_MAP:
                return _ACTION_MAP[num]
    return _ACTION_MAP.get(available_actions[0] if available_actions else 1, GameAction.ACTION1)


def run_game_with_llm(arc, game_id, llm, seed=0, max_steps=50, grid_size=8, action_help=None):
    env = arc.make(game_id, seed=seed, render_mode=None)
    if env is None:
        raise RuntimeError(f"Failed to create environment for {game_id}")
    obs = env.reset()
    if obs is None:
        raise RuntimeError(f"Failed to reset for {game_id}")
    info = getattr(env, "info", None)
    title = getattr(info, "title", game_id) if info else game_id
    desc = getattr(info, "description", "Reach the goal.") if info else "Reach the goal."
    action_help_override = action_help
    steps_used = 0
    levels_completed = getattr(obs, "levels_completed", 0) or 0
    while steps_used < max_steps:
        state_name = getattr(getattr(obs, "state", None), "name", "UNKNOWN")
        if state_name in ("WIN", "LOSE", "LOST", "GAME_OVER"):
            break
        grid_text = serialize_frame_to_text(getattr(obs, "frame", []), grid_size)
        avail = getattr(obs, "available_actions", [1, 2, 3, 4])
        ah = action_help_override if action_help_override is not None else default_action_help(list(avail))
        prompt = (
            f'You are playing "{title}": {desc}\n\n'
            f"Current grid (y increases downward, . = empty, numbers = objects):\n{grid_text}\n\n"
            f"Step {steps_used + 1}/{max_steps}. Levels completed: {levels_completed}\n{ah}"
        )
        response = llm.prompt(prompt)
        action = parse_action(response, avail)
        obs = env.step(action, reasoning={"step": steps_used + 1})
        steps_used += 1
        if obs is None:
            break
        levels_completed = getattr(obs, "levels_completed", levels_completed) or levels_completed
    return levels_completed, steps_used, obs


@kbench.task(name="arc_ez01_go_up")
def arc_ez01_go_up(llm, seed: int = 0, max_steps: int = 30):
    """Play ARC-AGI-3 ez01 (Go Up): reach the goal using ACTION1–4 (IDs 1–4); semantics are game-specific."""
    arc = Arcade(environments_dir=ENVIRONMENTS_DIR, operation_mode=OperationMode.OFFLINE)
    levels_completed, _, _ = run_game_with_llm(arc, _full_game_id("ez01"), llm, seed, max_steps, 8)
    kbench.assertions.assert_true(levels_completed >= 1, expectation="Complete at least 1 level.")


@kbench.task(name="arc_sk01_sokoban")
def arc_sk01_sokoban(llm, seed: int = 0, max_steps: int = 200):
    """sk01 Sokoban: push blocks onto targets via ACTION1–4 (IDs 1–4)."""
    arc = Arcade(environments_dir=ENVIRONMENTS_DIR, operation_mode=OperationMode.OFFLINE)
    levels_completed, _, _ = run_game_with_llm(arc, _full_game_id("sk01"), llm, seed, max_steps, 16)
    kbench.assertions.assert_true(levels_completed >= 1, expectation="Complete at least 1 level.")


@kbench.task(name="arc_tt01_collect")
def arc_tt01_collect(llm, seed: int = 0, max_steps: int = 200):
    """tt01: collect yellow targets, avoid red hazards via ACTION1–4 (IDs 1–4)."""
    arc = Arcade(environments_dir=ENVIRONMENTS_DIR, operation_mode=OperationMode.OFFLINE)
    levels_completed, _, _ = run_game_with_llm(arc, _full_game_id("tt01"), llm, seed, max_steps, 24)
    kbench.assertions.assert_true(levels_completed >= 1, expectation="Complete at least 1 level.")


@kbench.task(name="arc_sv01_survive")
def arc_sv01_survive(llm, seed: int = 0, max_steps: int = 80):
    """sv01: survive 60 steps per level (ACTION1–5; see game / GAMES.md for this build)."""
    arc = Arcade(environments_dir=ENVIRONMENTS_DIR, operation_mode=OperationMode.OFFLINE)
    levels_completed, _, _ = run_game_with_llm(arc, _full_game_id("sv01"), llm, seed, max_steps, 24)
    kbench.assertions.assert_true(levels_completed >= 1, expectation="Complete at least 1 survival level.")

# --- Cell 3: Run one task (duplicate cell or notebook per task on Kaggle) ---
arc_ez01_go_up.run(llm=kbench.llm, seed=0, max_steps=30)
