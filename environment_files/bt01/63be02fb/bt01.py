"""Battery steps: charge drops each move; pads refill to cap; goal clears before 0-charge loss on the same step."""

from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Bt01UI(RenderableUserDisplay):
    def __init__(self, ch: int) -> None:
        self._ch = ch

    def update(self, ch: int) -> None:
        self._ch = ch

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        frame[1, min(2, w - 1)] = 11
        for i in range(min(self._ch, 14)):
            frame[h - 2, 1 + i] = 14
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
    "pad": Sprite(
        pixels=[[10]],
        name="pad",
        visible=True,
        collidable=False,
        tags=["charge"],
    ),
}


def mk(sl: list, d: int, cap: int) -> Level:
    return Level(sprites=sl, grid_size=(10, 10), data={"difficulty": d, "cap": cap})


levels = [
    mk(
        [
            sprites["player"].clone().set_position(1, 5),
            sprites["pad"].clone().set_position(4, 5),
            sprites["goal"].clone().set_position(8, 5),
        ],
        1,
        30,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["pad"].clone().set_position(3, 3),
            sprites["goal"].clone().set_position(9, 9),
        ],
        2,
        25,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["pad"].clone().set_position(5, 1),
            sprites["goal"].clone().set_position(8, 8),
            sprites["wall"].clone().set_position(5, 4),
            sprites["wall"].clone().set_position(5, 5),
            sprites["wall"].clone().set_position(5, 6),
        ],
        3,
        22,
    ),
    mk(
        [
            sprites["player"].clone().set_position(2, 5),
            sprites["pad"].clone().set_position(5, 5),
            sprites["goal"].clone().set_position(8, 5),
        ],
        4,
        18,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 9),
            sprites["pad"].clone().set_position(5, 5),
            sprites["goal"].clone().set_position(9, 0),
        ],
        5,
        22,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Bt01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Bt01UI(20)
        super().__init__(
            "bt01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._goal = self.current_level.get_sprites_by_tag("goal")[0]
        self._cap = int(level.get_data("cap") or 25)
        self._charge = self._cap
        self._ui.update(self._charge)

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
        self._charge -= 1
        sp2 = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
        if sp2 and "charge" in sp2.tags:
            self._charge = self._cap
        self._ui.update(self._charge)

        if self._player.x == self._goal.x and self._player.y == self._goal.y:
            self.next_level()
            self.complete_action()
            return

        if self._charge <= 0:
            self.lose()
            self.complete_action()
            return

        self.complete_action()
