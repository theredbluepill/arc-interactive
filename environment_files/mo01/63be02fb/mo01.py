"""Momentum: you must move at least two steps in a row in the same direction before changing direction (illegal turn = lose)."""

from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Mo01UI(RenderableUserDisplay):
    def __init__(self, streak: int) -> None:
        self._streak = streak

    def update(self, streak: int) -> None:
        self._streak = streak

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        c = 11 if self._streak >= 2 else 8
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
    "wall": Sprite(
        pixels=[[3]],
        name="wall",
        visible=True,
        collidable=True,
        tags=["wall"],
    ),
}


def mk(sl, grid_size, difficulty):
    return Level(sprites=sl, grid_size=grid_size, data={"difficulty": difficulty})


levels = [
    mk(
        [
            sprites["player"].clone().set_position(0, 3),
            sprites["target"].clone().set_position(7, 3),
        ],
        (8, 8),
        1,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["target"].clone().set_position(6, 6),
        ],
        (8, 8),
        2,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["target"].clone().set_position(7, 7),
        ]
        + [sprites["wall"].clone().set_position(4, y) for y in range(8) if y != 3],
        (8, 8),
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(2, 2),
            sprites["target"].clone().set_position(5, 5),
        ],
        (8, 8),
        4,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 7),
            sprites["target"].clone().set_position(7, 0),
        ],
        (8, 8),
        5,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Mo01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Mo01UI(0)
        super().__init__(
            "mo01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._targets = self.current_level.get_sprites_by_tag("target")
        self._dir: tuple[int, int] | None = None
        self._streak = 0
        self._ui.update(0)

    def _intent(self) -> tuple[int, int]:
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
        return (dx, dy)

    def step(self) -> None:
        dx, dy = self._intent()
        if dx == 0 and dy == 0:
            self.complete_action()
            return

        if self._dir is None:
            self._dir = (dx, dy)
            self._streak = 1
        elif (dx, dy) == self._dir:
            self._streak += 1
        else:
            if self._streak < 2:
                self.lose()
                self.complete_action()
                return
            self._dir = (dx, dy)
            self._streak = 1

        self._ui.update(self._streak)

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
        if not sprite or not sprite.is_collidable:
            self._player.set_position(nx, ny)

        for t in self._targets:
            if self._player.x == t.x and self._player.y == t.y:
                self.next_level()
                break

        self.complete_action()
