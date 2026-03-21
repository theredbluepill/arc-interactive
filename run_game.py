#!/usr/bin/env python3
"""
ARC-AGI-3 Game Runner

CLI tool for running and testing ARC-AGI-3 games.
Based on patterns from redpill/launch.py and redpill/remote_attempt.py

Usage:
    uv run python run_game.py --game co01 --version auto
    uv run python run_game.py --game co01 --mode random-agent --steps 50
    uv run python run_game.py --game ls20 --mode human
    uv run python run_game.py --game sk01 --mode human
    uv run python run_game.py --game sk01 --mode human-toolkit
    uv run python run_game.py   # local environments, default stem co01; add --online for API + default stem ls20

Game selection: use ``--game`` (recommended). ``ARC_GAME_ID`` is never required if you pass
``--game``. Env ``ARC_GAME_ID`` only applies when ``--game`` is omitted (overrides the mode default).

CLI: ``--online`` / ``--offline`` / ``--competition`` select operation mode; optional env
``ARC_OPERATION_MODE`` / ``OPERATION_MODE`` when none of those flags are passed. See ``--help``.

Online scoring: this script does not pass scorecard_id to arc.make; see README (Online scorecard / competition).
"""

from __future__ import annotations

import argparse
import os
import random
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parent
_SCRIPTS = _ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
from env_resolve import full_game_id_for_stem  # noqa: E402

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None  # type: ignore[misc, assignment]

try:
    from arc_agi import Arcade, OperationMode
    from arcengine import GameAction
except ImportError as e:
    print(f"Error: Required packages not found: {e}")
    print("Please ensure arc-agi and arcengine are installed.")
    sys.exit(1)


def _load_dotenv() -> None:
    """Load repo-root ``.env`` (e.g. ``ARC_API_KEY`` for ``--online`` / ``--competition``)."""
    if load_dotenv is not None:
        load_dotenv(_ROOT / ".env")


# Default stems when ``--game`` is omitted (``ARC_GAME_ID`` still overrides). Online uses a
# registry-friendly stem; offline keeps a small tutorial default.
DEFAULT_GAME_STEM_OFFLINE = "co01"
DEFAULT_GAME_STEM_ONLINE = "ls20"


@dataclass
class GameConfig:
    """Configuration for running a game."""

    game_id: str = DEFAULT_GAME_STEM_OFFLINE
    version: str = "auto"
    seed: int = 0
    steps: int = 100
    mode: str = "terminal"  # terminal, random-agent, human / human-toolkit (pygame GUI)
    #: Passed to ``arc.make(..., render_mode=...)`` — terminal / none / terminal-fast (not GUI).
    render_mode: str | None = None
    operation_mode: OperationMode = OperationMode.OFFLINE


@dataclass
class GameResult:
    """Result from running a game."""

    steps_completed: int
    final_state: Any | None = None


def get_operation_mode_from_env() -> OperationMode:
    """``Arcade`` mode from ``ARC_OPERATION_MODE`` / ``OPERATION_MODE`` (legacy / scripts)."""
    raw = os.getenv("ARC_OPERATION_MODE") or os.getenv("OPERATION_MODE")
    if raw is None or not raw.strip():
        return OperationMode.OFFLINE
    mode = raw.strip().lower()
    if mode == "online":
        return OperationMode.ONLINE
    if mode == "offline":
        return OperationMode.OFFLINE
    if mode == "competition":
        return OperationMode.COMPETITION
    if mode == "normal":
        return OperationMode.NORMAL
    return OperationMode.NORMAL


def resolve_operation_mode(args: argparse.Namespace) -> OperationMode:
    """CLI flags win over env. Default when neither flag nor env: offline."""
    if getattr(args, "competition", False):
        return OperationMode.COMPETITION
    if getattr(args, "online", False):
        return OperationMode.ONLINE
    if getattr(args, "offline", False):
        return OperationMode.OFFLINE
    return get_operation_mode_from_env()


def get_default_game_stem(operation_mode: OperationMode) -> str:
    if operation_mode == OperationMode.ONLINE:
        return DEFAULT_GAME_STEM_ONLINE
    return DEFAULT_GAME_STEM_OFFLINE


