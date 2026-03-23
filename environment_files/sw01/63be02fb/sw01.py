"""Swap partner: ACTION5 swaps your position with the magenta partner when orthogonally adjacent."""

from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Sw01UI(RenderableUserDisplay):
    def __init__(self, d: int) -> None:
        self._d = d
        self._reject_frames = 0

    def update(self, d: int) -> None:
        self._d = d

    def flash_reject(self) -> None:
        self._reject_frames = 4

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for i in range(min(self._d, 12)):
            frame[h - 2, 1 + i] = 7
        if self._reject_frames > 0:
            frame[2, min(3, w - 1)] = 11
            self._reject_frames -= 1
        return frame


sprites = {
    "player": Sprite(
        pixels=[[9]],
        name="player",
        visible=True,
        collidable=True,
        tags=["player"],
    ),
    "partner": Sprite(
        pixels=[[7]],
        name="partner",
        visible=True,
        collidable=True,
        tags=["partner"],
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
            sprites["partner"].clone().set_position(2, 5),
            sprites["goal"].clone().set_position(8, 5),
        ],
        1,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 5),
            sprites["partner"].clone().set_position(1, 5),
            sprites["goal"].clone().set_position(9, 5),
        ],
        2,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["partner"].clone().set_position(1, 2),
            sprites["goal"].clone().set_position(8, 8),
        ],
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(2, 5),
            sprites["partner"].clone().set_position(3, 5),
            sprites["goal"].clone().set_position(7, 5),
            sprites["wall"].clone().set_position(5, 4),
            sprites["wall"].clone().set_position(5, 6),
        ],
        4,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["partner"].clone().set_position(0, 1),
            sprites["goal"].clone().set_position(9, 9),
        ],
        5,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Sw01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Sw01UI(1)
        super().__init__(
            "sw01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 5],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._partner = self.current_level.get_sprites_by_tag("partner")[0]
        self._goal = self.current_level.get_sprites_by_tag("goal")[0]
        self._ui.update(int(level.get_data("difficulty") or 1))

    def _orth_adj(self) -> bool:
        d = abs(self._player.x - self._partner.x) + abs(self._player.y - self._partner.y)
        return d == 1

    def step(self) -> None:
        if self.action.id.value == 5:
            if self._orth_adj():
                px, py = self._player.x, self._player.y
                qx, qy = self._partner.x, self._partner.y
                self._player.set_position(qx, qy)
                self._partner.set_position(px, py)
            else:
                self._ui.flash_reject()
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
            self.complete_action()
            return
        if sp and "partner" in sp.tags:
            self.complete_action()
            return

        self._player.set_position(nx, ny)

        if self._player.x == self._goal.x and self._player.y == self._goal.y:
            self.next_level()

        self.complete_action()
