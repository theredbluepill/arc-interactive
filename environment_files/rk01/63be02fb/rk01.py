"""Rook courier: ACTION1–4 slide orthogonally until a wall blocks."""

from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Rk01UI(RenderableUserDisplay):
    def __init__(self, d: int) -> None:
        self._d = d

    def update(self, d: int) -> None:
        self._d = d

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, _w = frame.shape
        for i in range(min(self._d, 12)):
            frame[h - 2, 1 + i] = 11
        return frame


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
    "wall": Sprite(
        pixels=[[3]],
        name="wall",
        visible=True,
        collidable=True,
        tags=["wall"],
    ),
}


def mk(sl: list, d: int) -> Level:
    return Level(sprites=sl, grid_size=(10, 10), data={"difficulty": d})


levels = [
    mk(
        [
            sprites["player"].clone().set_position(1, 5),
            sprites["goal"].clone().set_position(8, 5),
        ],
        1,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["goal"].clone().set_position(9, 9),
            sprites["wall"].clone().set_position(5, 5),
        ],
        2,
    ),
    mk(
        [
            sprites["player"].clone().set_position(2, 2),
            sprites["goal"].clone().set_position(9, 2),
        ]
        + [sprites["wall"].clone().set_position(5, y) for y in range(10) if y not in (2, 5)],
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["goal"].clone().set_position(9, 9),
        ]
        + [sprites["wall"].clone().set_position(x, 4) for x in range(3, 7)],
        4,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 9),
            sprites["goal"].clone().set_position(9, 0),
        ],
        5,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Rk01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Rk01UI(1)
        super().__init__(
            "rk01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._goal = self.current_level.get_sprites_by_tag("goal")[0]
        self._ui.update(int(level.get_data("difficulty") or 1))

    def _blocked(self, x: int, y: int) -> bool:
        gw, gh = self.current_level.grid_size
        if not (0 <= x < gw and 0 <= y < gh):
            return True
        sp = self.current_level.get_sprite_at(x, y, ignore_collidable=True)
        return bool(sp and "wall" in sp.tags)

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

        if dx == 0 and dy == 0:
            self.complete_action()
            return

        x, y = self._player.x, self._player.y
        while True:
            nx, ny = x + dx, y + dy
            if self._blocked(nx, ny):
                break
            x, y = nx, ny
            if x == self._goal.x and y == self._goal.y:
                self._player.set_position(x, y)
                self.next_level()
                self.complete_action()
                return

        if x != self._player.x or y != self._player.y:
            self._player.set_position(x, y)

        if self._player.x == self._goal.x and self._player.y == self._goal.y:
            self.next_level()

        self.complete_action()