def resolve_full_game_id(raw_id: str, version_arg: str) -> str:
    """Return full ``arc.make`` id: either ``raw_id`` if it already has a version suffix, else stem + resolved package."""
    version_pattern = re.compile(r"-[0-9a-f]{8}$|-[vV]\d+$")
    if version_pattern.search(raw_id):
        return raw_id
    stem = raw_id
    if version_arg == "auto":
        return full_game_id_for_stem(stem)
    return full_game_id_for_stem(stem, version_arg)


def get_game_id(operation_mode: OperationMode) -> str:
    """Stem or full id when ``--game`` is omitted: optional ``ARC_GAME_ID``, else mode-based default."""
    env_game_id = os.getenv("ARC_GAME_ID", "").strip()
    if env_game_id:
        print(f"Using game from ARC_GAME_ID: {env_game_id}")
        return env_game_id
    return get_default_game_stem(operation_mode)


def _list_available_games_env_walk(env_dir: Path) -> None:
    """Fallback: walk ``environment_files`` and read ``metadata.json`` titles."""
    print("\nAvailable Games (local environments scan):")
    print("-" * 50)

    games_found: list[str] = []
    for game_dir in sorted(env_dir.iterdir()):
        if not game_dir.is_dir():
            continue
        game_id = game_dir.name
        for version_dir in sorted(game_dir.iterdir()):
            if not version_dir.is_dir():
                continue
            metadata_file = version_dir / "metadata.json"
            title = game_id
            if metadata_file.exists():
                try:
                    import json

                    with open(metadata_file) as f:
                        metadata = json.load(f)
                    title = metadata.get("title", game_id)
                except Exception:
                    pass
            print(f"  {game_id}-{version_dir.name}: {title}")
            games_found.append(f"{game_id}-{version_dir.name}")

    print("-" * 50)
    print(f"\nTotal: {len(games_found)} game(s)")
    print("\nTo run a game:")
    print("  uv run python run_game.py --game <game_id> --version <version>")
    print("\nOptional override:")
    print("  ARC_GAME_ID=co01-<ver> uv run python run_game.py")


def list_available_games(operation_mode: OperationMode) -> None:
    """List games under ``environment_files`` using the toolkit when possible.

    Prefer :meth:`Arcade.get_environments` (see
    https://docs.arcprize.org/toolkit/list-games); fall back to a directory walk
    if the API is missing or fails.
    """
    env_dir = _ROOT / "environment_files"

    if not env_dir.is_dir():
        print("Error: environment_files directory not found")
        return

    games = None
    err: BaseException | None = None
    try:
        arc = Arcade(
            environments_dir=str(env_dir),
            operation_mode=operation_mode,
        )
        getter = getattr(arc, "get_environments", None)
        if callable(getter):
            games = getter()
    except BaseException as e:
        err = e

    if games:
        print("\nAvailable Games (Arcade.get_environments):")
        print("  https://docs.arcprize.org/toolkit/list-games")
        print("-" * 50)
        infos = sorted(games, key=lambda g: g.game_id)
        for info in infos:
            print(f"  {info.game_id}: {info.title}")
        print("-" * 50)
        print(f"\nTotal: {len(infos)} game(s)")
        print("\nTo run a game:")
        print("  uv run python run_game.py --game <stem> --version auto")
        print("\nOr full id / env:")
        print("  ARC_GAME_ID=<game_id-from-above> uv run python run_game.py")
        return

    if err is not None:
        print(f"get_environments() unavailable ({err!r}); using local environments scan.\n")
    elif games is not None:
        print("get_environments() returned empty; using local environments scan.\n")
    else:
        print("get_environments() not found on Arcade; using local environments scan.\n")

    _list_available_games_env_walk(env_dir)


