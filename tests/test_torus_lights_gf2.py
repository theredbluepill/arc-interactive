"""Lights Out GF(2) helpers match lo02/lo03/lo05 level data."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
DEVTOOLS = ROOT / "devtools"
for p in (str(ROOT), str(SCRIPTS), str(DEVTOOLS)):
    if p not in sys.path:
        sys.path.insert(0, p)

from solvability_common import (  # noqa: E402
    canonical_version_for_stem,
    load_stem_game_module,
)
from solvers.torus_lights_gf2 import (  # noqa: E402
    apply_click,
    arc_level_is_solvable,
    is_solvable,
    solve_clicks_mask,
)


def _cell_index(gw: int, gx: int, gy: int) -> int:
    return gy * gw + gx


class TorusLightsGf2Tests(unittest.TestCase):
    def test_lo02_lo03_all_levels_solvable(self) -> None:
        for stem, mode in (("lo02", "orth"), ("lo03", "king")):
            ver = canonical_version_for_stem(stem)
            mod = load_stem_game_module(stem, ver, f"_test_torus_{stem}")
            for i, lvl in enumerate(mod.levels):
                with self.subTest(stem=stem, level=i):
                    self.assertTrue(
                        arc_level_is_solvable(lvl, mode=mode),
                        f"{stem} level {i} should be GF(2)-solvable",
                    )

    def test_solution_mask_clears_state_lo02_level4(self) -> None:
        stem = "lo02"
        ver = canonical_version_for_stem(stem)
        mod = load_stem_game_module(stem, ver, "_test_torus_lo02_l4")
        lvl = mod.levels[4]
        gw, gh = lvl.grid_size
        raw = lvl.get_data("lights_on") or []
        lit = {(int(p[0]), int(p[1])) for p in raw}
        walls = {(s.x, s.y) for s in lvl.get_sprites_by_tag("wall")}
        ok, mask = solve_clicks_mask(lit, walls, gw, gh, mode="orth")
        self.assertTrue(ok, "expected a GF(2) solution")
        working = set(lit)
        for gy in range(gh):
            for gx in range(gw):
                if (mask >> _cell_index(gw, gx, gy)) & 1:
                    apply_click(working, gw, gh, gx, gy, walls, mode="orth")
        self.assertEqual(len(working), 0)

    def test_known_unsolvable_orth_pattern(self) -> None:
        bad = {(1, 1), (2, 1), (1, 2), (2, 2)}
        self.assertFalse(is_solvable(bad, set(), 5, 5, mode="orth"))

    def test_lo05_all_levels_solvable_knight_clip(self) -> None:
        stem = "lo05"
        ver = canonical_version_for_stem(stem)
        mod = load_stem_game_module(stem, ver, "_test_knight_lo05")
        for i, lvl in enumerate(mod.levels):
            with self.subTest(stem=stem, level=i):
                self.assertTrue(
                    arc_level_is_solvable(lvl, mode="knight_clip"),
                    f"lo05 level {i} should be GF(2)-solvable",
                )

    def test_lo05_solution_mask_clears_every_level(self) -> None:
        stem = "lo05"
        ver = canonical_version_for_stem(stem)
        mod = load_stem_game_module(stem, ver, "_test_knight_lo05_masks")
        for i, lvl in enumerate(mod.levels):
            gw, gh = lvl.grid_size
            raw = lvl.get_data("lights_on") or []
            lit = {(int(p[0]), int(p[1])) for p in raw}
            walls = {(s.x, s.y) for s in lvl.get_sprites_by_tag("wall")}
            ok, mask = solve_clicks_mask(lit, walls, gw, gh, mode="knight_clip")
            with self.subTest(level=i):
                self.assertTrue(ok, f"expected a GF(2) solution for level {i}")
                working = set(lit)
                for gy in range(gh):
                    for gx in range(gw):
                        if (mask >> _cell_index(gw, gx, gy)) & 1:
                            apply_click(working, gw, gh, gx, gy, walls, mode="knight_clip")
                self.assertEqual(len(working), 0)

    def test_old_lo05_level1_pattern_is_unreachable(self) -> None:
        # the regression this fix exists for: the original hand-authored level-1
        # pattern {(3, 3)} lies outside the clipped knight matrix's column space
        # (rank 56/64) — the game could never advance past level 1
        self.assertFalse(is_solvable({(3, 3)}, set(), 8, 8, mode="knight_clip"))

    def test_knight_clip_does_not_wrap(self) -> None:
        # a corner click toggles exactly 3 cells: itself + 2 in-board knight
        # hops; wrapped arithmetic would claim more
        from solvers.torus_lights_gf2 import click_affected_cells

        cells = click_affected_cells(8, 8, 0, 0, set(), mode="knight_clip")
        self.assertEqual(sorted(cells), [(0, 0), (1, 2), (2, 1)])


if __name__ == "__main__":
    unittest.main()
