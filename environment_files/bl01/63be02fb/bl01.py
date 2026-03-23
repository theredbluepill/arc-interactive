"""Phase step: ACTION5 arms a one-use pass through a single wall on the next move."""

from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Bl01UI(RenderableUserDisplay):
    def __init__(self, armed: bool) -> None:
        self._armed = armed
        self._pulse = 0

    def update(self, armed: bool) -> None:
        if armed and not self._armed:
            self._pulse = 8
        self._armed = armed

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, _w = frame.shape
        if self._armed:
            for i, x in enumerate((2, 3, 4)):
                c = 15 if (self._pulse > 0 and i == 1) else 10
                frame[h - 2, x] = c
        else:
            frame[h - 2, 2] = 3
        if self._pulse > 0:
            self._pulse -= 1
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
            sprites["player"].clone().set_position(0, 5),
            sprites["goal"].clone().set_position(9, 5),
            sprites["wall"].clone().set_position(5, 5),
        ],
        1,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["goal"].clone().set_position(8, 8),
        ]
        + [sprites["wall"].clone().set_position(x, 5) for x in range(3, 7)],
        2,
    ),
    mk(
        [
            sprites["player"].clone().set_position(2, 5),
            sprites["goal"].clone().set_position(7, 5),
            sprites["wall"].clone().set_position(4, 5),
            sprites["wall"].clone().set_position(5, 5),
        ],
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["goal"].clone().set_position(9, 9),
            sprites["wall"].clone().set_position(5, 5),
        ],
        4,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 5),
            sprites["goal"].clone().set_position(8, 5),
            sprites["wall"].clone().set_position(4, 5),
            sprites["wall"].clone().set_position(5, 5),
            sprites["wall"].clone().set_position(6, 5),
        ],
        5,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Bl01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Bl01UI(False)
        super().__init__(
            "bl01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 5],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._goal = self.current_level.get_sprites_by_tag("goal")[0]
        self._phase_next = False
        self._ui.update(False)

    def step(self) -> None:
        if self.action.id.value == 5:
            self._phase_next = True
            self._ui.update(True)
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
            if self._phase_next:
                self._phase_next = False
                self._ui.update(False)
                self._player.set_position(nx, ny)
            else:
                self.complete_action()
                return
        else:
            self._phase_next = False
            self._ui.update(False)
            self._player.set_position(nx, ny)

        if self._player.x == self._goal.x and self._player.y == self._goal.y:
            self.next_level()

        self.complete_action()