def run_game(config: GameConfig) -> GameResult:
    """Run a game with the given configuration.

    Based on patterns from redpill/remote_attempt.py
    """
    operation_mode = config.operation_mode

    print(f"\nStarting {config.game_id} (seed={config.seed})")
    print(f"Operation mode: {operation_mode.name}")
    rm = config.render_mode
    print(
        f"Toolkit render_mode: {rm!r} "
        f"(https://docs.arcprize.org/toolkit/render-games)"
    )
    print("=" * 50)

    arc = Arcade(
        environments_dir="environment_files",
        operation_mode=operation_mode,
    )

    make_kw: dict[str, Any] = {
        "seed": config.seed,
        "render_mode": config.render_mode,
    }
    if config.mode in ("human", "human-toolkit"):
        make_kw["include_frame_data"] = True

    environment = arc.make(config.game_id, **make_kw)

    if environment is None:
        raise RuntimeError(f"Failed to create environment for game {config.game_id}")

    step_count = 0
    final_state = None

    try:
        if config.mode in ("human", "human-toolkit"):
            from human_play_pygame import run_interactive_pygame

            print(
                "Pygame window: WASD/Arrows = ACTION1–4, Space/F/5 = ACTION5, "
                "click = ACTION6 (0–63), U or Ctrl/Cmd+Z = ACTION7, R = reset, Q = quit"
            )
            print("See https://docs.arcprize.org/actions")
            print("-" * 50)
            step_count = run_interactive_pygame(environment)
            final_state = environment.observation_space

        elif config.mode == "terminal":
            print("Controls: 1-4=Movement, 5-6=Special, 7=Undo (if game supports), q=Quit")
            print("-" * 50)

            while True:
                try:
                    cmd = input("\nAction [1-7/q]: ").strip().lower()

                    if cmd == "q":
                        print("\nGame exited by user")
                        break

                    action_map = {
                        "1": GameAction.ACTION1,
                        "2": GameAction.ACTION2,
                        "3": GameAction.ACTION3,
                        "4": GameAction.ACTION4,
                        "5": GameAction.ACTION5,
                        "6": GameAction.ACTION6,
                        "7": GameAction.ACTION7,
                    }

                    if cmd in action_map:
                        action = action_map[cmd]
                        result = environment.step(
                            action,
                            reasoning={
                                "thought": "User input action",
                                "step": step_count + 1,
                            },
                        )
                        step_count += 1
                        final_state = result
                        print(f"Step {step_count}: Action={action.name}")
                    else:
                        print("Invalid action. Use 1-7 or q")

                except KeyboardInterrupt:
                    print("\n\nGame interrupted")
                    break

        elif config.mode == "random-agent":
            # Random agent: uniform ACTION1–ACTION5 each step
            print("Running in random-agent mode (random ACTION1–ACTION5)")
            print("-" * 50)

            actions = [
                GameAction.ACTION1,
                GameAction.ACTION2,
                GameAction.ACTION3,
                GameAction.ACTION4,
                GameAction.ACTION5,
            ]

            rng = random.Random(config.seed)

            for step_index in range(1, config.steps + 1):
                action = rng.choice(actions)
                result = environment.step(
                    action,
                    reasoning={
                        "thought": "Random-agent action",
                        "step_index": step_index,
                        "planned_steps": config.steps,
                    },
                )
                step_count = step_index
                final_state = result

                if step_index % 10 == 0:
                    print(f"Step {step_index}/{config.steps}")

            print(f"\nCompleted {step_count} steps")

        else:
            raise ValueError(f"unsupported play mode: {config.mode!r}")

    except Exception as e:
        print(f"\nError during game execution: {e}")
        import traceback

        traceback.print_exc()

    return GameResult(steps_completed=step_count, final_state=final_state)


