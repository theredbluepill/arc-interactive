"""Grid paint: ACTION6 clicks toggle yellow marks on cells; match the dim hint pattern. ACTION1–4 are no-ops."""

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
PAINT_COLOR = 11
HINT_COLOR = 2
WALL_COLOR = 3
CAM_W = 16
CAM_H = 16


class Gp01UI(RenderableUserDisplay):
    CLICK_ANIM_FRAMES = 16

    def __init__(self, matched: int, total: int) -> None:
        self._matched = matched
        self._total = total
        self._click_pos: tuple[int, int] | None = None
        self._click_frames = 0

    def update(self, matched: int, total: int) -> None:
        self._matched = matched
        self._total = total

    def set_click(self, frame_x: int, frame_y: int) -> None:
        self._click_pos = (frame_x, frame_y)
        self._click_frames = Gp01UI.CLICK_ANIM_FRAMES

    @staticmethod
    def _plot_px(frame, h: int, w: int, px: int, py: int, color: int) -> None:
        if 0 <= px < w and 0 <= py < h:
            frame[py, px] = color

    @classmethod
    def _chebyshev_ring(
        cls, frame, h: int, w: int, cx: int, cy: int, r: int, color: int
    ) -> None:
        if r <= 0:
            return
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if max(abs(dx), abs(dy)) == r:
                    cls._plot_px(frame, h, w, cx + dx, cy + dy, color)

    @classmethod
    def _draw_plus(
        cls, frame, h: int, w: int, cx: int, cy: int, arm: int, color: int
    ) -> None:
        cls._plot_px(frame, h, w, cx, cy, color)
        for a in range(1, arm + 1):
            cls._plot_px(frame, h, w, cx - a, cy, color)
            cls._plot_px(frame, h, w, cx + a, cy, color)
            cls._plot_px(frame, h, w, cx, cy - a, color)
            cls._plot_px(frame, h, w, cx, cy + a, color)

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for i in range(min(self._total, 12)):
            c = 14 if i < self._matched else 8
            self._plot_px(frame, h, w, 1 + i * 2, 1, c)

        if self._click_pos and self._click_frames > 0:
            cx, cy = self._click_pos
            phase = Gp01UI.CLICK_ANIM_FRAMES - self._click_frames
            if phase < 6:
                ring_r = phase + 1 if phase < 3 else 6 - phase
                if ring_r > 0:
                    col = 11 if ring_r >= 2 else 10
                    self._chebyshev_ring(frame, h, w, cx, cy, ring_r, col)
            self._draw_plus(frame, h, w, cx, cy, 2, 12)
            self._click_frames -= 1
        else:
            self._click_pos = None

        return frame


sprites = {
    "wall": Sprite(
        pixels=[[WALL_COLOR]],
        name="wall",
        visible=True,
        collidable=True,
        tags=["wall"],
    ),
    "hint": Sprite(
        pixels=[[HINT_COLOR]],
        name="hint",
        visible=True,
        collidable=False,
        tags=["hint"],
    ),
    "paint": Sprite(
        pixels=[[PAINT_COLOR]],
        name="paint",
        visible=True,
        collidable=False,
        tags=["paint"],
    ),
}


def mk(
    goal: list[tuple[int, int]],
    walls: list[tuple[int, int]],
    grid_size: tuple[int, int],
    difficulty: int,
) -> Level:
    sl: list[Sprite] = []
    for wx, wy in walls:
        sl.append(sprites["wall"].clone().set_position(wx, wy))
    for gx, gy in goal:
        sl.append(sprites["hint"].clone().set_position(gx, gy))
    return Level(
        sprites=sl,
        grid_size=grid_size,
        data={
            "difficulty": difficulty,
            "goal_cells": [list(p) for p in goal],
        },
    )


levels = [
    mk([(2, 2), (3, 2), (2, 3), (3, 3)], [], (8, 8), 1),
    mk([(1, 1), (2, 1), (3, 1)], [(2, 2)], (8, 8), 2),
    mk([(0, 0), (7, 0), (0, 7), (7, 7)], [], (8, 8), 3),
    mk([(x, 4) for x in range(8)], [(3, 3), (5, 5)], (8, 8), 4),
    mk([(3, y) for y in range(8)], [(4, 2), (4, 5)], (8, 8), 5),
]


class Gp01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Gp01UI(0, 1)
        super().__init__(
            "gp01",
            levels,
            Camera(0, 0, CAM_W, CAM_H, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 6],
        )

    def _grid_to_frame_pixel(self, gx: int, gy: int) -> tuple[int, int]:
        cam = self.camera
        cw, ch = cam.width, cam.height
        scale_x = int(64 / cw)
        scale_y = int(64 / ch)
        scale = min(scale_x, scale_y)
        x_pad = int((64 - (cw * scale)) / 2)
        y_pad = int((64 - (ch * scale)) / 2)
        px = gx * scale + scale // 2 + x_pad
        py = gy * scale + scale // 2 + y_pad
        return px, py

    def on_set_level(self, level: Level) -> None:
        raw = self.current_level.get_data("goal_cells") or []
        self._goal = {tuple(int(t) for t in p) for p in raw}
        self._sync_ui()

    def _painted(self) -> set[tuple[int, int]]:
        out: set[tuple[int, int]] = set()
        for sp in self.current_level.get_sprites_by_tag("paint"):
            out.add((sp.x, sp.y))
        return out

    def _sync_ui(self) -> None:
        painted = self._painted()
        matched = len(self._goal & painted)
        total = len(self._goal)
        self._ui.update(matched, max(1, total))

    def step(self) -> None:
        aid = self.action.id.value
        if aid in (1, 2, 3, 4):
            self.complete_action()
            return

        if self.action.id != GameAction.ACTION6:
            self.complete_action()
            return

        x = self.action.data.get("x", 0)
        y = self.action.data.get("y", 0)
        coords = self.camera.display_to_grid(x, y)
        if coords is None:
            cx = max(0, min(63, int(x)))
            cy = max(0, min(63, int(y)))
            self._ui.set_click(cx, cy)
            self.complete_action()
            return

        gx, gy = coords
        self._ui.set_click(*self._grid_to_frame_pixel(gx, gy))

        grid_w, grid_h = self.current_level.grid_size
        if not (0 <= gx < grid_w and 0 <= gy < grid_h):
            self.complete_action()
            return

        sp = self.current_level.get_sprite_at(gx, gy, ignore_collidable=True)
        if sp and "wall" in sp.tags:
            self.complete_action()
            return

        existing = self.current_level.get_sprites_by_tag("paint")
        hit = next((p for p in existing if p.x == gx and p.y == gy), None)
        if hit:
            self.current_level.remove_sprite(hit)
        else:
            self.current_level.add_sprite(
                sprites["paint"].clone().set_position(gx, gy),
            )

        self._sync_ui()
        if self._painted() == self._goal:
            self.next_level()

        self.complete_action()
