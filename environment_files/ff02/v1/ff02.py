# MIT License
#
# Copyright (c) 2026 ARC Prize Foundation
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import annotations

from collections import deque

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
FILL_COLOR = 11
HINT_COLOR = 2
WALL_COLOR = 3
LIVES_COLOR = 8
HUD_DIM = 3
HUD_ACCENT = 11

GRID_W = 64
GRID_H = 64

# Frames to hold after last fill before advancing (readable in GIFs / terminal).
WIN_HOLD_FRAMES = 14


def _flood_region(
    seed: tuple[int, int],
    walls: set[tuple[int, int]],
    gw: int,
    gh: int,
) -> list[tuple[int, int]]:
    sx, sy = seed
    if not (0 <= sx < gw and 0 <= sy < gh) or seed in walls:
        return []
    q = deque([seed])
    seen = {seed}
    out: list[tuple[int, int]] = []
    while q:
        x, y = q.popleft()
        out.append((x, y))
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nx, ny = x + dx, y + dy
            if not (0 <= nx < gw and 0 <= ny < gh):
                continue
            if (nx, ny) in walls or (nx, ny) in seen:
                continue
            seen.add((nx, ny))
            q.append((nx, ny))
    return out


def _rect_perimeter(ox: int, oy: int, w: int, h: int) -> set[tuple[int, int]]:
    walls: set[tuple[int, int]] = set()
    for i in range(w):
        walls.add((ox + i, oy))
        walls.add((ox + i, oy + h - 1))
    for j in range(1, h - 1):
        walls.add((ox, oy + j))
        walls.add((ox + w - 1, oy + j))
    return walls


