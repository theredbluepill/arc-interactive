"""Diagonal Lights Out: ACTION6 toggles a cell and its four diagonal neighbors only. ACTION1–4 no-op."""

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
ON_COLOR = 11
WALL_COLOR = 3
CAM_W = 16
CAM_H = 16


class Lo04UI(RenderableUserDisplay):
    CLICK_ANIM_FRAMES = 16

    def __init__(self, remaining: int) -> None:
        self._remaining = remaining
        self._click_pos: tuple[int, int] | None = None
        self._click_frames = 0

    def update(self, remaining: int) -> None:
        self._remaining = remaining

    def set_click(self, frame_x: int, frame_y: int) -> None:
        self._click_pos = (frame_x, frame_y)
        self._click_frames = Lo04UI.CLICK_ANIM_FRAMES

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
        for i in range(min(self._remaining, 15)):
            self._plot_px(frame, h, w, 1 + i * 2, 1, 8)

        if self._click_pos and self._click_frames > 0:
            cx, cy = self._click_pos
            phase = Lo04UI.CLICK_ANIM_FRAMES - self._click_frames
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
    "lit": Sprite(
        pixels=[[ON_COLOR]],
        name="lit",
        visible=True,
        collidable=False,
        tags=["lit"],
    ),
}


def mk(
    lights_on: list[tuple[int, int]],
    walls: list[tuple[int, int]],
    grid_size: tuple[int, int],
    difficulty: int,
) -> Level:
    sl: list[Sprite] = []
    for wx, wy in walls:
        sl.append(sprites["wall"].clone().set_position(wx, wy))
    return Level(
        sprites=sl,
        grid_size=grid_size,
        data={
            "difficulty": difficulty,
            "lights_on": [list(p) for p in lights_on],
        },
    )


levels = [
    mk([(1, 1), (0, 0), (2, 2)], [], (5, 5), 1),
    mk([(2, 2), (1, 1), (3, 3), (1, 3), (3, 1)], [], (5, 5), 2),
    mk([(0, 0), (2, 2), (4, 4)], [], (5, 5), 3),
    mk([(3, 3), (2, 2), (4, 4), (2, 4), (4, 2)], [], (6, 6), 4),
    mk([(1, 1), (2, 2), (3, 3), (4, 4), (0, 4), (4, 0)], [], (6, 6), 5),
    mk([(0, 2), (2, 0), (2, 4), (4, 2)], [], (6, 6), 6),
    mk([(1, 0), (0, 1), (4, 3), (3, 4), (5, 5)], [], (6, 6), 7),
]


class Lo04(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Lo04UI(0)
        super().__init__(
            "lo04",
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
        raw = self.current_level.get_data("lights_on") or []
        self._lit = {tuple(int(t) for t in p) for p in raw}
        self._walls = set()
        for s in self.current_level.get_sprites_by_tag("wall"):
            self._walls.add((s.x, s.y))
        self._refresh_lit_sprites()
        self._ui.update(len(self._lit))

    def _refresh_lit_sprites(self) -> None:
        for s in list(self.current_level.get_sprites_by_tag("lit")):
            self.current_level.remove_sprite(s)
        for x, y in self._lit:
            self.current_level.add_sprite(sprites["lit"].clone().set_position(x, y))
        self._ui.update(len(self._lit))

    def _toggle_cell(self, gx: int, gy: int) -> None:
        p = (gx, gy)
        if p in self._lit:
            self._lit.remove(p)
        else:
            self._lit.add(p)

    def step(self) -> None:
        if self.action.id.value in (1, 2, 3, 4):
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

        if (gx, gy) in self._walls:
            self.complete_action()
            return

        diag = (
            (gx, gy),
            (gx - 1, gy - 1),
            (gx + 1, gy - 1),
            (gx - 1, gy + 1),
            (gx + 1, gy + 1),
        )
        for tx, ty in diag:
            if not (0 <= tx < grid_w and 0 <= ty < grid_h):
                continue
            if (tx, ty) in self._walls:
                continue
            self._toggle_cell(tx, ty)

        self._refresh_lit_sprites()

        if len(self._lit) == 0:
            self.next_level()

        self.complete_action()
