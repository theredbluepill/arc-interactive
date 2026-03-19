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

import numpy as np
from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)

BACKGROUND_COLOR = 5
PADDING_COLOR = 4

GRID_WIDTH = 10
GRID_HEIGHT = 16
FLOOR_Y = 14

sprites = {
    "player": Sprite(
        pixels=[
            [9, 9],
            [9, 9],
        ],
        name="player",
        visible=True,
        collidable=True,
        tags=["player"],
    ),
    "block": Sprite(
        pixels=[
            [12, 12],
            [12, 12],
        ],
        name="block",
        visible=True,
        collidable=True,
        tags=["block"],
    ),
    "floor": Sprite(
        pixels=[
            [3, 3, 3, 3, 3, 3, 3, 3, 3, 3],
        ],
        name="floor",
        visible=True,
        collidable=True,
        tags=["floor"],
    ),
    "target_line": Sprite(
        pixels=[
            [11, 0, 11, 0, 11, 0, 11, 0, 11, 0],
        ],
        name="target_line",
        visible=True,
        collidable=False,
        tags=["target_line"],
    ),
}


class Gr01UI(RenderableUserDisplay):
    def __init__(self, blocks_remaining: int, target_height: int) -> None:
        self._blocks_remaining = blocks_remaining
        self._target_height = target_height

    def update(self, blocks_remaining: int, target_height: int) -> None:
        self._blocks_remaining = blocks_remaining
        self._target_height = target_height

    def render_interface(self, frame: np.ndarray) -> np.ndarray:
        for x in range(GRID_WIDTH):
            if x < self._blocks_remaining:
                frame[0, x] = 12
            else:
                frame[0, x] = 5
        frame[1, 0] = 11
        frame[1, 1] = 11
        frame[1, 2] = 11
        frame[1, 3] = 11
        return frame


levels = [
    Level(
        sprites=[
            sprites["player"].clone().set_position(4, 1),
            sprites["floor"].clone().set_position(0, FLOOR_Y),
            sprites["target_line"].clone().set_position(0, FLOOR_Y - 2),
        ],
        grid_size=(GRID_WIDTH, GRID_HEIGHT),
        data={
            "target_height": 2,
            "blocks_remaining": 3,
            "step_limit": 30,
        },
        name="Level 1",
    ),
    Level(
        sprites=[
            sprites["player"].clone().set_position(4, 1),
            sprites["floor"].clone().set_position(0, FLOOR_Y),
            sprites["target_line"].clone().set_position(0, FLOOR_Y - 3),
        ],
        grid_size=(GRID_WIDTH, GRID_HEIGHT),
        data={
            "target_height": 3,
            "blocks_remaining": 4,
            "step_limit": 40,
        },
        name="Level 2",
    ),
    Level(
        sprites=[
            sprites["player"].clone().set_position(4, 1),
            sprites["floor"].clone().set_position(0, FLOOR_Y),
            sprites["target_line"].clone().set_position(0, FLOOR_Y - 4),
        ],
        grid_size=(GRID_WIDTH, GRID_HEIGHT),
        data={
            "target_height": 4,
            "blocks_remaining": 5,
            "step_limit": 50,
        },
        name="Level 3",
    ),
    Level(
        sprites=[
            sprites["player"].clone().set_position(4, 1),
            sprites["floor"].clone().set_position(0, FLOOR_Y),
            sprites["target_line"].clone().set_position(0, FLOOR_Y - 5),
        ],
        grid_size=(GRID_WIDTH, GRID_HEIGHT),
        data={
            "target_height": 5,
            "blocks_remaining": 6,
            "step_limit": 60,
        },
        name="Level 4",
    ),
    Level(
        sprites=[
            sprites["player"].clone().set_position(4, 1),
            sprites["floor"].clone().set_position(0, FLOOR_Y),
            sprites["target_line"].clone().set_position(0, FLOOR_Y - 6),
        ],
        grid_size=(GRID_WIDTH, GRID_HEIGHT),
        data={
            "target_height": 6,
            "blocks_remaining": 7,
            "step_limit": 70,
        },
        name="Level 5",
    ),
]


class Gr01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Gr01UI(0, 0)
        super().__init__(
            "gr01",
            levels,
            Camera(
                0,
                0,
                GRID_WIDTH,
                GRID_HEIGHT,
                BACKGROUND_COLOR,
                PADDING_COLOR,
                [self._ui],
            ),
            False,
            1,
            [1, 2, 3, 4, 5],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._blocks_remaining = self.current_level.get_data("blocks_remaining")
        self._target_height = self.current_level.get_data("target_height")
        self._step_limit = self.current_level.get_data("step_limit")
        self._step_count = 0
        self._placed_blocks = []
        self._ui.update(self._blocks_remaining, self._target_height)

    def step(self) -> None:
        self._step_count += 1

        if self._step_count > self._step_limit:
            self.lose()
            self.complete_action()
            return

        action = self.action.id.value

        if action == 1:
            pass
        elif action == 2:
            pass
        elif action == 3:
            new_x = self._player.x - 1
            if new_x >= 0:
                self._player.set_position(new_x, self._player.y)
        elif action == 4:
            new_x = self._player.x + 1
            if new_x <= GRID_WIDTH - 2:
                self._player.set_position(new_x, self._player.y)
        elif action == 5:
            if self._blocks_remaining > 0:
                self._drop_block()
                self._blocks_remaining -= 1
                self._ui.update(self._blocks_remaining, self._target_height)

                if self._check_win():
                    self.next_level()
                    self.complete_action()
                    return

                if self._blocks_remaining == 0:
                    if not self._check_win():
                        self.lose()
                        self.complete_action()
                        return

        self.complete_action()

    def _drop_block(self) -> None:
        drop_x = self._player.x
        drop_y = 2
        block_height = 2
        block_bottom = drop_y + block_height - 1

        while block_bottom < FLOOR_Y:
            occupied = False
            for block in self._placed_blocks:
                if block.x == drop_x:
                    block_top = block.y
                    block_bot = block.y + 2 - 1
                    if block_top <= block_bottom and block_bot >= drop_y:
                        occupied = True
                        break
            if occupied:
                break
            drop_y += 1
            block_bottom = drop_y + block_height - 1

        final_y = drop_y - 1
        if final_y < 2:
            final_y = 2

        new_block = Sprite(
            pixels=sprites["block"].pixels,
            name="block",
            visible=True,
            collidable=True,
            tags=["block"],
        ).set_position(drop_x, final_y)
        self.current_level.add_sprite(new_block)
        self._placed_blocks.append(new_block)

    def _check_win(self) -> bool:
        if not self._placed_blocks:
            return False

        target_y = FLOOR_Y - self._target_height
        for block in self._placed_blocks:
            if block.y <= target_y:
                return True
        return False
