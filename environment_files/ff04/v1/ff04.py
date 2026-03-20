"""Gradient budget paint: grow paint from seed orthogonally; total Manhattan cost to seed may not exceed budget; match goal set."""

from __future__ import annotations

from arcengine import (
    ARCBaseGame,
    Camera,
    GameAction,
    Level,
    RenderableUserDisplay,
    Sprite,
)

BG, PAD = 5, 4
GW = GH = 8
CAM = 16
WALL_C = 3
PAINT_C = 11
HINT_C = 2


class Ff04UI(RenderableUserDisplay):
    CLICK_ANIM_FRAMES = 16

    def __init__(self, cost: int, budget: int) -> None:
        self._cost = cost
        self._budget = budget
        self._click_pos: tuple[int, int] | None = None
        self._click_frames = 0

    def update(self, cost: int, budget: int) -> None:
        self._cost = cost
        self._budget = budget

    def set_click(self, fx: int, fy: int) -> None:
        self._click_pos = (fx, fy)
        self._click_frames = Ff04UI.CLICK_ANIM_FRAMES

    @staticmethod
    def _plot_px(frame, h: int, w: int, px: int, py: int, color: int) -> None:
        if 0 <= px < w and 0 <= py < h:
            frame[py, px] = color

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        ok = self._cost <= self._budget
        self._plot_px(frame, h, w, 2, 2, 14 if ok else 8)
        if self._click_pos and self._click_frames > 0:
            cx, cy = self._click_pos
            for r in (1, 2):
                for dy in range(-r, r + 1):
                    for dx in range(-r, r + 1):
                        if abs(dx) + abs(dy) == r:
                            self._plot_px(frame, h, w, cx + dx, cy + dy, 12)
            self._click_frames -= 1
        else:
            self._click_pos = None
        return frame


sprites = {
    "wall": Sprite(
        pixels=[[WALL_C]],
        name="wall",
        visible=True,
        collidable=True,
        tags=["wall"],
    ),
    "hint": Sprite(
        pixels=[[HINT_C]],
        name="hint",
        visible=True,
        collidable=False,
        tags=["hint"],
    ),
    "paint": Sprite(
        pixels=[[PAINT_C]],
        name="paint",
        visible=True,
        collidable=False,
        tags=["paint"],
    ),
}


def _manh(a: tuple[int, int], b: tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def mk(
    seed: tuple[int, int],
    goal: list[tuple[int, int]],
    walls: list[tuple[int, int]],
    budget: int,
    diff: int,
) -> Level:
    sl: list[Sprite] = []
    for wx, wy in walls:
        sl.append(sprites["wall"].clone().set_position(wx, wy))
    for gx, gy in goal:
        sl.append(sprites["hint"].clone().set_position(gx, gy))
    return Level(
        sprites=sl,
        grid_size=(GW, GH),
        data={
            "difficulty": diff,
            "seed": [seed[0], seed[1]],
            "goal_cells": [list(p) for p in goal],
            "budget": budget,
        },
    )


levels = [
    mk((0, 0), [(0, 0), (1, 0), (0, 1)], [(2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7)], 5, 1),
    mk((3, 3), [(2, 3), (3, 3), (4, 3), (3, 2), (3, 4)], [], 12, 2),
    mk((1, 1), [(x, 1) for x in range(1, 6)] + [(1, y) for y in range(2, 5)], [(7, 7)], 18, 3),
    mk((0, 7), [(0, 7), (1, 7), (0, 6), (1, 6)], [(4, 0), (5, 0)], 14, 4),
    mk((4, 4), [(x, 4) for x in range(2, 6)] + [(4, y) for y in range(2, 6)], [], 22, 5),
    mk((2, 2), [(2, 2), (3, 2), (2, 3), (3, 3), (4, 4)], [], 16, 6),
    mk((0, 0), [(x, 0) for x in range(4)] + [(0, y) for y in range(1, 4)], [(5, 5), (6, 6)], 20, 7),
]


class Ff04(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Ff04UI(0, 1)
        super().__init__(
            "ff04",
            levels,
            Camera(0, 0, CAM, CAM, BG, PAD, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 6],
        )

    def _grid_to_frame_pixel(self, gx: int, gy: int) -> tuple[int, int]:
        cam = self.camera
        cw, ch = cam.width, cam.height
        scale = min(int(64 / cw), int(64 / ch))
        x_pad = int((64 - (cw * scale)) / 2)
        y_pad = int((64 - (ch * scale)) / 2)
        return gx * scale + scale // 2 + x_pad, gy * scale + scale // 2 + y_pad

    def on_set_level(self, level: Level) -> None:
        s = self.current_level.get_data("seed") or [0, 0]
        self._seed = (int(s[0]), int(s[1]))
        raw = self.current_level.get_data("goal_cells") or []
        self._goal = {tuple(int(t) for t in p) for p in raw}
        self._budget = int(self.current_level.get_data("budget") or 10)
        self._walls = set()
        for sp in self.current_level.get_sprites_by_tag("wall"):
            self._walls.add((sp.x, sp.y))
        self._painted: set[tuple[int, int]] = {self._seed}
        self._refresh_paint()
        self._sync_cost()

    def _total_cost(self) -> int:
        return sum(_manh(p, self._seed) for p in self._painted)

    def _sync_cost(self) -> None:
        self._ui.update(self._total_cost(), self._budget)

    def _refresh_paint(self) -> None:
        for s in list(self.current_level.get_sprites_by_tag("paint")):
            self.current_level.remove_sprite(s)
        for p in self._painted:
            self.current_level.add_sprite(sprites["paint"].clone().set_position(p[0], p[1]))

    def step(self) -> None:
        if self.action.id.value in (1, 2, 3, 4):
            self.complete_action()
            return

        if self.action.id != GameAction.ACTION6:
            self.complete_action()
            return

        px = int(self.action.data.get("x", 0))
        py = int(self.action.data.get("y", 0))
        hit = self.camera.display_to_grid(px, py)
        if hit is None:
            cx = max(0, min(63, px))
            cy = max(0, min(63, py))
            self._ui.set_click(cx, cy)
            self.complete_action()
            return

        gx, gy = int(hit[0]), int(hit[1])
        self._ui.set_click(*self._grid_to_frame_pixel(gx, gy))

        c = (gx, gy)
        if c in self._walls or not (0 <= gx < GW and 0 <= gy < GH):
            self.complete_action()
            return

        if c in self._painted:
            self.complete_action()
            return

        ok_nb = False
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nb = (gx + dx, gy + dy)
            if nb in self._painted:
                ok_nb = True
                break
        if not ok_nb:
            self.complete_action()
            return

        add_cost = _manh(c, self._seed)
        if self._total_cost() + add_cost > self._budget:
            self.complete_action()
            return

        self._painted.add(c)
        self._refresh_paint()
        self._sync_cost()
        if self._painted == self._goal:
            self.next_level()

        self.complete_action()
