"""Two-touch: step on the orange waypoint before the green goal counts."""

from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Tw01UI(RenderableUserDisplay):
    def __init__(self, n_levels: int) -> None:
        self._ok = False
        self._n_levels = n_levels
        self._li = 0

    def update(self, ok: bool, level_index: int | None = None) -> None:
        self._ok = ok
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
        frame[h - 2, 2] = 12 if self._ok else 8
        return frame


sprites = {
    "player": Sprite(
        pixels=[[9]],
        name="player",
        visible=True,
        collidable=True,
        tags=["player"],
    ),
    "way": Sprite(
        pixels=[[12]],
        name="way",
        visible=True,
        collidable=False,
        tags=["waypoint"],
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
            sprites["player"].clone().set_position(0, 5),
            sprites["way"].clone().set_position(4, 5),
            sprites["goal"].clone().set_position(8, 5),
        ],
        1,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["way"].clone().set_position(5, 5),
            sprites["goal"].clone().set_position(8, 8),
        ],
        2,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["way"].clone().set_position(3, 3),
            sprites["goal"].clone().set_position(9, 9),
        ],
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(2, 5),
            sprites["way"].clone().set_position(5, 5),
            sprites["goal"].clone().set_position(7, 5),
        ],
        4,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 9),
            sprites["way"].clone().set_position(5, 5),
            sprites["goal"].clone().set_position(9, 0),
        ],
        5,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Tw01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Tw01UI(len(levels))
        super().__init__(
            "tw01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._goal = self.current_level.get_sprites_by_tag("goal")[0]
        self._way = self.current_level.get_sprites_by_tag("waypoint")[0]
        self._touched = False
        self._ui.update(False, self.level_index)

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

        sp = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
        if sp and "wall" in sp.tags:
            self.complete_action()
            return

        self._player.set_position(nx, ny)

        if self._player.x == self._way.x and self._player.y == self._way.y:
            self._touched = True
            self._ui.update(True)

        if self._touched and self._player.x == self._goal.x and self._player.y == self._goal.y:
            self.next_level()

        self.complete_action()
