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

sprites = {
    "player": Sprite(
        pixels=[[9]],
        name="player",
        visible=True,
        collidable=True,
        tags=["player"],
    ),
    "goal": Sprite(
        pixels=[[14]],
        name="goal",
        visible=True,
        collidable=False,
        tags=["goal"],
    ),
    "mine": Sprite(
        pixels=[[8]],
        name="mine",
        visible=False,
        collidable=False,
        tags=["mine"],
    ),
    "tile": Sprite(
        pixels=[[4]],
        name="tile",
        visible=True,
        collidable=False,
        tags=["tile"],
    ),
    "wall": Sprite(
        pixels=[[3]],
        name="wall",
        visible=True,
        collidable=True,
        tags=["wall"],
    ),
}


class Ms01UI(RenderableUserDisplay):
    """HUD + mine-hit burst in final 64×64 frame space (matches Camera letterbox math)."""

    CAMERA_W = 16
    CAMERA_H = 16

    def __init__(self, revealed_count: int, mine_count: int) -> None:
        self._revealed = revealed_count
        self._mine_count = mine_count
        self._difficulty = 1
        self._fail_active = False
        self._fail_k = 0
        self._fail_cx = 32
        self._fail_cy = 32

    def update(self, revealed: int, mine_count: int, difficulty: int = 1) -> None:
        self._revealed = revealed
        self._mine_count = mine_count
        self._difficulty = difficulty

    def clear_fail(self) -> None:
        self._fail_active = False
        self._fail_k = 0

    def trigger_fail(self, grid_x: int, grid_y: int) -> None:
        self._fail_cx, self._fail_cy = self._grid_to_frame_pixel(grid_x, grid_y)
        self._fail_active = True

    def set_fail_frame(self, k: int) -> None:
        self._fail_k = max(0, k)

    @classmethod
    def _grid_to_frame_pixel(cls, gx: int, gy: int) -> tuple[int, int]:
        cw, ch = cls.CAMERA_W, cls.CAMERA_H
        scale = min(64 // cw, 64 // ch)
        x_pad = (64 - cw * scale) // 2
        y_pad = (64 - ch * scale) // 2
        return gx * scale + scale // 2 + x_pad, gy * scale + scale // 2 + y_pad

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
                if max(abs(dx), abs(dy)) != r:
                    continue
                cls._plot_px(frame, h, w, cx + dx, cy + dy, color)

    @classmethod
    def _draw_plus(cls, frame, h: int, w: int, cx: int, cy: int, arm: int, color: int) -> None:
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
        # Top-left in letterbox padding: level / difficulty cue (64×64-style HUD strip)
        frame[1, 2] = 9
        level_colors = [10, 11, 12, 14, 15]
        frame[1, 3] = level_colors[(self._difficulty - 1) % len(level_colors)]
        # Bottom: exploration ticks (capped) — safe cells uncovered
        tick = min(w - 4, max(0, self._revealed))
        for i in range(tick):
            frame[h - 2, 2 + i] = 10

        if self._fail_active:
            ph = self._fail_k
            thick = 2 + min(3, ph // 2)
            for t in range(thick):
                for x in range(w):
                    self._plot_px(frame, h, w, x, t, 8)
                    self._plot_px(frame, h, w, x, h - 1 - t, 8)
                for y in range(h):
                    self._plot_px(frame, h, w, t, y, 8)
                    self._plot_px(frame, h, w, w - 1 - t, y, 8)
            for r in range(2, min(12, 3 + ph * 2), 2):
                c = 8 if (r // 2) % 2 == 1 else 11
                self._chebyshev_ring(frame, h, w, self._fail_cx, self._fail_cy, r, c)
            arm = min(3 + ph, 10)
            self._draw_plus(frame, h, w, self._fail_cx, self._fail_cy, arm, 8)
            self._plot_px(frame, h, w, self._fail_cx, self._fail_cy, 11)

        return frame


class Ms01(ARCBaseGame):
    DEATH_ANIM_STEPS = 8

    def __init__(self) -> None:
        self._ui = Ms01UI(0, 0)
        super().__init__(
            "ms01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )
        self._minefield = {}
        self._revealed = set()
        self._mine_count = {}
        self._death_ticks = 0

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._minefield = {}
        self._revealed = set()
        self._mine_count = {}
        mine_sprites = self.current_level.get_sprites_by_tag("mine")
        for m in mine_sprites:
            self._minefield[(m.x, m.y)] = True
        grid_w, grid_h = self.current_level.grid_size
        for y in range(grid_h):
            for x in range(grid_w):
                if (x, y) not in self._minefield:
                    count = self._count_adjacent_mines(x, y)
                    self._mine_count[(x, y)] = count
        self._death_ticks = 0
        self._ui.clear_fail()
        self._ui.update(0, len(self._minefield), level.get_data("difficulty"))

    def _count_adjacent_mines(self, x: int, y: int) -> int:
        count = 0
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                if (x + dx, y + dy) in self._minefield:
                    count += 1
        return count

    def _get_clue_color(self, count: int) -> int:
        if count == 0:
            return 1
        elif count == 1:
            return 8
        elif count == 2:
            return 11
        elif count == 3:
            return 14
        else:
            return 15

    def step(self) -> None:
        if self._death_ticks > 0:
            self._death_ticks -= 1
            self._ui.set_fail_frame(Ms01.DEATH_ANIM_STEPS - 1 - self._death_ticks)
            if self._death_ticks == 0:
                self.lose()
                self.complete_action()
            return

        dx = dy = 0
        if self.action.id.value == 1:
            dy = -1
        elif self.action.id.value == 2:
            dy = 1
        elif self.action.id.value == 3:
            dx = -1
        elif self.action.id.value == 4:
            dx = 1

        new_x = self._player.x + dx
        new_y = self._player.y + dy

        grid_w, grid_h = self.current_level.grid_size
        if not (0 <= new_x < grid_w and 0 <= new_y < grid_h):
            self.complete_action()
            return

        sprite = self.current_level.get_sprite_at(new_x, new_y, ignore_collidable=True)

        if sprite and "wall" in sprite.tags:
            self.complete_action()
            return

        if (new_x, new_y) in self._minefield:
            # Reveal the mine at the death location for clarity.
            for m in self.current_level.get_sprites_by_tag("mine"):
                if m.x == new_x and m.y == new_y:
                    m.set_visible(True)
                    break
            self._player.set_position(new_x, new_y)
            self._death_ticks = Ms01.DEATH_ANIM_STEPS - 1
            self._ui.trigger_fail(new_x, new_y)
            self._ui.set_fail_frame(0)
            return

        self._player.set_position(new_x, new_y)

        if (new_x, new_y) not in self._revealed:
            self._revealed.add((new_x, new_y))
            count = self._mine_count.get((new_x, new_y), 0)
            for s in self.current_level._sprites:
                if s.x == new_x and s.y == new_y and "tile" in s.tags:
                    s.color_remap(s.pixels[0][0], self._get_clue_color(count))
                    break
            self._ui.update(
                len(self._revealed),
                len(self._minefield),
                self.current_level.get_data("difficulty"),
            )

        if sprite and "goal" in sprite.tags:
            self.next_level()

        self.complete_action()


def make_ms_level(
    grid_size, player_pos, goal_pos, mine_coords, wall_coords, difficulty
):
    sprite_list = [
        sprites["player"].clone().set_position(*player_pos),
        sprites["goal"].clone().set_position(*goal_pos),
    ]
    for mc in mine_coords:
        sprite_list.append(sprites["mine"].clone().set_position(*mc))
    for wc in wall_coords:
        sprite_list.append(sprites["wall"].clone().set_position(*wc))
    for y in range(grid_size[1]):
        for x in range(grid_size[0]):
            is_mine = (x, y) in mine_coords
            is_player = (x, y) == player_pos
            is_goal = (x, y) == goal_pos
            is_wall = (x, y) in wall_coords
            # Always add a ground tile everywhere except walls.
            # This ensures mine cells don't show as black background/void.
            if not is_wall and not is_player and not is_goal:
                sprite_list.append(sprites["tile"].clone().set_position(x, y))
    return Level(
        sprites=sprite_list,
        grid_size=grid_size,
        data={"difficulty": difficulty},
    )


levels = [
    make_ms_level(
        (8, 8),
        (0, 0),
        (7, 7),
        [(3, 3), (3, 4), (4, 3), (4, 4), (5, 5)],
        [],
        1,
    ),
    make_ms_level(
        (10, 10),
        (0, 5),
        (9, 5),
        [(3, 3), (3, 4), (3, 5), (3, 6), (3, 7), (5, 2), (5, 3), (5, 7), (5, 8)],
        [],
        2,
    ),
    make_ms_level(
        (12, 12),
        (0, 0),
        (11, 11),
        [
            (2, 2),
            (3, 3),
            (4, 4),
            (5, 5),
            (6, 6),
            (7, 5),
            (8, 4),
            (9, 3),
            (5, 9),
            (6, 8),
            (7, 7),
            (8, 6),
        ],
        [],
        3,
    ),
    make_ms_level(
        (14, 14),
        (7, 0),
        (7, 13),
        [
            (3, 3),
            (3, 4),
            (3, 5),
            (3, 6),
            (5, 6),
            (5, 7),
            (5, 8),
            (7, 4),
            (7, 5),
            (7, 9),
            (7, 10),
            (9, 6),
            (9, 7),
            (9, 8),
            (11, 8),
            (11, 9),
            (11, 10),
        ],
        [],
        4,
    ),
    make_ms_level(
        (16, 16),
        (0, 0),
        (15, 15),
        [
            (2, 2),
            (2, 3),
            (3, 2),
            (4, 5),
            (5, 4),
            (5, 5),
            (6, 6),
            (7, 7),
            (8, 5),
            (9, 6),
            (9, 7),
            (10, 8),
            (11, 9),
            (11, 10),
            (12, 11),
            (12, 12),
            (13, 10),
            (14, 11),
            (6, 12),
            (8, 10),
        ],
        [],
        5,
    ),
]
