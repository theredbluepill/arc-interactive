"""Golden checks for solvability harness (real env transitions)."""

from __future__ import annotations

import sys
import unittest
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
DEVTOOLS = ROOT / "devtools"
for p in (str(ROOT), str(SCRIPTS), str(DEVTOOLS)):
    if p not in sys.path:
        sys.path.insert(0, p)

from arc_agi import Arcade, OperationMode  # noqa: E402
from arcengine import GameAction, GameState  # noqa: E402
from env_resolve import load_stem_game_py  # noqa: E402
from solvability_common import (  # noqa: E402
    canonical_version_for_stem,
    full_game_id_canonical,
)
from solvers.engine_bfs import engine_bfs_single_level  # noqa: E402
from solvers.push_switch import verify_push_stem, verify_switch_stem  # noqa: E402


class SolvabilityGoldenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.arcade = Arcade(
            environments_dir=str(ROOT / "environment_files"),
            operation_mode=OperationMode.OFFLINE,
        )

    def test_co01_engine_bfs_level0(self) -> None:
        env = self.arcade.make(full_game_id_canonical("co01"), seed=0, render_mode=None)
        assert env is not None
        bfs = engine_bfs_single_level(
            env,
            level_index=0,
            max_nodes=80_000,
            max_depth=80,
            max_click_cells=2500,
            allowed_action_ids=None,
        )
        self.assertTrue(bfs.ok, bfs.reason)

    def test_co01_recolor_pad_opens_matching_door(self) -> None:
        env = self.arcade.make(full_game_id_canonical("co01"), seed=0, render_mode=None)
        assert env is not None
        env.reset()
        game = env._game
        door = game.current_level.get_sprites_by_tag("door")[0]
        self.assertTrue(door.is_collidable)

        for _ in range(2):
            env.step(GameAction.ACTION4, reasoning={})
        self.assertEqual((game._player.x, game._player.y), (3, 5))
        self.assertEqual(game._active, 8)
        self.assertFalse(door.is_collidable)
        # Player renders above the pad it stands on.
        self.assertGreater(game._player.layer, 0)

        res = None
        for _ in range(5):
            res = env.step(GameAction.ACTION4, reasoning={})
        assert res is not None
        self.assertEqual(res.levels_completed, 1)

    def test_co01_levels_have_no_door_bypass(self) -> None:
        """Doors must gate the goal: walling every door off leaves it unreachable."""
        mod = load_stem_game_py("co01", "_co01_bypass_check")
        for idx, level in enumerate(mod.levels):
            blocked = {(s.x, s.y) for s in level._sprites if "wall" in s.tags or "door" in s.tags}
            player = level.get_sprites_by_tag("player")[0]
            goal = level.get_sprites_by_tag("goal")[0]
            gw, gh = level.grid_size
            start = (player.x, player.y)
            seen = {start}
            q = deque([start])
            while q:
                x, y = q.popleft()
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if (
                        0 <= nx < gw
                        and 0 <= ny < gh
                        and (nx, ny) not in blocked
                        and (nx, ny) not in seen
                    ):
                        seen.add((nx, ny))
                        q.append((nx, ny))
            self.assertNotIn((goal.x, goal.y), seen, f"level {idx + 1} door bypass")

    def test_bp01_action5_powers_tower_under_player(self) -> None:
        env = self.arcade.make(full_game_id_canonical("bp01"), seed=0, render_mode=None)
        assert env is not None
        env.reset()
        for _ in range(3):
            env.step(GameAction.ACTION4, reasoning={})

        game = env._game
        self.assertEqual((game._player.x, game._player.y), (4, 1))
        self.assertEqual(game._on, 0)
        untagged = game.current_level.get_sprite_at(
            game._player.x, game._player.y, ignore_collidable=True
        )
        tagged = game.current_level.get_sprite_at(
            game._player.x,
            game._player.y,
            tag="tower",
            ignore_collidable=True,
        )
        self.assertEqual(untagged.name, "player")
        self.assertEqual(tagged.name, "tower")

        env.step(GameAction.ACTION5, reasoning={})

        self.assertEqual(game._on, 1)
        powered = game.current_level.get_sprite_at(
            game._player.x,
            game._player.y,
            tag="tower",
            ignore_collidable=True,
        )
        assert powered is not None
        self.assertIn("powered", powered.tags)

    def test_sk01_push_plan_level0(self) -> None:
        stem = "sk01"
        env = self.arcade.make(full_game_id_canonical(stem), seed=0, render_mode=None)
        assert env is not None
        v = canonical_version_for_stem(stem)
        ok, msg = verify_push_stem(env, stem, v, 0, variant="default")
        self.assertTrue(ok, msg)

    def test_fs01_switch_plan_level0(self) -> None:
        stem = "fs01"
        env = self.arcade.make(full_game_id_canonical(stem), seed=0, render_mode=None)
        assert env is not None
        v = canonical_version_for_stem(stem)
        ok, msg = verify_switch_stem(env, stem, v, 0, mode="all")
        self.assertTrue(ok, msg)

    def test_action6_step_lo01(self) -> None:
        env = self.arcade.make(full_game_id_canonical("lo01"), seed=0, render_mode=None)
        assert env is not None
        env.reset()
        r = env.step(GameAction.ACTION6, data={"x": 1, "y": 1}, reasoning={})
        assert r is not None
        self.assertNotEqual(r.state, GameState.GAME_OVER)


if __name__ == "__main__":
    unittest.main()
