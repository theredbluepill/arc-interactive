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
    def __init__(self, revealed_count: int, mine_count: int) -> None:
        self._revealed = revealed_count
        self._mine_count = mine_count

    def update(self, revealed: int, mine_count: int) -> None:
        self._revealed = revealed
        self._mine_count = mine_count

    def render_interface(self, frame):
        return frame


class Ms01(ARCBaseGame):
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
        self._ui.update(0, len(self._minefield))

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
            self.lose()
            self.complete_action()
            return

        self._player.set_position(new_x, new_y)

        if (new_x, new_y) not in self._revealed:
            self._revealed.add((new_x, new_y))
            count = self._mine_count.get((new_x, new_y), 0)
            for s in self.current_level._sprites:
                if s.x == new_x and s.y == new_y and "tile" in s.tags:
                    s.color_remap(s.pixels[0][0], self._get_clue_color(count))
                    break
            self._ui.update(len(self._revealed), len(self._minefield))

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
