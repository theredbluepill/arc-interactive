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

from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)

BACKGROUND_COLOR = 5
PADDING_COLOR = 4
FILL_COLOR = 11
WALL_COLOR = 3
LIVES_COLOR = 8
TIMER_COLOR = 11


class Ff01UI(RenderableUserDisplay):
    def __init__(self, lives: int, shapes_remaining: int, steps_remaining: int) -> None:
        self._lives = lives
        self._shapes_remaining = shapes_remaining
        self._steps_remaining = steps_remaining
        self._click_pos = None
        self._click_frames = 0

    def update(self, lives: int, shapes_remaining: int, steps_remaining: int) -> None:
        self._lives = lives
        self._shapes_remaining = shapes_remaining
        self._steps_remaining = steps_remaining

    def set_click(self, x: int, y: int) -> None:
        self._click_pos = (x, y)
        self._click_frames = 15

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape

        if self._click_pos and self._click_frames > 0:
            cx, cy = self._click_pos
            if 0 <= cx < w and 0 <= cy < h:
                frame[cy, cx] = 8
                for r in range(1, 4):
                    for dx, dy in [(0, -r), (0, r), (-r, 0), (r, 0)]:
                        px, py = cx + dx, cy + dy
                        if 0 <= px < w and 0 <= py < h:
                            frame[py, px] = 14
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        if abs(dx) + abs(dy) <= 1:
                            px, py = cx + dx, cy + dy
                            if 0 <= px < w and 0 <= py < h:
                                frame[py, px] = 8
            self._click_frames -= 1
        else:
            self._click_pos = None

        return frame


