#!/usr/bin/env python3
"""
ARC-AGI-3 Game Runner

CLI tool for running and testing ARC-AGI-3 games.
Based on patterns from redpill/launch.py and redpill/remote_attempt.py

Usage:
    uv run python run_game.py --game co01 --version v1
    uv run python run_game.py --game co01 --version v1 --mode auto --steps 50
    ARC_GAME_ID=co01-v1 uv run python run_game.py
    ARC_OPERATION_MODE=offline uv run python run_game.py
"""

from __future__ import annotations

import argparse
import os
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    from arc_agi import Arcade, OperationMode
    from arcengine import GameAction
except ImportError as e:
    print(f"Error: Required packages not found: {e}")
    print("Please ensure arc-agi and arcengine are installed.")
    sys.exit(1)


@dataclass
class GameConfig:
    """Configuration for running a game."""

    game_id: str = "co01-v1"
    version: str = "v1"
    seed: int = 0
    steps: int = 100
    mode: str = "terminal"  # "terminal" or "auto"
    render_terminal: bool = True
    operation_mode: OperationMode = OperationMode.NORMAL


@dataclass
class GameResult:
    """Result from running a game."""

    steps_completed: int
    final_state: Any | None = None


def get_operation_mode() -> OperationMode:
    """Get operation mode from environment variable."""
    mode = os.getenv("ARC_OPERATION_MODE", "normal").lower()
    if mode == "online":
        return OperationMode.ONLINE
    if mode == "offline":
        return OperationMode.OFFLINE
    return OperationMode.NORMAL


def get_game_id(default: str = "co01") -> str:
    """Get game ID from environment variable or use default."""
    env_game_id = os.getenv("ARC_GAME_ID", "").strip()
    if env_game_id:
        print(f"Using game from ARC_GAME_ID: {env_game_id}")
        return env_game_id
    return default


def list_available_games():
    """List all available games in environment_files directory."""
    env_dir = Path(__file__).parent / "environment_files"

    if not env_dir.exists():
        print("Error: environment_files directory not found")
        return

    print("\nAvailable Games:")
    print("-" * 50)

    games_found = []
    for game_dir in sorted(env_dir.iterdir()):
        if game_dir.is_dir():
            game_id = game_dir.name
            for version_dir in sorted(game_dir.iterdir()):
                if version_dir.is_dir():
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
    print("  ARC_GAME_ID=co01-v1 uv run python run_game.py")


def run_game(config: GameConfig) -> GameResult:
    """Run a game with the given configuration.

    Based on patterns from redpill/remote_attempt.py
    """
    operation_mode = config.operation_mode

    print(f"\nStarting {config.game_id} (seed={config.seed})")
    print(f"Operation mode: {operation_mode.name}")
    print("=" * 50)

    arc = Arcade(
        environments_dir="environment_files",
        operation_mode=operation_mode,
    )

    environment = arc.make(
        config.game_id,
        seed=config.seed,
        render_mode="terminal" if config.render_terminal else None,
    )

    if environment is None:
        raise RuntimeError(f"Failed to create environment for game {config.game_id}")

    step_count = 0
    final_state = None

    try:
        if config.mode == "terminal":
            # Interactive mode
            print("Controls: 1-4=Movement (scrambled!), 5-6=Special, q=Quit")
            print("-" * 50)

            while True:
                try:
                    cmd = input("\nAction [1-6/q]: ").strip().lower()

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
                        print("Invalid action. Use 1-6 or q")

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
  uv run python run_game.py --game co01 --version v1
  uv run python run_game.py --game co01 --version v1 --mode auto --steps 50
  uv run python run_game.py --list
  
Environment Variables:
  ARC_GAME_ID=co01-v1        # Specify game ID
  ARC_OPERATION_MODE=offline # Set operation mode (online/offline/normal)
        """,
    )

    parser.add_argument("--game", "-g", type=str, help="Game ID (e.g., co01)")
    parser.add_argument(
        "--version", "-v", type=str, default="v1", help="Game version (default: v1)"
    )
    parser.add_argument(
        "--seed", "-s", type=int, default=0, help="Random seed (default: 0)"
    )
    parser.add_argument(
        "--mode",
        "-m",
        type=str,
        choices=["terminal", "auto"],
        default="auto",
        help="Mode: terminal (interactive) or auto (random actions, default)",
    )
    parser.add_argument(
        "--steps",
        "-n",
        type=int,
        default=100,
        help="Steps for auto mode (default: 100)",
    )
    parser.add_argument(
        "--list", "-l", action="store_true", help="List all available games"
    )

    return parser


def main():
    """Main entry point."""
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

    # Build full game ID with version
    full_game_id = f"{game_id}-{args.version}"

    # Create configuration
    config = GameConfig(
        game_id=full_game_id,
        version=args.version,
        seed=args.seed,
        steps=args.steps,
        mode=args.mode,
        render_terminal=True,
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
