"""Wind gust: every K steps you are pushed one cell east if that cell is free."""

from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Wg01UI(RenderableUserDisplay):
    def __init__(self, k: int) -> None:
        self._k = k

    def update(self, k: int) -> None:
        self._k = k

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        # Bottom ticks = gust period **K** (not every-step row belts like cy01/eb01).
        for i in range(min(self._k, min(8, w - 2))):
            frame[h - 2, 1 + i] = 10
        frame[2, 1] = 8
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


def mk(sl: list, d: int, k: int) -> Level:
    return Level(sprites=sl, grid_size=(10, 10), data={"difficulty": d, "wind_k": k})


levels = [
    mk(
        [
            sprites["player"].clone().set_position(0, 5),
            sprites["goal"].clone().set_position(8, 5),
        ],
        1,
        4,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["goal"].clone().set_position(8, 8),
        ],
        2,
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["goal"].clone().set_position(9, 9),
            sprites["wall"].clone().set_position(7, 5),
        ],
        3,
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(2, 5),
            sprites["goal"].clone().set_position(7, 5),
        ],
        4,
        2,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 9),
            sprites["goal"].clone().set_position(9, 0),
        ],
        5,
        2,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Wg01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Wg01UI(3)
        super().__init__(
            "wg01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._goal = self.current_level.get_sprites_by_tag("goal")[0]
        self._k = int(level.get_data("wind_k") or 3)
        self._ctr = 0
        self._ui.update(self._k)

    def _blocked(self, x: int, y: int) -> bool:
        gw, gh = self.current_level.grid_size
        if not (0 <= x < gw and 0 <= y < gh):
            return True
        sp = self.current_level.get_sprite_at(x, y, ignore_collidable=True)
        return bool(sp and "wall" in sp.tags)

    def _wind(self) -> None:
        self._ctr += 1
        if self._ctr < self._k:
            return
        self._ctr = 0
        nx = self._player.x + 1
        ny = self._player.y
        if not self._blocked(nx, ny):
            self._player.set_position(nx, ny)

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
            if (0 <= nx < gw and 0 <= ny < gh) and not self._blocked(nx, ny):
                self._player.set_position(nx, ny)

        self._wind()

        if self._player.x == self._goal.x and self._player.y == self._goal.y:
            self.next_level()

        self.complete_action()
