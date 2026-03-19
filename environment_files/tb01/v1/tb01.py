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
# THE SOFTWARE IS PROVIDED " AS" WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
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


class Tb01UI(RenderableUserDisplay):
    def __init__(self) -> None:
        self._bridges = set()

    def update(self, bridges: set) -> None:
        self._bridges = bridges

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        scale = h / 24  # 24x24 grid in hxh frame
        cell_size = int(np.ceil(scale))  # Use ceil to ensure continuous coverage
        for bx, by in self._bridges:
            px, py = int(bx * scale), int(by * scale)
            for sy in range(cell_size):
                for sx in range(cell_size):
                    fy, fx = py + sy, px + sx
                    if 0 <= fy < h and 0 <= fx < w:
                        frame[fy, fx] = 12
        return frame


COLOR_BG = 10
COLOR_ISLAND = 13
COLOR_GOAL_ISLAND = 14
COLOR_BRIDGE = 12
COLOR_PLAYER = 9
COLOR_PADDING = 4


sprites = {
    "player": Sprite(
        pixels=[[9]],
        name="player",
        visible=True,
        collidable=True,
        layer=10,
        tags=["player"],
    ),
}


def make_island_3x3(center_x, center_y):
    return [(center_x + dx, center_y + dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1]]


def make_level(island_coords, goal_island_coords, player_start, grid_size=24):
    sprite_list = []
    for cx, cy in island_coords:
        sprite_list.append(
            Sprite(
                pixels=[[COLOR_ISLAND]],
                name="island",
                visible=True,
                collidable=False,
                layer=1,
                tags=["island"],
            ).set_position(cx, cy)
        )

    for cx, cy in goal_island_coords:
        sprite_list.append(
            Sprite(
                pixels=[[COLOR_GOAL_ISLAND]],
                name="goal_island",
                visible=True,
                collidable=False,
                layer=1,
                tags=["goal_island"],
            ).set_position(cx, cy)
        )

    sprite_list.append(sprites["player"].clone().set_position(*player_start))

    return Level(
        sprites=sprite_list,
        grid_size=(grid_size, grid_size),
        data={
            "island_coords": set(island_coords),
            "goal_island_coords": set(goal_island_coords),
        },
    )


def make_level_1():
    start_island = make_island_3x3(4, 12)
    goal_island = make_island_3x3(18, 12)
    return make_level(start_island, goal_island, (4, 12), 24)


def make_level_2():
    start_island = make_island_3x3(4, 4)
    middle_island = make_island_3x3(12, 12)
    goal_island = make_island_3x3(20, 20)
    return make_level(start_island + middle_island, goal_island, (4, 4), 24)


def make_level_3():
    start_island = make_island_3x3(4, 4)
    island2 = make_island_3x3(12, 4)
    island3 = make_island_3x3(12, 20)
    goal_island = make_island_3x3(20, 20)
    return make_level(start_island + island2 + island3, goal_island, (4, 4), 24)


def make_level_4():
    start_island = make_island_3x3(4, 12)
    island2 = make_island_3x3(10, 4)
    island3 = make_island_3x3(10, 20)
    island4 = make_island_3x3(18, 12)
    goal_island = make_island_3x3(22, 4)
    return make_level(
        start_island + island2 + island3 + island4, goal_island, (4, 12), 24
    )


def make_level_5():
    start_island = make_island_3x3(4, 12)
    island2 = make_island_3x3(10, 4)
    island3 = make_island_3x3(10, 20)
    island4 = make_island_3x3(16, 4)
    island5 = make_island_3x3(16, 20)
    goal_island = make_island_3x3(22, 12)
    return make_level(
        start_island + island2 + island3 + island4 + island5, goal_island, (4, 12), 24
    )


levels = [
    make_level_1(),
    make_level_2(),
    make_level_3(),
    make_level_4(),
    make_level_5(),
]


class Tb01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Tb01UI()
        super().__init__(
            "tb01",
            levels,
            Camera(0, 0, 24, 24, COLOR_BG, COLOR_PADDING, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 6],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._island_coords = level.get_data("island_coords")
        self._goal_island_coords = level.get_data("goal_island_coords")
        self._start_position = (self._player.x, self._player.y)
        self._bridges = set()
        self._last_dx = 1
        self._last_dy = 0
        self._lives = 3
        self._update_ui()

    def _is_land(self, x, y):
        if (x, y) in self._island_coords:
            return True
        if (x, y) in self._goal_island_coords:
            return True
        if (x, y) in self._bridges:
            return True
        return False

    def step(self) -> None:
        dx = dy = 0

        if self.action.id.value == 1:
            dy = -1
        elif self.action.id.value == 2:
            dy = 1
        elif self.action.id.value == 3:
            dx = -1
        elif self.action.id.value == 4:
            dx = 1
        elif self.action.id.value == 6:
            x = self.action.data.get("x", self._player.x + self._last_dx)
            y = self.action.data.get("y", self._player.y + self._last_dy)
            if not self._is_land(x, y) and 0 <= x < 24 and 0 <= y < 24:
                self._bridges.add((x, y))
                self._update_ui()
            self.complete_action()
            return

        new_x = self._player.x + dx
        new_y = self._player.y + dy

        if dx != 0 or dy != 0:
            self._last_dx = dx
            self._last_dy = dy

        grid_w, grid_h = self.current_level.grid_size
        if not (0 <= new_x < grid_w and 0 <= new_y < grid_h):
            self.complete_action()
            return

        if self._is_land(new_x, new_y):
            self._player.set_position(new_x, new_y)
            self._check_win()
        else:
            self._lives -= 1
            self._player.set_position(self._start_position[0], self._start_position[1])
            if self._lives <= 0:
                self.lose()

        self.complete_action()

    def _check_win(self):
        if (self._player.x, self._player.y) in self._goal_island_coords:
            self.next_level()

    def _update_ui(self):
        self._ui.update(self._bridges)
