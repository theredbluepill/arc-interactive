"""Zone timer: every T steps, red hazard cells on a fixed pattern toggle blocking."""

from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Zq01UI(RenderableUserDisplay):
    def __init__(self, phase: bool) -> None:
        self._phase = phase

    def update(self, phase: bool) -> None:
        self._phase = phase

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        c = 8 if self._phase else 14
        for dy in range(3):
            for dx in range(3):
                frame[h - 3 + dy, w - 4 + dx] = c
        return frame


sprites = {
    "player": Sprite(
        pixels=[[9]],
        name="player",
        visible=True,
        collidable=True,
        tags=["player"],
    ),
    "target": Sprite(
        pixels=[[11]],
        name="target",
        visible=True,
        collidable=False,
        tags=["target"],
    ),
    "hazard": Sprite(
        pixels=[[8]],
        name="hazard",
        visible=True,
        collidable=True,
        tags=["zq_hazard"],
    ),
    "wall": Sprite(
        pixels=[[3]],
        name="wall",
        visible=True,
        collidable=True,
        tags=["wall"],
    ),
}


def mk(sl, grid_size, difficulty, period: int, hazard_cells: list[tuple[int, int]]):
    return Level(
        sprites=sl,
        grid_size=grid_size,
        data={
            "difficulty": difficulty,
            "period": period,
            "hazard_cells": hazard_cells,
        },
    )


levels = [
    mk(
        [
            sprites["player"].clone().set_position(0, 3),
            sprites["target"].clone().set_position(7, 3),
        ],
        (8, 8),
        1,
        5,
        [(4, 2), (4, 3), (4, 4), (4, 5)],
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["target"].clone().set_position(6, 6),
        ],
        (8, 8),
        2,
        4,
        [(3, 3), (4, 3), (3, 4), (4, 4)],
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["target"].clone().set_position(7, 7),
        ],
        (8, 8),
        3,
        6,
        [(2, y) for y in range(8) if y % 2 == 0],
    ),
    mk(
        [
            sprites["player"].clone().set_position(2, 4),
            sprites["target"].clone().set_position(7, 4),
        ],
        (10, 8),
        4,
        5,
        [(5, y) for y in range(8)],
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 7),
            sprites["target"].clone().set_position(7, 0),
        ],
        (8, 8),
        5,
        3,
        [(x, 4) for x in range(8) if x not in (0, 7)],
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Zq01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Zq01UI(False)
        super().__init__(
            "zq01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        for s in list(self.current_level.get_sprites_by_tag("zq_hazard")):
            self.current_level.remove_sprite(s)
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._targets = self.current_level.get_sprites_by_tag("target")
        self._ticks = 0
        self._hazard_on = False
        self._hazard_sprites: list[Sprite] = []
        cells = list(self.current_level.get_data("hazard_cells") or [])
        for hx, hy in cells:
            s = sprites["hazard"].clone().set_position(hx, hy)
            self._hazard_sprites.append(s)
            self.current_level.add_sprite(s)
        self._sync_hazards()

    def _sync_hazards(self) -> None:
        for s in self._hazard_sprites:
            if self._hazard_on:
                s.set_visible(True)
                s.set_collidable(True)
            else:
                s.set_visible(False)
                s.set_collidable(False)
        self._ui.update(self._hazard_on)

    def step(self) -> None:
        self._ticks += 1
        period = int(self.current_level.get_data("period") or 5)
        if self._ticks % period == 0:
            self._hazard_on = not self._hazard_on
            self._sync_hazards()

        dx = 0
        dy = 0
        if self.action.id.value == 1:
            dy = -1
        elif self.action.id.value == 2:
            dy = 1
        elif self.action.id.value == 3:
            dx = -1
        elif self.action.id.value == 4:
            dx = 1

        if dx == 0 and dy == 0:
            self.complete_action()
            return

        nx = self._player.x + dx
        ny = self._player.y + dy
        grid_w, grid_h = self.current_level.grid_size
        if not (0 <= nx < grid_w and 0 <= ny < grid_h):
            self.complete_action()
            return

        sprite = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
        if sprite and "wall" in sprite.tags:
            self.complete_action()
            return
        if sprite and "zq_hazard" in sprite.tags and sprite.is_collidable:
            self.complete_action()
            return

        if not sprite or not sprite.is_collidable:
            self._player.set_position(nx, ny)

        for t in self._targets:
            if self._player.x == t.x and self._player.y == t.y:
                self.next_level()
                break

        self.complete_action()
