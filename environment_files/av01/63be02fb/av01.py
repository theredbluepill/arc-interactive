"""Avalanche: gray rocks fall one cell after each move when the cell below is empty (sb01 uses tan sand + different levels, same fall step)."""

from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Av01UI(RenderableUserDisplay):
    def __init__(self, d: int) -> None:
        self._d = d

    def update(self, d: int) -> None:
        self._d = d

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, _w = frame.shape
        for i in range(min(self._d, 12)):
            frame[h - 2, 1 + i] = 2
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
    "rock": Sprite(
        pixels=[[2]],
        name="rock",
        visible=True,
        collidable=True,
        tags=["rock"],
    ),
}


def mk(sl: list, d: int) -> Level:
    return Level(sprites=sl, grid_size=(10, 10), data={"difficulty": d})


levels = [
    mk(
        [
            sprites["player"].clone().set_position(0, 5),
            sprites["goal"].clone().set_position(9, 5),
            sprites["rock"].clone().set_position(5, 2),
        ],
        1,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 8),
            sprites["goal"].clone().set_position(8, 8),
            sprites["rock"].clone().set_position(4, 3),
            sprites["rock"].clone().set_position(5, 3),
        ],
        2,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["goal"].clone().set_position(9, 9),
            sprites["wall"].clone().set_position(5, 7),
            sprites["wall"].clone().set_position(5, 8),
            sprites["wall"].clone().set_position(5, 9),
            sprites["rock"].clone().set_position(5, 2),
        ],
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(2, 5),
            sprites["goal"].clone().set_position(7, 5),
            sprites["rock"].clone().set_position(5, 1),
        ],
        4,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 9),
            sprites["goal"].clone().set_position(9, 0),
            sprites["rock"].clone().set_position(3, 2),
            sprites["rock"].clone().set_position(6, 2),
        ],
        5,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Av01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Av01UI(1)
        super().__init__(
            "av01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._goal = self.current_level.get_sprites_by_tag("goal")[0]
        self._rocks = list(self.current_level.get_sprites_by_tag("rock"))
        self._ui.update(int(level.get_data("difficulty") or 1))

    def _blocked(self, x: int, y: int, ignore: Sprite | None = None) -> bool:
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

    def _fall_rocks(self) -> None:
        changed = True
        while changed:
            changed = False
            for r in list(self.current_level.get_sprites_by_tag("rock")):
                nx, ny = r.x, r.y + 1
                if not self._blocked(nx, ny, ignore=r):
                    r.set_position(nx, ny)
                    changed = True

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
        if sp and "rock" in sp.tags:
            self.complete_action()
            return

        self._player.set_position(nx, ny)
        self._fall_rocks()

        for r in self.current_level.get_sprites_by_tag("rock"):
            if r.x == self._player.x and r.y == self._player.y:
                self.lose()
                self.complete_action()
                return

        if self._player.x == self._goal.x and self._player.y == self._goal.y:
            self.next_level()

        self.complete_action()
