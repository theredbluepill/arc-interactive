"""Echo move: odd steps use your input; the next step repeats the same delta automatically (input ignored on echo steps)."""

from arcengine import (
    ARCBaseGame,
    Camera,
    GameAction,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Em01UI(RenderableUserDisplay):
    def __init__(self, echo: bool) -> None:
        self._echo = echo
        self._edx = 0
        self._edy = 0

    def update(self, echo: bool, edx: int = 0, edy: int = 0) -> None:
        self._echo = echo
        self._edx = edx
        self._edy = edy

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        frame[h - 2, 2] = 7 if self._echo else 5
        if self._echo and (self._edx != 0 or self._edy != 0):
            cx, cy = 5, h - 2
            c = 10
            if abs(self._edx) >= abs(self._edy):
                if self._edx < 0:
                    frame[cy, cx - 1] = c
                elif self._edx > 0:
                    frame[cy, cx + 1] = c
            else:
                if self._edy < 0:
                    frame[cy - 1, cx] = c
                elif self._edy > 0:
                    frame[cy + 1, cx] = c
            frame[cy, cx] = c
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


def mk(sl, d: int):
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
            sprites["player"].clone().set_position(2, 2),
            sprites["goal"].clone().set_position(7, 7),
            sprites["wall"].clone().set_position(4, 3),
            sprites["wall"].clone().set_position(4, 4),
        ],
        2,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["goal"].clone().set_position(9, 9),
        ]
        + [sprites["wall"].clone().set_position(5, y) for y in range(3, 8)],
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(8, 1),
            sprites["goal"].clone().set_position(1, 8),
        ],
        4,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["goal"].clone().set_position(8, 8),
            sprites["wall"].clone().set_position(3, 2),
            sprites["wall"].clone().set_position(3, 3),
            sprites["wall"].clone().set_position(6, 6),
            sprites["wall"].clone().set_position(6, 7),
        ],
        5,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Em01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Em01UI(False)
        self._echo_dx = 0
        self._echo_dy = 0
        self._parity = 0
        super().__init__(
            "em01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._goal = self.current_level.get_sprites_by_tag("goal")[0]
        self._echo_dx = self._echo_dy = 0
        self._parity = 0
        self._ui.update(False, 0, 0)

    def _apply_delta(self, dx: int, dy: int) -> None:
        if dx == 0 and dy == 0:
            return
        nx = self._player.x + dx
        ny = self._player.y + dy
        gw, gh = self.current_level.grid_size
        if not (0 <= nx < gw and 0 <= ny < gh):
            return
        sp = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
        if sp and "wall" in sp.tags:
            return
        if not sp or not sp.is_collidable:
            self._player.set_position(nx, ny)
        if self._player.x == self._goal.x and self._player.y == self._goal.y:
            self.next_level()

    def step(self) -> None:
        use_echo = self._parity % 2 == 1
        self._ui.update(use_echo, self._echo_dx, self._echo_dy)

        dx = dy = 0
        if not use_echo:
            if self.action.id == GameAction.ACTION1:
                dy = -1
            elif self.action.id == GameAction.ACTION2:
                dy = 1
            elif self.action.id == GameAction.ACTION3:
                dx = -1
            elif self.action.id == GameAction.ACTION4:
                dx = 1
            self._echo_dx, self._echo_dy = dx, dy
        else:
            dx, dy = self._echo_dx, self._echo_dy

        if dx == 0 and dy == 0:
            self._parity += 1
            self.complete_action()
            return

        self._apply_delta(dx, dy)
        self._parity += 1
        self.complete_action()
