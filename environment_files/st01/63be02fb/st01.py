"""Sentry sweep: guard looks along a 90° cone; get spotted and you lose. ACTION5 whistles to make the guard step forward one cell."""

from arcengine import (
    ARCBaseGame,
    Camera,
    GameAction,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class St01UI(RenderableUserDisplay):
    def __init__(self, w: int) -> None:
        self._w = w

    def update(self, w: int) -> None:
        self._w = w

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        frame[h - 2, 2] = 8
        frame[h - 2, 3] = self._w
        return frame


sprites = {
    "player": Sprite(
        pixels=[[9]],
        name="player",
        visible=True,
        collidable=True,
        tags=["player"],
    ),
    "guard": Sprite(
        pixels=[[8]],
        name="guard",
        visible=True,
        collidable=False,
        tags=["guard"],
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

DX = (0, 1, 0, -1)
DY = (-1, 0, 1, 0)


def mk(sl, facing: int, d: int):
    return Level(
        sprites=sl,
        grid_size=(16, 16),
        data={"difficulty": d, "guard_facing": facing},
    )


levels = [
    mk(
        [
            sprites["player"].clone().set_position(1, 8),
            sprites["guard"].clone().set_position(10, 8),
            sprites["goal"].clone().set_position(14, 14),
        ],
        3,
        1,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["guard"].clone().set_position(8, 4),
            sprites["goal"].clone().set_position(15, 15),
        ],
        2,
        2,
    ),
    mk(
        [
            sprites["player"].clone().set_position(2, 14),
            sprites["guard"].clone().set_position(8, 8),
            sprites["goal"].clone().set_position(14, 0),
        ]
        + [sprites["wall"].clone().set_position(8, y) for y in range(16) if abs(y - 8) > 2],
        0,
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(4, 4),
            sprites["guard"].clone().set_position(12, 12),
            sprites["goal"].clone().set_position(0, 15),
        ],
        3,
        4,
    ),
    mk(
        [
            sprites["player"].clone().set_position(15, 15),
            sprites["guard"].clone().set_position(7, 7),
            sprites["goal"].clone().set_position(0, 0),
        ],
        1,
        5,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class St01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = St01UI(0)
        super().__init__(
            "st01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 5],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._guard = self.current_level.get_sprites_by_tag("guard")[0]
        self._face = int(self.current_level.get_data("guard_facing") or 0) % 4
        self._ui.update(self._face)

    def _seen(self) -> bool:
        gx, gy = self._guard.x, self._guard.y
        px, py = self._player.x, self._player.y
        fdx, fdy = DX[self._face], DY[self._face]
        rdx, rdy = -fdy, fdx
        for dist in range(1, 8):
            cx = gx + fdx * dist
            cy = gy + fdy * dist
            if not (
                0 <= cx < self.current_level.grid_size[0]
                and 0 <= cy < self.current_level.grid_size[1]
            ):
                break
            for w in (-1, 0, 1):
                tx = cx + rdx * w
                ty = cy + rdy * w
                if tx == px and ty == py:
                    return True
                sp = self.current_level.get_sprite_at(tx, ty, ignore_collidable=True)
                if sp and "wall" in sp.tags:
                    break
        return False

    def step(self) -> None:
        if self.action.id == GameAction.ACTION5:
            fdx, fdy = DX[self._face], DY[self._face]
            nx, ny = self._guard.x + fdx, self._guard.y + fdy
            gw, gh = self.current_level.grid_size
            if 0 <= nx < gw and 0 <= ny < gh:
                sp = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
                if not sp or "wall" not in sp.tags:
                    self._guard.set_position(nx, ny)
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
        else:
            self.complete_action()
            return

        nx, ny = self._player.x + dx, self._player.y + dy
        gw, gh = self.current_level.grid_size
        if 0 <= nx < gw and 0 <= ny < gh:
            sp = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
            if not sp or not sp.is_collidable:
                self._player.set_position(nx, ny)

        if self._seen():
            self.lose()
            self.complete_action()
            return

        gl = self.current_level.get_sprites_by_tag("goal")
        if gl and self._player.x == gl[0].x and self._player.y == gl[0].y:
            self.next_level()

        self.complete_action()
