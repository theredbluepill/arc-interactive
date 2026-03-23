"""Magnet crates: after each move, each metal crate slides one cell toward the player if the path is clear."""

from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Mb01UI(RenderableUserDisplay):
    def __init__(self, n_crates: int) -> None:
        self._n_crates = n_crates

    def update(self, n_crates: int) -> None:
        self._n_crates = n_crates

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, _w = frame.shape
        for i in range(min(self._n_crates, 12)):
            frame[h - 2, 1 + i] = 12
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
    "metal": Sprite(
        pixels=[[2]],
        name="metal",
        visible=True,
        collidable=True,
        tags=["metal", "crate"],
    ),
}


def mk(sl: list, d: int) -> Level:
    return Level(sprites=sl, grid_size=(10, 10), data={"difficulty": d})


levels = [
    mk(
        [
            sprites["player"].clone().set_position(1, 5),
            sprites["metal"].clone().set_position(5, 5),
            sprites["goal"].clone().set_position(8, 5),
        ],
        1,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 5),
            sprites["metal"].clone().set_position(4, 5),
            sprites["goal"].clone().set_position(9, 5),
        ],
        2,
    ),
    mk(
        [
            sprites["player"].clone().set_position(2, 2),
            sprites["metal"].clone().set_position(5, 2),
            sprites["metal"].clone().set_position(5, 5),
            sprites["goal"].clone().set_position(8, 8),
        ],
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["metal"].clone().set_position(4, 4),
            sprites["goal"].clone().set_position(8, 1),
            sprites["wall"].clone().set_position(6, 3),
            sprites["wall"].clone().set_position(6, 4),
            sprites["wall"].clone().set_position(6, 5),
        ],
        4,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["metal"].clone().set_position(3, 3),
            sprites["goal"].clone().set_position(9, 9),
        ],
        5,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Mb01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Mb01UI(1)
        super().__init__(
            "mb01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._goal = self.current_level.get_sprites_by_tag("goal")[0]
        self._crates = list(self.current_level.get_sprites_by_tag("metal"))
        self._ui.update(len(self._crates))

    def _blocked_move(self, x: int, y: int, ignore: Sprite | None = None) -> bool:
        gw, gh = self.current_level.grid_size
        if not (0 <= x < gw and 0 <= y < gh):
            return True
        sp = self.current_level.get_sprite_at(x, y, ignore_collidable=True)
        if sp is ignore:
            return False
        if not sp:
            return False
        if "goal" in sp.tags:
            return False
        return sp.is_collidable

    def _pull_crates(self) -> None:
        px, py = self._player.x, self._player.y
        for c in self._crates:
            cx, cy = c.x, c.y
            dx = (1 if px > cx else -1) if px != cx else 0
            dy = (1 if py > cy else -1) if py != cy else 0
            if dx != 0 and dy != 0:
                if abs(px - cx) >= abs(py - cy):
                    dy = 0
                else:
                    dx = 0
            nx, ny = cx + dx, cy + dy
            if not self._blocked_move(nx, ny, ignore=c):
                c.set_position(nx, ny)

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
        if sp and "metal" in sp.tags:
            self.complete_action()
            return

        self._player.set_position(nx, ny)
        self._pull_crates()

        if self._player.x == self._goal.x and self._player.y == self._goal.y:
            self.next_level()

        self.complete_action()
