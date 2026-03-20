"""Warp line: crossing a directed warp band shifts you +2 along its axis when the skip cell is clear."""

from arcengine import (
    ARCBaseGame,
    Camera,
    GameAction,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Wa01UI(RenderableUserDisplay):
    def __init__(self, d: int) -> None:
        self._d = d

    def update(self, d: int) -> None:
        self._d = d

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for i in range(min(self._d, 10)):
            frame[h - 2, 1 + i] = 6
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
    "warp_h": Sprite(
        pixels=[[6]],
        name="warp_h",
        visible=True,
        collidable=False,
        tags=["warp", "axis_x"],
    ),
    "warp_v": Sprite(
        pixels=[[7]],
        name="warp_v",
        visible=True,
        collidable=False,
        tags=["warp", "axis_y"],
    ),
}


def mk(sl, d: int):
    return Level(sprites=sl, grid_size=(12, 12), data={"difficulty": d})


levels = [
    mk(
        [
            sprites["player"].clone().set_position(1, 6),
            sprites["warp_h"].clone().set_position(5, 6),
            sprites["goal"].clone().set_position(10, 6),
        ],
        1,
    ),
    mk(
        [
            sprites["player"].clone().set_position(6, 1),
            sprites["warp_v"].clone().set_position(6, 5),
            sprites["goal"].clone().set_position(6, 10),
        ],
        2,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["warp_h"].clone().set_position(3, 0),
            sprites["warp_v"].clone().set_position(8, 6),
            sprites["goal"].clone().set_position(11, 11),
        ],
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(2, 2),
            sprites["warp_h"].clone().set_position(6, 2),
            sprites["wall"].clone().set_position(8, 2),
            sprites["goal"].clone().set_position(10, 2),
        ],
        4,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 10),
            sprites["warp_v"].clone().set_position(5, 8),
            sprites["warp_h"].clone().set_position(8, 4),
            sprites["goal"].clone().set_position(10, 1),
        ],
        5,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Wa01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Wa01UI(1)
        super().__init__(
            "wa01",
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

    def _warp_shift(self, x: int, y: int) -> tuple[int, int]:
        sp = self.current_level.get_sprite_at(x, y, ignore_collidable=True)
        if not sp or "warp" not in sp.tags:
            return x, y
        if "axis_x" in sp.tags:
            nx, ny = x + 2, y
        elif "axis_y" in sp.tags:
            nx, ny = x, y + 2
        else:
            return x, y
        if self._blocked(nx, ny):
            return x, y
        return nx, ny

    def step(self) -> None:
        dx = dy = 0
        if self.action.id == GameAction.ACTION1:
            dy = -1
        elif self.action.id == GameAction.ACTION2:
            dy = 1
        elif self.action.id == GameAction.ACTION3:
            dx = -1
        elif self.action.id == GameAction.ACTION4:
            dx = 1
        else:
            self.complete_action()
            return

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

        if not sp or not sp.is_collidable:
            self._player.set_position(nx, ny)

        fx, fy = self._warp_shift(self._player.x, self._player.y)
        self._player.set_position(fx, fy)

        if self._player.x == self._goal.x and self._player.y == self._goal.y:
            self.next_level()

        self.complete_action()
