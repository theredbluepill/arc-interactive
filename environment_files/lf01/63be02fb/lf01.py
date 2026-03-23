"""Laser fence: a fixed row is lethal on alternating periods of P steps."""

from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Lf01UI(RenderableUserDisplay):
    def __init__(self, n_levels: int) -> None:
        self._on = False
        self._p = 3
        self._row = 5
        self._n_levels = n_levels
        self._li = 0

    def update(
        self,
        on: bool,
        level_index: int | None = None,
        *,
        period: int | None = None,
        laser_row: int | None = None,
    ) -> None:
        self._on = on
        if period is not None:
            self._p = period
        if laser_row is not None:
            self._row = laser_row
        if level_index is not None:
            self._li = level_index

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for i in range(min(self._n_levels, 14)):
            cx = 1 + i * 2
            if cx >= w:
                break
            c = 14 if i < self._li else (11 if i == self._li else 3)
            frame[0, cx] = c
        frame[h - 2, 2] = 8 if self._on else 14
        for i in range(min(self._p, 8)):
            frame[h - 3, 1 + i] = 10
        rr = min(max(self._row, 0), w - 2)
        frame[h - 4, 1 + rr] = 11
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


def mk(sl: list, d: int, p: int, row: int) -> Level:
    return Level(sprites=sl, grid_size=(10, 10), data={"difficulty": d, "period": p, "laser_row": row})


levels = [
    mk(
        [
            sprites["player"].clone().set_position(0, 4),
            sprites["goal"].clone().set_position(9, 6),
        ],
        1,
        3,
        5,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 3),
            sprites["goal"].clone().set_position(8, 7),
        ],
        2,
        2,
        5,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["goal"].clone().set_position(9, 9),
            sprites["wall"].clone().set_position(5, 5),
        ],
        3,
        3,
        4,
    ),
    mk(
        [
            sprites["player"].clone().set_position(2, 6),
            sprites["goal"].clone().set_position(7, 4),
        ],
        4,
        2,
        5,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 9),
            sprites["goal"].clone().set_position(9, 0),
        ],
        5,
        2,
        5,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Lf01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Lf01UI(len(levels))
        super().__init__(
            "lf01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._goal = self.current_level.get_sprites_by_tag("goal")[0]
        self._p = int(level.get_data("period") or 3)
        self._row = int(level.get_data("laser_row") or 5)
        self._tick = 0
        self._ui.update(
            self._laser_on(),
            self.level_index,
            period=self._p,
            laser_row=self._row,
        )

    def _laser_on(self) -> bool:
        return (self._tick // self._p) % 2 == 0

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

        if dx != 0 or dy != 0:
            nx = self._player.x + dx
            ny = self._player.y + dy
            gw, gh = self.current_level.grid_size
            if (0 <= nx < gw and 0 <= ny < gh):
                sp = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
                if not (sp and "wall" in sp.tags):
                    self._player.set_position(nx, ny)

        if self._laser_on() and self._player.y == self._row:
            self.lose()
            self.complete_action()
            return

        self._tick += 1
        self._ui.update(
            self._laser_on(),
            self.level_index,
            period=self._p,
            laser_row=self._row,
        )

        if self._player.x == self._goal.x and self._player.y == self._goal.y:
            self.next_level()

        self.complete_action()
