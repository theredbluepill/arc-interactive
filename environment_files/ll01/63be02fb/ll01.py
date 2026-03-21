"""Generations lock: toggle cells with ACTION6; ACTION5 runs one Conway generation. After exactly N advances, the live set must match the target."""

from __future__ import annotations

from arcengine import (
    ARCBaseGame,
    Camera,
    GameAction,
    Level,
    RenderableUserDisplay,
    Sprite,
)

BACKGROUND_COLOR = 5
PADDING_COLOR = 4
CAM_W = CAM_H = 32
LIVE_C = 14
WALL_C = 3


class Ll01UI(RenderableUserDisplay):
    def __init__(self, gen: int, need: int, toggles: int) -> None:
        self._gen = gen
        self._need = need
        self._toggles = toggles

    def update(self, gen: int, need: int, toggles: int) -> None:
        self._gen = gen
        self._need = need
        self._toggles = toggles

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for i in range(min(self._need, 12)):
            frame[h - 2, 1 + i * 2] = 11 if i < self._gen else 2
        for i in range(min(self._toggles, 20)):
            frame[h - 1, 1 + i] = 9
        return frame


sprites = {
    "wall": Sprite(
        pixels=[[WALL_C]],
        name="wall",
        visible=True,
        collidable=True,
        tags=["wall"],
    ),
    "live": Sprite(
        pixels=[[LIVE_C]],
        name="live",
        visible=True,
        collidable=False,
        tags=["live"],
    ),
}


def mk(
    walls: list[tuple[int, int]],
    target: list[tuple[int, int]],
    need_gens: int,
    max_toggles: int,
    diff: int,
) -> Level:
    sl: list[Sprite] = []
    for wx, wy in walls:
        sl.append(sprites["wall"].clone().set_position(wx, wy))
    return Level(
        sprites=sl,
        grid_size=(CAM_W, CAM_H),
        data={
            "difficulty": diff,
            "target_cells": [list(p) for p in target],
            "need_generations": need_gens,
            "max_toggles": max_toggles,
        },
    )


def _block(ax: int, ay: int) -> list[tuple[int, int]]:
    return [(ax, ay), (ax + 1, ay), (ax, ay + 1), (ax + 1, ay + 1)]


def _pit_walls_around_block(ax: int, ay: int) -> list[tuple[int, int]]:
    """Walls on a 4×4 ring; interior is exactly the 2×2 at (ax, ay)..(ax+1, ay+1) (no goal overlay)."""
    out: list[tuple[int, int]] = []
    for x in range(ax - 1, ax + 3):
        for y in range(ay - 1, ay + 3):
            if not (ax <= x <= ax + 1 and ay <= y <= ay + 1):
                out.append((x, y))
    return out


# Stable 2×2 blocks; after each generation the pattern is unchanged if it matches the block.
levels = [
    # Level 1: walled pit is the only 2×2 non-wall region (same target as before).
    mk(_pit_walls_around_block(15, 15), _block(15, 15), 2, 60, 1),
    mk([(x, 14) for x in range(10, 22)], _block(18, 10), 1, 100, 2),
    mk([], _block(8, 8) + _block(20, 20), 3, 180, 3),
    mk([(16, y) for y in range(32) if 10 < y < 20], _block(22, 12), 2, 220, 4),
    mk([], _block(5, 5) + _block(25, 25), 4, 300, 5),
]


class Ll01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Ll01UI(0, 1, 0)
        super().__init__(
            "ll01",
            levels,
            Camera(0, 0, CAM_W, CAM_H, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 5, 6],
        )

    def on_set_level(self, level: Level) -> None:
        raw = self.current_level.get_data("target_cells") or []
        self._target = {tuple(int(t) for t in p) for p in raw}
        self._need = int(self.current_level.get_data("need_generations") or 1)
        self._tog_left = int(self.current_level.get_data("max_toggles") or 100)
        self._gen_count = 0
        self._sync_ui()

    def _alive(self) -> set[tuple[int, int]]:
        return {(s.x, s.y) for s in self.current_level.get_sprites_by_tag("live")}

    def _sync_ui(self) -> None:
        self._ui.update(self._gen_count, self._need, self._tog_left)

    def _neighbors(self, x: int, y: int) -> int:
        c = 0
        for dx, dy in ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)):
            if (x + dx, y + dy) in self._alive():
                c += 1
        return c

    def _step_conway(self) -> None:
        gw, gh = self.current_level.grid_size
        cur = self._alive()
        nxt: set[tuple[int, int]] = set()
        for y in range(gh):
            for x in range(gw):
                sp = self.current_level.get_sprite_at(x, y, ignore_collidable=True)
                if sp and "wall" in sp.tags:
                    continue
                n = self._neighbors(x, y)
                live = (x, y) in cur
                if live and n in (2, 3):
                    nxt.add((x, y))
                elif not live and n == 3:
                    nxt.add((x, y))
        for s in list(self.current_level.get_sprites_by_tag("live")):
            self.current_level.remove_sprite(s)
        for x, y in nxt:
            self.current_level.add_sprite(sprites["live"].clone().set_position(x, y))

    def step(self) -> None:
        aid = self.action.id

        if aid in (
            GameAction.ACTION1,
            GameAction.ACTION2,
            GameAction.ACTION3,
            GameAction.ACTION4,
        ):
            self.complete_action()
            return

        if aid == GameAction.ACTION5:
            self._step_conway()
            self._gen_count += 1
            self._sync_ui()
            if self._gen_count == self._need:
                if self._alive() == self._target:
                    self.next_level()
                else:
                    self.lose()
            elif self._gen_count > self._need:
                self.lose()
            self.complete_action()
            return

        if aid != GameAction.ACTION6:
            self.complete_action()
            return

        if self._tog_left <= 0:
            self.complete_action()
            return

        x = self.action.data.get("x", 0)
        y = self.action.data.get("y", 0)
        coords = self.camera.display_to_grid(x, y)
        if coords is None:
            self.complete_action()
            return
        gx, gy = coords
        gw, gh = self.current_level.grid_size
        if not (0 <= gx < gw and 0 <= gy < gh):
            self.complete_action()
            return

        sp = self.current_level.get_sprite_at(gx, gy, ignore_collidable=True)
        if sp and "wall" in sp.tags:
            self.complete_action()
            return

        hit = next(
            (s for s in self.current_level.get_sprites_by_tag("live") if s.x == gx and s.y == gy),
            None,
        )
        if hit:
            self.current_level.remove_sprite(hit)
        else:
            self.current_level.add_sprite(sprites["live"].clone().set_position(gx, gy))

        self._tog_left -= 1
        self._sync_ui()
        self.complete_action()
