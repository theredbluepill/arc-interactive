"""Divergent walls: ACTION5 toggles timeline 0/1; only walls for the active timeline are collidable."""

from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Dv01UI(RenderableUserDisplay):
    def __init__(self, n_levels: int) -> None:
        self._t = 0
        self._n_levels = n_levels
        self._li = 0

    def update(self, t: int, level_index: int | None = None) -> None:
        self._t = t
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
        frame[h - 2, 2] = 10 if self._t == 0 else 7
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
    "wall0": Sprite(
        pixels=[[3]],
        name="wall0",
        visible=True,
        collidable=True,
        tags=["wall", "t0"],
    ),
    "wall1": Sprite(
        pixels=[[4]],
        name="wall1",
        visible=True,
        collidable=True,
        tags=["wall", "t1"],
    ),
}


def mk(sl: list, d: int) -> Level:
    return Level(sprites=sl, grid_size=(10, 10), data={"difficulty": d})


levels = [
    mk(
        [
            sprites["player"].clone().set_position(0, 5),
            sprites["goal"].clone().set_position(9, 5),
            sprites["wall0"].clone().set_position(4, 5),
            sprites["wall1"].clone().set_position(6, 5),
        ],
        1,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["goal"].clone().set_position(8, 8),
            sprites["wall0"].clone().set_position(5, 4),
            sprites["wall1"].clone().set_position(5, 6),
        ],
        2,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["goal"].clone().set_position(9, 9),
            sprites["wall0"].clone().set_position(3, 5),
            sprites["wall1"].clone().set_position(7, 5),
        ],
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(2, 5),
            sprites["goal"].clone().set_position(7, 5),
            sprites["wall0"].clone().set_position(4, 5),
            sprites["wall1"].clone().set_position(5, 4),
        ],
        4,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 9),
            sprites["goal"].clone().set_position(9, 0),
            sprites["wall0"].clone().set_position(5, 3),
            sprites["wall1"].clone().set_position(5, 7),
        ],
        5,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Dv01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Dv01UI(len(levels))
        super().__init__(
            "dv01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 5],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._goal = self.current_level.get_sprites_by_tag("goal")[0]
        self._tl = 0
        self._walls0 = [s for s in self.current_level.get_sprites_by_tag("wall") if "t0" in s.tags]
        self._walls1 = [s for s in self.current_level.get_sprites_by_tag("wall") if "t1" in s.tags]
        self._sync_walls()

    def _sync_walls(self) -> None:
        for w in self._walls0:
            w.set_collidable(self._tl == 0)
        for w in self._walls1:
            w.set_collidable(self._tl == 1)
        self._ui.update(self._tl, self.level_index)

    def step(self) -> None:
        if self.action.id.value == 5:
            self._tl = 1 - self._tl
            self._sync_walls()
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
        if sp and "wall" in sp.tags and sp.is_collidable:
            self.complete_action()
            return

        self._player.set_position(nx, ny)

        if self._player.x == self._goal.x and self._player.y == self._goal.y:
            self.next_level()

        self.complete_action()
