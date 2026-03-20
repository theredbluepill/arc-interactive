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
    GameAction,
    Level,
    RenderableUserDisplay,
    Sprite,
)

# Must match `Camera(…, width, height, …)` for all tb01 levels
TB_GRID_W = 24
TB_GRID_H = 24

COLOR_BG = 10  # cyan / light-blue water
COLOR_ISLAND = 13
COLOR_GOAL_ISLAND = 14
COLOR_BRIDGE = 12
COLOR_PLAYER = 9
COLOR_PADDING = 4
COLOR_ROCK = 3  # shallow reef — cannot bridge or stand on


class Tb02UI(RenderableUserDisplay):
    def __init__(self) -> None:
        self._bridges: set[tuple[int, int]] = set()
        self._player_cell: tuple[int, int] = (0, 0)
        self._difficulty = 1

    def update(
        self,
        bridges: set[tuple[int, int]],
        player_x: int,
        player_y: int,
        difficulty: int = 1,
    ) -> None:
        self._bridges = bridges
        self._player_cell = (player_x, player_y)
        self._difficulty = max(1, min(5, difficulty))

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        # Level / difficulty ticks (1–5) — bottom-left in 64×64 frame space
        for i in range(5):
            frame[h - 2, 2 + i] = 9 if i < self._difficulty else 3
        # Align with Camera.render: uniform scale + letterbox into 64×64
        scale = min(64 // TB_GRID_W, 64 // TB_GRID_H)
        pad_x = (w - TB_GRID_W * scale) // 2
        pad_y = (h - TB_GRID_H * scale) // 2
        for bx, by in self._bridges:
            x0 = pad_x + bx * scale
            y0 = pad_y + by * scale
            for sy in range(scale):
                for sx in range(scale):
                    fy, fx = y0 + sy, x0 + sx
                    if 0 <= fy < h and 0 <= fx < w:
                        frame[fy, fx] = COLOR_BRIDGE
        # Bridges are drawn after sprites, so they hid the player; paint player on top
        px, py = self._player_cell
        x0 = pad_x + px * scale
        y0 = pad_y + py * scale
        for sy in range(scale):
            for sx in range(scale):
                fy, fx = y0 + sy, x0 + sx
                if 0 <= fy < h and 0 <= fx < w:
                    frame[fy, fx] = COLOR_PLAYER
        return frame


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


# --- Levels (24×24): multiple 3×3 maroon islands, green goal, gray reef “blocks” ---
#
# L1  Tutorial — start + goal only, straight bridge.
# L2  Three islands in one row + off-path reefs.
# L3  Diagonal hop (SW → center → NE) + scattered reefs.
# L4  Three east islands then long south leg to elevated goal + reefs.
# L5  Like L2 row + two extra maroon hubs and a larger reef field (same bridge line).
#
# Knobs: rock_coords (1×1 cells; cluster several for “blocks”), max_bridges,
# step_limit — kept generous so levels stay fair.


def make_level(
    island_coords,
    goal_island_coords,
    player_start,
    grid_size=24,
    *,
    difficulty: int = 1,
    max_bridges: int | None = None,
    step_limit: int | None = None,
    rock_coords: list[tuple[int, int]] | None = None,
):
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

    for rx, ry in rock_coords or []:
        sprite_list.append(
            Sprite(
                pixels=[[COLOR_ROCK]],
                name="reef",
                visible=True,
                collidable=False,
                layer=2,
                tags=["rock"],
            ).set_position(rx, ry)
        )

    sprite_list.append(sprites["player"].clone().set_position(*player_start))

    data = {
        "difficulty": difficulty,
        "island_coords": set(island_coords),
        "goal_island_coords": set(goal_island_coords),
        "rock_coords": set(rock_coords or ()),
        "max_bridges": max_bridges,
        "step_limit": step_limit,
    }
    return Level(
        sprites=sprite_list,
        grid_size=(grid_size, grid_size),
        data=data,
    )


def make_level_1():
    start_island = make_island_3x3(4, 12)
    goal_island = make_island_3x3(18, 12)
    return make_level(
        start_island, goal_island, (4, 12), 24, difficulty=1
    )


def make_level_2():
    # Three islands on y=12; reefs sit above/below the channel (not on it)
    row_y = 12
    start = make_island_3x3(4, row_y)
    mid = make_island_3x3(12, row_y)
    goal = make_island_3x3(20, row_y)
    reefs = [
        (8, 11),
        (8, 13),
        (16, 11),
        (16, 13),
        (10, 10),
        (14, 14),
    ]
    return make_level(
        start + mid,
        goal,
        (4, row_y),
        24,
        difficulty=2,
        rock_coords=reefs,
        max_bridges=28,
        step_limit=220,
    )


def make_level_3():
    start_island = make_island_3x3(4, 4)
    middle_island = make_island_3x3(12, 12)
    goal_island = make_island_3x3(20, 20)
    reefs = [
        (9, 9),
        (15, 15),
        (11, 14),
        (7, 7),
        (7, 8),
        (8, 7),
        (8, 8),
    ]
    return make_level(
        start_island + middle_island,
        goal_island,
        (4, 4),
        24,
        difficulty=3,
        rock_coords=reefs,
        max_bridges=40,
        step_limit=240,
    )


def make_level_4():
    # Waypoints along y=8, then goal far south-east
    a = make_island_3x3(4, 8)
    b = make_island_3x3(12, 8)
    c = make_island_3x3(20, 8)
    goal = make_island_3x3(20, 20)
    reefs = [
        (14, 7),
        (14, 9),
        (6, 10),
        (18, 10),
        (12, 14),
        (16, 16),
    ]
    return make_level(
        a + b + c,
        goal,
        (4, 8),
        24,
        difficulty=4,
        rock_coords=reefs,
        max_bridges=44,
        step_limit=260,
    )


def make_level_5():
    # Same hop pattern as L2 (three islands on y=12) plus extra maroon “hubs” and reefs
    row_y = 12
    start = make_island_3x3(4, row_y)
    mid = make_island_3x3(12, row_y)
    goal = make_island_3x3(20, row_y)
    extra = make_island_3x3(8, 6) + make_island_3x3(16, 18)
    reefs = [
        (8, 11),
        (8, 13),
        (16, 11),
        (16, 13),
        (10, 10),
        (14, 14),
        (6, 8),
        (7, 8),
        (18, 16),
        (19, 16),
        (12, 8),
        (12, 16),
    ]
    return make_level(
        start + mid + extra,
        goal,
        (4, row_y),
        24,
        difficulty=5,
        rock_coords=reefs,
        max_bridges=32,
        step_limit=240,
    )


levels = [
    make_level_1(),
    make_level_2(),
    make_level_3(),
    make_level_4(),
    make_level_5(),
]


class Tb02(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Tb02UI()
        super().__init__(
            "tb02",
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
        self._rock_coords: frozenset[tuple[int, int]] = frozenset(
            level.get_data("rock_coords") or ()
        )
        self._max_bridges: int | None = level.get_data("max_bridges")
        self._step_limit: int | None = level.get_data("step_limit")
        self._difficulty: int = level.get_data("difficulty") or 1
        self._steps_this_level = 0
        self._start_position = (self._player.x, self._player.y)
        self._bridges = set()
        self._last_dx = 1
        self._last_dy = 0
        self._lives = 3
        self._update_ui()

    def _is_rock(self, x: int, y: int) -> bool:
        return (x, y) in self._rock_coords

    def _is_land(self, x, y):
        if (x, y) in self._island_coords:
            return True
        if (x, y) in self._goal_island_coords:
            return True
        if (x, y) in self._bridges:
            return True
        return False

    def _is_open_water(self, x: int, y: int) -> bool:
        """Cyan sea only: in bounds, not island, not goal, not bridge, not reef."""
        gw, gh = self.current_level.grid_size
        if not (0 <= x < gw and 0 <= y < gh):
            return False
        if (x, y) in self._island_coords or (x, y) in self._goal_island_coords:
            return False
        if (x, y) in self._bridges:
            return False
        if self._is_rock(x, y):
            return False
        return True

    def _toggle_bridge_at(self, gx: int, gy: int) -> None:
        if (gx, gy) in self._bridges:
            self._bridges.discard((gx, gy))
            self._update_ui()
            return
        if not self._is_open_water(gx, gy):
            return
        if (
            self._max_bridges is not None
            and len(self._bridges) >= self._max_bridges
        ):
            return
        self._bridges.add((gx, gy))
        self._update_ui()

    def _after_action(self) -> None:
        self._steps_this_level += 1
        if (
            self._step_limit is not None
            and self._steps_this_level > self._step_limit
        ):
            self.lose()
        self.complete_action()

    def step(self) -> None:
        dx = dy = 0

        if self.action.id == GameAction.ACTION1:
            dy = -1
        elif self.action.id == GameAction.ACTION2:
            dy = 1
        elif self.action.id == GameAction.ACTION3:
            dx = -1
        elif self.action.id == GameAction.ACTION4:
            dx = 1
        elif self.action.id == GameAction.ACTION6:
            disp_x = self.action.data.get("x", 0)
            disp_y = self.action.data.get("y", 0)
            coords = self.camera.display_to_grid(disp_x, disp_y)
            if coords is not None:
                self._toggle_bridge_at(coords[0], coords[1])
            self._after_action()
            return

        new_x = self._player.x + dx
        new_y = self._player.y + dy

        if dx != 0 or dy != 0:
            self._last_dx = dx
            self._last_dy = dy

        grid_w, grid_h = self.current_level.grid_size
        if not (0 <= new_x < grid_w and 0 <= new_y < grid_h):
            self._after_action()
            return

        if self._is_rock(new_x, new_y):
            self._after_action()
            return

        if self._is_land(new_x, new_y):
            ox, oy = self._player.x, self._player.y
            if (ox, oy) in self._bridges:
                self._bridges.discard((ox, oy))
            self._player.set_position(new_x, new_y)
            self._update_ui()
            # Count before next_level() so on_set_level can reset for the new map
            self._steps_this_level += 1
            if (
                self._step_limit is not None
                and self._steps_this_level > self._step_limit
            ):
                self.lose()
            else:
                self._check_win()
            self.complete_action()
            return

        self._lives -= 1
        self._player.set_position(self._start_position[0], self._start_position[1])
        self._update_ui()
        if self._lives <= 0:
            self.lose()
        self._after_action()

    def _check_win(self):
        if (self._player.x, self._player.y) in self._goal_island_coords:
            self.next_level()

    def _update_ui(self) -> None:
        self._ui.update(
            self._bridges, self._player.x, self._player.y, self._difficulty
        )
