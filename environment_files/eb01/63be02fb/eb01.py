"""Escalator row: on the marked row, after each move you auto-slide one cell east when free."""

from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Eb01UI(RenderableUserDisplay):
    def __init__(self, row: int) -> None:
        self._row = row

    def update(self, row: int) -> None:
        self._row = row

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        # Bottom orange ticks: **east** escalator row; corner yellow marks eastward auto-slide (vs cy01 top / west).
        for i in range(min(self._row + 1, min(12, w - 2))):
            frame[h - 2, 1 + i] = 12
        frame[h - 2, min(w - 2, 15)] = 11
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


def mk(sl: list, d: int, row: int) -> Level:
    return Level(sprites=sl, grid_size=(10, 10), data={"difficulty": d, "escalator_row": row})


levels = [
    mk(
        [
            sprites["player"].clone().set_position(0, 5),
            sprites["goal"].clone().set_position(9, 5),
        ],
        1,
        5,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 5),
            sprites["goal"].clone().set_position(6, 5),
            sprites["wall"].clone().set_position(7, 5),
        ],
        2,
        5,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 3),
            sprites["goal"].clone().set_position(9, 7),
            sprites["wall"].clone().set_position(5, 5),
            sprites["wall"].clone().set_position(5, 6),
        ],
        3,
        5,
    ),
    mk(
        [
            sprites["player"].clone().set_position(2, 5),
            sprites["goal"].clone().set_position(8, 5),
        ],
        4,
        5,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 5),
            sprites["goal"].clone().set_position(9, 5),
        ]
        + [sprites["wall"].clone().set_position(x, 4) for x in (3, 4, 5)]
        + [sprites["wall"].clone().set_position(x, 6) for x in (3, 4, 5)],
        5,
        5,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Eb01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Eb01UI(5)
        super().__init__(
            "eb01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._goal = self.current_level.get_sprites_by_tag("goal")[0]
        self._row = int(level.get_data("escalator_row") or 5)
        self._ui.update(self._row)

    def _blocked(self, x: int, y: int) -> bool:
        gw, gh = self.current_level.grid_size
        if not (0 <= x < gw and 0 <= y < gh):
            return True
        sp = self.current_level.get_sprite_at(x, y, ignore_collidable=True)
        return bool(sp and "wall" in sp.tags)

    def _escalate(self) -> None:
        while self._player.y == self._row:
            nx = self._player.x + 1
            if self._blocked(nx, self._player.y):
                break
            self._player.set_position(nx, self._player.y)
            if self._player.x == self._goal.x and self._player.y == self._goal.y:
                return

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

        nx = self._player.x + dx
        ny = self._player.y + dy
        gw, gh = self.current_level.grid_size
        if not (0 <= nx < gw and 0 <= ny < gh):
            self.complete_action()
            return

        if self._blocked(nx, ny):
            self.complete_action()
            return

        self._player.set_position(nx, ny)
        if self._player.x == self._goal.x and self._player.y == self._goal.y:
            self.next_level()
            self.complete_action()
            return

        self._escalate()

        if self._player.x == self._goal.x and self._player.y == self._goal.y:
            self.next_level()

        self.complete_action()