class Enclosure:
    """Closed wall loop + flood-fillable interior (not necessarily rectangular)."""

    __slots__ = ("wall_positions", "interior", "_interior_set")

    def __init__(
        self,
        wall_positions: set[tuple[int, int]],
        interior: list[tuple[int, int]],
    ) -> None:
        self.wall_positions = wall_positions
        self.interior = interior
        self._interior_set = set(interior)

    @property
    def center(self) -> tuple[int, int]:
        if not self.interior:
            return (0, 0)
        xs = [p[0] for p in self.interior]
        ys = [p[1] for p in self.interior]
        return (sum(xs) // len(xs), sum(ys) // len(ys))

    def contains(self, gx: int, gy: int) -> bool:
        return (gx, gy) in self._interior_set

    def get_sprites(self) -> list[Sprite]:
        wall = Sprite(
            pixels=[[WALL_COLOR]],
            name="wall",
            visible=True,
            collidable=True,
            tags=["wall"],
        )
        return [wall.clone().set_position(wx, wy) for wx, wy in self.wall_positions]


def make_rect(ox: int, oy: int, w: int, h: int) -> Enclosure:
    walls = _rect_perimeter(ox, oy, w, h)
    seed = (ox + 1, oy + 1)
    interior = _flood_region(seed, walls, GRID_W, GRID_H)
    return Enclosure(walls, interior)


def make_donut(
    ox: int,
    oy: int,
    ow: int,
    oh: int,
    hox: int,
    hoy: int,
    hw: int,
    hh: int,
) -> Enclosure:
    """Hollow rectangle with a rectangular hole (wall on both perimeters)."""
    walls = _rect_perimeter(ox, oy, ow, oh)
    ix0, iy0 = ox + hox, oy + hoy
    walls |= _rect_perimeter(ix0, iy0, hw, hh)
    seed = (ox + 1, oy + 1)
    if (ix0 <= seed[0] < ix0 + hw) and (iy0 <= seed[1] < iy0 + hh):
        seed = (ox + ow // 2, oy + 1)
    interior = _flood_region(seed, walls, GRID_W, GRID_H)
    return Enclosure(walls, interior)


def make_l_room(ox: int, oy: int, w: int = 14, h: int = 12) -> Enclosure:
    """Single connected L-shaped cavity (horizontal bar + vertical leg)."""
    walls = _rect_perimeter(ox, oy, w, h)
    for x in range(ox + 5, ox + w - 1):
        walls.add((x, oy + 4))
    for y in range(oy + 5, oy + h - 1):
        walls.add((ox + w - 2, y))
    seed = (ox + 2, oy + 2)
    interior = _flood_region(seed, walls, GRID_W, GRID_H)
    return Enclosure(walls, interior)


def make_c_room(ox: int, oy: int, w: int = 15, h: int = 11) -> Enclosure:
    """C-shaped / three-sided bay: one opening on the long side."""
    walls = _rect_perimeter(ox, oy, w, h)
    for y in range(oy + 2, oy + h - 2):
        walls.add((ox + w - 2, y))
    for x in range(ox + 3, ox + w - 2):
        walls.add((x, oy + h // 2))
    seed = (ox + 2, oy + 2)
    interior = _flood_region(seed, walls, GRID_W, GRID_H)
    return Enclosure(walls, interior)


# Five levels: ramp shape count and mix topologies (rect / donut / L / C).
LEVEL_CONFIGS: list[list[Enclosure]] = [
    [make_donut(18, 18, 24, 24, 8, 8, 8, 8)],
    [make_rect(5, 22, 11, 11), make_donut(36, 18, 22, 22, 7, 7, 8, 8)],
    # L3: ring + C-bay (distinct from L2’s rect + ring).
    [make_donut(10, 10, 22, 22, 7, 7, 8, 8), make_c_room(38, 32, 14, 10)],
    [
        make_rect(4, 4, 9, 9),
        make_donut(34, 6, 20, 20, 6, 6, 8, 8),
        make_c_room(6, 38),
    ],
    [
        make_donut(4, 4, 18, 18, 5, 5, 6, 6),
        make_donut(42, 42, 18, 18, 5, 5, 6, 6),
        make_rect(22, 22, 18, 18),
    ],
]


def get_level_shapes(level_num: int) -> list[Enclosure]:
    idx = min(level_num - 1, len(LEVEL_CONFIGS) - 1)
    return LEVEL_CONFIGS[idx]


class Ff02UI(RenderableUserDisplay):
    CLICK_ANIM_FRAMES = 20

    def __init__(self, lives: int, shapes_remaining: int, steps_remaining: int) -> None:
        self._lives = lives
        self._shapes_remaining = shapes_remaining
        self._steps_remaining = steps_remaining
        self._click_pos: tuple[int, int] | None = None
        self._click_frames = 0

    def update(self, lives: int, shapes_remaining: int, steps_remaining: int) -> None:
        self._lives = lives
        self._shapes_remaining = shapes_remaining
        self._steps_remaining = steps_remaining

    def set_click(self, frame_x: int, frame_y: int) -> None:
        self._click_pos = (frame_x, frame_y)
        self._click_frames = Ff02UI.CLICK_ANIM_FRAMES

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

        # --- Compact HUD (top-left): lives + shapes + steps (may overlap row 0 playfield) ---
        for i in range(3):
            c = LIVES_COLOR if i < self._lives else HUD_DIM
            bx, by = 1 + i * 3, 1
            for dy in range(2):
                for dx in range(2):
                    self._plot_px(frame, h, w, bx + dx, by + dy, c)
        for i in range(min(self._shapes_remaining, 5)):
            self._plot_px(frame, h, w, 12 + i * 2, 1, HUD_ACCENT)
        step_vis = min(self._steps_remaining, 7)
        for i in range(step_vis):
            self._plot_px(frame, h, w, 24 + i, 2, 10)

        if self._click_pos and self._click_frames > 0:
            cx, cy = self._click_pos
            phase = Ff02UI.CLICK_ANIM_FRAMES - self._click_frames
            if phase < 8:
                ring_r = phase + 1 if phase < 4 else 8 - phase
                if ring_r > 0:
                    ring_col = 0 if ring_r >= 4 else (11 if ring_r == 3 else 12)
                    self._chebyshev_ring(frame, h, w, cx, cy, ring_r, ring_col)
            arm = 2 if phase < 14 else 1
            plus_col = 0 if phase < 2 else 12
            self._draw_plus(frame, h, w, cx, cy, arm, plus_col)
            self._click_frames -= 1
        else:
            self._click_pos = None

        return frame


class Ff02(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Ff02UI(3, 0, 30)
        self._win_hold = 0
        super().__init__(
            "ff02",
            levels,
            Camera(0, 0, GRID_W, GRID_H, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
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

    def _hint_cells(self, shapes: list[Enclosure]) -> set[tuple[int, int]]:
        hints: set[tuple[int, int]] = set()
        for enc in shapes:
            interior = enc.interior
            if not interior:
                continue
            step = max(1, len(interior) // 5)
            for i in range(0, len(interior), step):
                hints.add(interior[i])
        return hints

    def on_set_level(self, level: Level) -> None:
        self._win_hold = 0
        level_num = self._current_level_index + 1
        self._shapes = get_level_shapes(level_num)
        self._erased_shapes: set[int] = set()
        self._hints = self._hint_cells(self._shapes)
        n = len(self._shapes)
        self._steps_remaining = max(10, 8 + level_num * 2 + n * 6)
        self._lives = 3

        for shape in self.current_level.get_sprites_by_tag("fill"):
            self.current_level.remove_sprite(shape)
        for shape in self.current_level.get_sprites_by_tag("wall"):
            self.current_level.remove_sprite(shape)
        for shape in self.current_level.get_sprites_by_tag("hint"):
            self.current_level.remove_sprite(shape)

        for enc in self._shapes:
            for sprite in enc.get_sprites():
                self.current_level.add_sprite(sprite)

        hint_sprite = Sprite(
            pixels=[[HINT_COLOR]],
            name="hint",
            visible=True,
            collidable=False,
            tags=["hint"],
        )
        for hx, hy in self._hints:
            self.current_level.add_sprite(hint_sprite.clone().set_position(hx, hy))

        fill_sprite = Sprite(
            pixels=[[FILL_COLOR]],
            name="fill_start",
            visible=True,
            collidable=False,
            tags=["fill"],
        )
        for si, enc in enumerate(self._shapes):
            for cx, cy in enc.interior:
                self.current_level.add_sprite(
                    fill_sprite.clone().set_position(cx, cy),
                )

        self._update_ui()

    def _update_ui(self) -> None:
        remaining = len(self._shapes) - len(self._erased_shapes)
        self._ui.update(self._lives, remaining, self._steps_remaining)

    def _is_inside_any_shape(self, x: int, y: int) -> int:
        for i, shape in enumerate(self._shapes):
            if i not in self._erased_shapes and shape.contains(x, y):
                return i
        return -1

    def _erase_shape(self, shape_idx: int) -> None:
        shape = self._shapes[shape_idx]
        inside = set(shape.interior)
        to_remove: list[Sprite] = []
        for sp in list(self.current_level._sprites):
            if sp and "fill" in sp.tags and (sp.x, sp.y) in inside:
                to_remove.append(sp)
        for sp in to_remove:
            self.current_level.remove_sprite(sp)

    def _hints_clear(self) -> bool:
        for hx, hy in self._hints:
            sp = self.current_level.get_sprite_at(hx, hy, ignore_collidable=True)
            if sp and "fill" in sp.tags:
                return False
        return True

    def step(self) -> None:
        if self._win_hold > 0:
            self._win_hold -= 1
            self._update_ui()
            if self._win_hold == 0:
                self.next_level()
            self.complete_action()
            return

        aid = self.action.id.value
        if aid in (1, 2, 3, 4):
            self.complete_action()
            return

        if self.action.id == GameAction.ACTION6:
            x = self.action.data.get("x", 0)
            y = self.action.data.get("y", 0)
            coords = self.camera.display_to_grid(x, y)
            if coords is None:
                cx = max(0, min(63, int(x)))
                cy = max(0, min(63, int(y)))
                self._ui.set_click(cx, cy)
                self._steps_remaining -= 1
                self._update_ui()
                if self._steps_remaining <= 0:
                    self._lose_or_reset()
                self.complete_action()
                return

            gx, gy = coords
            self._ui.set_click(*self._grid_to_frame_pixel(gx, gy))

            shape_idx = self._is_inside_any_shape(gx, gy)
            if shape_idx >= 0:
                self._erased_shapes.add(shape_idx)
                self._erase_shape(shape_idx)

                if len(self._erased_shapes) == len(self._shapes) and self._hints_clear():
                    self._win_hold = WIN_HOLD_FRAMES
                    self._update_ui()
                    self.complete_action()
                    return

            self._steps_remaining -= 1
            self._update_ui()

            if self._steps_remaining <= 0:
                self._lose_or_reset()

        self.complete_action()

    def _lose_or_reset(self) -> None:
        self._lives -= 1
        if self._lives <= 0:
            self.lose()
        else:
            self._reset_current_level()
        self._update_ui()

    def _reset_current_level(self) -> None:
        self._win_hold = 0
        self._shapes = get_level_shapes(self._current_level_index + 1)
        self._erased_shapes = set()
        self._hints = self._hint_cells(self._shapes)
        n = len(self._shapes)
        ln = self._current_level_index + 1
        self._steps_remaining = max(10, 8 + ln * 2 + n * 6)

        for shape in self.current_level.get_sprites_by_tag("fill"):
            self.current_level.remove_sprite(shape)
        for shape in self.current_level.get_sprites_by_tag("wall"):
            self.current_level.remove_sprite(shape)
        for shape in self.current_level.get_sprites_by_tag("hint"):
            self.current_level.remove_sprite(shape)

        for enc in self._shapes:
            for sprite in enc.get_sprites():
                self.current_level.add_sprite(sprite)

        hint_sprite = Sprite(
            pixels=[[HINT_COLOR]],
            name="hint",
            visible=True,
            collidable=False,
            tags=["hint"],
        )
        for hx, hy in self._hints:
            self.current_level.add_sprite(hint_sprite.clone().set_position(hx, hy))

        fill_sprite = Sprite(
            pixels=[[FILL_COLOR]],
            name="fill_start",
            visible=True,
            collidable=False,
            tags=["fill"],
        )
        for enc in self._shapes:
            for cx, cy in enc.interior:
                self.current_level.add_sprite(
                    fill_sprite.clone().set_position(cx, cy),
                )


def make_level_sprites(level_num: int) -> list[Sprite]:
    sprites: list[Sprite] = []
    for enc in get_level_shapes(level_num):
        sprites.extend(enc.get_sprites())
    return sprites


levels = [
    Level(sprites=make_level_sprites(1), grid_size=(GRID_W, GRID_H), data={}, name="Level 1"),
    Level(sprites=make_level_sprites(2), grid_size=(GRID_W, GRID_H), data={}, name="Level 2"),
    Level(sprites=make_level_sprites(3), grid_size=(GRID_W, GRID_H), data={}, name="Level 3"),
    Level(sprites=make_level_sprites(4), grid_size=(GRID_W, GRID_H), data={}, name="Level 4"),
    Level(sprites=make_level_sprites(5), grid_size=(GRID_W, GRID_H), data={}, name="Level 5"),
]
