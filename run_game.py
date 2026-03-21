#!/usr/bin/env python3
"""
ARC-AGI-3 Game Runner

CLI tool for running and testing ARC-AGI-3 games.
Based on patterns from redpill/launch.py and redpill/remote_attempt.py

Usage:
    uv run python run_game.py --game co01 --version auto
    uv run python run_game.py --game co01 --mode auto --steps 50
    uv run python run_game.py --game ls20 --mode human
    uv run python run_game.py --game sk01 --mode human
    uv run python run_game.py --game sk01 --mode human-toolkit
    ARC_GAME_ID=co01-<ver> uv run python run_game.py
    ARC_OPERATION_MODE=offline uv run python run_game.py
    ARC_OPERATION_MODE=competition uv run python run_game.py  # toolkit competition rules

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
    """Load repo-root ``.env`` so ``ARC_API_KEY``, ``ARC_OPERATION_MODE`` / ``OPERATION_MODE`` work with ``uv run``."""
    if load_dotenv is not None:
        load_dotenv(_ROOT / ".env")


@dataclass
class GameConfig:
    """Configuration for running a game."""

    game_id: str = "co01"
    version: str = "auto"
    seed: int = 0
    steps: int = 100
    mode: str = "terminal"  # terminal, auto, human / human-toolkit (pygame GUI)
    #: Passed to ``arc.make(..., render_mode=...)`` — terminal / none / terminal-fast (not GUI).
    render_mode: str | None = None
    operation_mode: OperationMode = OperationMode.NORMAL


@dataclass
class GameResult:
    """Result from running a game."""

    steps_completed: int
    final_state: Any | None = None


def get_operation_mode() -> OperationMode:
    """Get operation mode from ``ARC_OPERATION_MODE`` (or ``OPERATION_MODE`` toolkit alias)."""
    raw = os.getenv("ARC_OPERATION_MODE") or os.getenv("OPERATION_MODE", "normal")
    mode = raw.strip().lower()
    if mode == "online":
        return OperationMode.ONLINE
    if mode == "offline":
        return OperationMode.OFFLINE
    if mode == "competition":
        return OperationMode.COMPETITION
    return OperationMode.NORMAL


def resolve_full_game_id(raw_id: str, version_arg: str) -> str:
    """Return full ``arc.make`` id: either ``raw_id`` if it already has a version suffix, else stem + resolved package."""
    version_pattern = re.compile(r"-[0-9a-f]{8}$|-[vV]\d+$")
    if version_pattern.search(raw_id):
        return raw_id
    stem = raw_id
    if version_arg == "auto":
        return full_game_id_for_stem(stem)
    return full_game_id_for_stem(stem, version_arg)


def get_game_id(default: str = "co01") -> str:
    """Get game ID from environment variable or use default."""
    env_game_id = os.getenv("ARC_GAME_ID", "").strip()
    if env_game_id:
        print(f"Using game from ARC_GAME_ID: {env_game_id}")
        return env_game_id
    return default


def _list_available_games_disk_scan(env_dir: Path) -> None:
    """Fallback: walk ``environment_files`` and read ``metadata.json`` titles."""
    print("\nAvailable Games (disk scan):")
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
    print("\nOr use environment variable:")
    print("  ARC_GAME_ID=co01-<ver> uv run python run_game.py")


def list_available_games() -> None:
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
            operation_mode=get_operation_mode(),
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
        print(f"get_environments() unavailable ({err!r}); using disk scan.\n")
    elif games is not None:
        print("get_environments() returned empty; using disk scan.\n")
    else:
        print("get_environments() not found on Arcade; using disk scan.\n")

    _list_available_games_disk_scan(env_dir)


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

        else:
            # Auto mode with random actions
            print("Running in auto mode with random actions")
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
                        "thought": "Auto-play random action",
                        "step_index": step_index,
                        "planned_steps": config.steps,
                    },
                )
                step_count = step_index
                final_state = result

                if step_index % 10 == 0:
                    print(f"Step {step_index}/{config.steps}")

            print(f"\nCompleted {step_count} steps")

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
  uv run python run_game.py --game co01 --mode auto --steps 50
  uv run python run_game.py --game ls20 --mode human
  uv run python run_game.py --game sk01 --mode human
  uv run python run_game.py --game sk01 --mode human-toolkit
  uv run python run_game.py --list

Render modes (https://docs.arcprize.org/toolkit/render-games):
  default, none, terminal, terminal-fast  (human GUI: use --mode human, pygame)

Environment Variables:
  ARC_GAME_ID=co01-<ver>     # Full game id from metadata
  ARC_OPERATION_MODE=offline # normal / online / offline / competition
  OPERATION_MODE=...         # Optional toolkit alias (if ARC_OPERATION_MODE unset)
  ARC_API_KEY=...            # Required when online/competition uses API (see .env.example)

Optional:
  Repo-root .env is loaded at startup when python-dotenv is installed (bundled with arc-agi).

Note:
  No create_scorecard / scorecard_id / close_scorecard — use Arcade in a script or the quickstarter
  for custom scorecards; toolkit: Create / Get / Close scorecard docs on docs.arcprize.org.
        """,
    )

    parser.add_argument("--game", "-g", type=str, help="Game ID (e.g., co01)")
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
        choices=["terminal", "auto", "human", "human-toolkit"],
        default="auto",
        help=(
            "Play: terminal (typed 1–6), human (pygame WASD/click), "
            "human-toolkit (same pygame UI; legacy name), or auto (random)"
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
        help="Steps for auto mode (default: 100)",
    )
    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="List games (Arcade.get_environments; see docs.arcprize.org/toolkit/list-games)",
    )

    return parser


def main():
    """Main entry point."""
    _load_dotenv()
    parser = setup_argparser()
    args = parser.parse_args()

    if args.list:
        list_available_games()
        return

    # Get game ID from args or environment
    game_id = args.game or get_game_id()

    if not game_id:
        print("Error: --game is required (unless using ARC_GAME_ID)")
        parser.print_help()
        sys.exit(1)

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
        operation_mode=get_operation_mode(),
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