class Shape:
    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int | None = None,
        filled: bool = False,
    ):
        self.x = x
        self.y = y
        self.width = width
        self.height = height if height is not None else width
        self.filled = filled
        self.interior = [
            (x + i, y + j)
            for i in range(1, self.width - 1)
            for j in range(1, self.height - 1)
            if i < self.width - 1 and j < self.height - 1
        ]
        self.wall_positions = set()
        for i in range(self.width):
            self.wall_positions.add((x + i, y))
            self.wall_positions.add((x + i, y + self.height - 1))
        if self.height > 2:
            for j in range(1, self.height - 1):
                self.wall_positions.add((x, y + j))
                self.wall_positions.add((x + self.width - 1, y + j))

    @property
    def center(self) -> tuple:
        return (self.x + self.width // 2, self.y + self.height // 2)

    def contains(self, gx: int, gy: int) -> bool:
        return (gx, gy) in self.interior

    def get_sprites(self):
        wall = Sprite(
            pixels=[[WALL_COLOR]],
            name="wall",
            visible=True,
            collidable=True,
            tags=["wall"],
        )
        return [wall.clone().set_position(wx, wy) for wx, wy in self.wall_positions]


LEVEL_CONFIGS = [
    [Shape(26, 26, 12)],  # L1: 1 large square, dead center
    [Shape(8, 26, 10), Shape(46, 26, 10)],  # L2: 2 squares, horizontal spread
    [Shape(8, 8, 8), Shape(48, 48, 8)],  # L3: 2 squares, diagonal corners
    [Shape(3, 26, 8), Shape(28, 28, 8)],  # L4: one near left edge, one center
    [Shape(6, 6, 8), Shape(40, 15, 8), Shape(20, 45, 8)],  # L5: 3 squares, asymmetric
    [
        Shape(5, 25, 10),
        Shape(49, 25, 10),
        Shape(8, 8, 6),
        Shape(50, 50, 6),
    ],  # L6: 2 large + 2 small
    [
        Shape(5, 5, 8),
        Shape(51, 5, 8),
        Shape(5, 51, 8),
        Shape(51, 51, 8),
    ],  # L7: 4 corners
]


def get_level_shapes(level_num: int):
    idx = min(level_num - 1, len(LEVEL_CONFIGS) - 1)
    return [Shape(s.x, s.y, s.width, s.height) for s in LEVEL_CONFIGS[idx]]


class Ff01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Ff01UI(3, 0, 30)
        super().__init__(
            "ff01",
            levels,
            Camera(0, 0, 64, 64, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [6],
        )

    def on_set_level(self, level: Level) -> None:
        level_num = self._current_level_index + 1
        self._shapes = get_level_shapes(level_num)
        self._filled_shapes = set()
        self._steps_remaining = 25 + (level_num * 5)
        self._lives = 3

        for shape in self.current_level.get_sprites_by_tag("fill"):
            self.current_level.remove_sprite(shape)
        for shape in self.current_level.get_sprites_by_tag("wall"):
            self.current_level.remove_sprite(shape)

        for shape in self._shapes:
            for sprite in shape.get_sprites():
                self.current_level.add_sprite(sprite)

        self._update_ui()

    def _update_ui(self) -> None:
        remaining = len(self._shapes) - len(self._filled_shapes)
        self._ui.update(self._lives, remaining, self._steps_remaining)

    def _is_inside_any_shape(self, x: int, y: int):
        for i, shape in enumerate(self._shapes):
            if i not in self._filled_shapes and shape.contains(x, y):
                return i
        return -1

    def _fill_shape(self, shape_idx: int) -> None:
        shape = self._shapes[shape_idx]
        shape.filled = True
        self._filled_shapes.add(shape_idx)

        fill_sprite = Sprite(
            pixels=[[FILL_COLOR]],
            name=f"fill_{shape_idx}",
            visible=True,
            collidable=False,
            tags=["fill"],
        )
        for cx, cy in shape.interior:
            cell = fill_sprite.clone().set_position(cx, cy)
            self.current_level.add_sprite(cell)

    def step(self) -> None:
        if self.action.id.value == 6:
            x = self.action.data.get("x", 0)
            y = self.action.data.get("y", 0)

            self._ui.set_click(x, y)

            shape_idx = self._is_inside_any_shape(x, y)
            if shape_idx >= 0:
                self._fill_shape(shape_idx)

                if len(self._filled_shapes) == len(self._shapes):
                    self.next_level()
                    self.complete_action()
                    return

            self._steps_remaining -= 1
            self._update_ui()

            if self._steps_remaining <= 0:
                self._lives -= 1
                if self._lives <= 0:
                    self.lose()
                else:
                    self._reset_current_level()
                self._update_ui()

        self.complete_action()

    def _reset_current_level(self) -> None:
        self._shapes = get_level_shapes(self._current_level_index + 1)
        self._filled_shapes = set()
        self._steps_remaining = 25 + ((self._current_level_index + 1) * 5)

        for shape in self.current_level.get_sprites_by_tag("fill"):
            self.current_level.remove_sprite(shape)
        for shape in self.current_level.get_sprites_by_tag("wall"):
            self.current_level.remove_sprite(shape)

        for shape in self._shapes:
            for sprite in shape.get_sprites():
                self.current_level.add_sprite(sprite)


def make_level_sprites(level_num):
    shapes = get_level_shapes(level_num)
    sprites = []
    for shape in shapes:
        sprites.extend(shape.get_sprites())
    return sprites


levels = [
    Level(sprites=make_level_sprites(1), grid_size=(64, 64), data={}, name="Level 1"),
    Level(sprites=make_level_sprites(2), grid_size=(64, 64), data={}, name="Level 2"),
    Level(sprites=make_level_sprites(3), grid_size=(64, 64), data={}, name="Level 3"),
    Level(sprites=make_level_sprites(4), grid_size=(64, 64), data={}, name="Level 4"),
    Level(sprites=make_level_sprites(5), grid_size=(64, 64), data={}, name="Level 5"),
    Level(sprites=make_level_sprites(6), grid_size=(64, 64), data={}, name="Level 6"),
    Level(sprites=make_level_sprites(7), grid_size=(64, 64), data={}, name="Level 7"),
]