def setup_argparser():
    """Setup command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Run ARC-AGI-3 games",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run python run_game.py --game co01 --version auto
  uv run python run_game.py --game co01 --mode random-agent --steps 50
  uv run python run_game.py --game ls20 --mode human
  uv run python run_game.py --game sk01 --mode human
  uv run python run_game.py --game sk01 --mode human-toolkit
  uv run python run_game.py --list
  uv run python run_game.py --online --list        # API catalog (needs ARC_API_KEY)
  uv run python run_game.py --online --game ls20 --version auto

Render modes (https://docs.arcprize.org/toolkit/render-games):
  default, none, terminal, terminal-fast  (human GUI: use --mode human, pygame)

Operation mode (pick one; default offline / local environments):
  --online       API / online registry (put ARC_API_KEY in .env)
  --offline      Force local environments even if .env sets ARC_OPERATION_MODE=online
  --competition  Competition toolkit rules (API); see docs.arcprize.org/toolkit/competition_mode
  If none of the above: ARC_OPERATION_MODE / OPERATION_MODE env (legacy), else offline.

  Picking a game: prefer --game <stem>. No ARC_GAME_ID needed if you use --game.
  If you omit --game: default stem co01 (offline/normal/competition) or ls20 (--online); ARC_GAME_ID overrides.

Environment variables (optional):
  ARC_API_KEY=...            # Required for --online / --competition API calls (.env.example)
  ARC_OPERATION_MODE=...     # Only when no --online/--offline/--competition (legacy scripts)
  OPERATION_MODE=...         # Toolkit alias if ARC_OPERATION_MODE unset
  ARC_GAME_ID=...            # When --game omitted only (overrides default stem)

Repo-root .env is loaded at startup when python-dotenv is installed (bundled with arc-agi).

Note:
  No create_scorecard / scorecard_id / close_scorecard — use Arcade in a script or the quickstarter
  for custom scorecards; toolkit: Create / Get / Close scorecard docs on docs.arcprize.org.
        """,
    )

    parser.add_argument(
        "--game",
        "-g",
        type=str,
        help=(
            "Game stem or full id. If set, ignores ARC_GAME_ID. If omitted: default stem is "
            "co01 (local environments / competition) or ls20 (--online); ARC_GAME_ID env overrides that."
        ),
    )
    parser.add_argument(
        "--version",
        "-v",
        type=str,
        default="auto",
        help="Version dir when --game is stem-only, or 'auto' for sole dir (default: auto)",
    )
    parser.add_argument(
        "--seed", "-s", type=int, default=0, help="Random seed (default: 0)"
    )
    parser.add_argument(
        "--mode",
        "-m",
        type=str,
        choices=["terminal", "random-agent", "human", "human-toolkit"],
        default="random-agent",
        help=(
            "Play: terminal (typed 1–7), human (pygame WASD/click), "
            "human-toolkit (same pygame UI; legacy name), or random-agent (random ACTION1–5)"
        ),
    )
    parser.add_argument(
        "--render-mode",
        type=str,
        choices=["default", "none", "terminal", "terminal-fast"],
        default="default",
        help=(
            "arc.make(render_mode=...): default=infer from --mode (terminal uses "
            "terminal; else none). For a GUI use --mode human (pygame), not render_mode."
        ),
    )
    parser.add_argument(
        "--steps",
        "-n",
        type=int,
        default=100,
        help="Steps for random-agent mode (default: 100)",
    )
    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="List games (Arcade.get_environments; see docs.arcprize.org/toolkit/list-games)",
    )

    om = parser.add_mutually_exclusive_group()
    om.add_argument(
        "--online",
        action="store_true",
        help="Use API / online game registry (set ARC_API_KEY in .env)",
    )
    om.add_argument(
        "--offline",
        action="store_true",
        help="Force local environments (ignore ARC_OPERATION_MODE=online in .env)",
    )
    om.add_argument(
        "--competition",
        action="store_true",
        help="Competition toolkit mode (API); see docs.arcprize.org/toolkit/competition_mode",
    )

    return parser


def main():
    """Main entry point."""
    _load_dotenv()
    parser = setup_argparser()
    args = parser.parse_args()
    op_mode = resolve_operation_mode(args)

    if args.list:
        list_available_games(op_mode)
        return

    game_id = args.game or get_game_id(op_mode)
    full_game_id = resolve_full_game_id(game_id, args.version)

    # Resolve arc.make(render_mode=...) and which play loop runs.
    play_mode = args.mode
    if args.mode in ("human", "human-toolkit"):
        # Pygame UI in run_game; do not attach arc-agi matplotlib renderer.
        make_render_mode: str | None = None
    elif args.render_mode == "default":
        make_render_mode = "terminal" if args.mode == "terminal" else None
    elif args.render_mode == "none":
        make_render_mode = None
    else:
        make_render_mode = args.render_mode

    # Create configuration
    config = GameConfig(
        game_id=full_game_id,
        version=args.version,
        seed=args.seed,
        steps=args.steps,
        mode=play_mode,
        render_mode=make_render_mode,
        operation_mode=op_mode,
    )

    try:
        result = run_game(config)
        print(f"\nFinal Result: {result.steps_completed} steps completed")
        if result.final_state:
            print(f"State: {result.final_state}")
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
