"""Conquest ring: visit every orange ring marker cell, then reach the green goal."""

from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Cq01UI(RenderableUserDisplay):
    def __init__(self, n_levels: int) -> None:
        self._left = 0
        self._n_levels = n_levels
        self._li = 0

    def update(self, left: int, level_index: int | None = None) -> None:
        self._left = left
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
        for i in range(min(self._left, 10)):
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
    "ring": Sprite(
        pixels=[[12]],
        name="ring",
        visible=True,
        collidable=False,
        tags=["ring"],
    ),
}


def mk(sl: list, d: int) -> Level:
    return Level(sprites=sl, grid_size=(10, 10), data={"difficulty": d})


levels = [
    mk(
        [
            sprites["player"].clone().set_position(0, 5),
            sprites["goal"].clone().set_position(9, 5),
            sprites["ring"].clone().set_position(4, 5),
            sprites["ring"].clone().set_position(5, 5),
            sprites["ring"].clone().set_position(6, 5),
        ],
        1,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["goal"].clone().set_position(8, 8),
        ]
        + [sprites["ring"].clone().set_position(x, 5) for x in range(2, 8)],
        2,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["goal"].clone().set_position(9, 9),
            sprites["ring"].clone().set_position(3, 3),
            sprites["ring"].clone().set_position(6, 3),
            sprites["ring"].clone().set_position(6, 6),
            sprites["ring"].clone().set_position(3, 6),
        ],
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(2, 5),
            sprites["goal"].clone().set_position(8, 5),
            sprites["ring"].clone().set_position(4, 4),
            sprites["ring"].clone().set_position(5, 4),
            sprites["ring"].clone().set_position(6, 4),
        ],
        4,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 9),
            sprites["goal"].clone().set_position(9, 0),
            sprites["ring"].clone().set_position(5, 3),
            sprites["ring"].clone().set_position(5, 6),
        ],
        5,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Cq01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Cq01UI(len(levels))
        super().__init__(
            "cq01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._goal = self.current_level.get_sprites_by_tag("goal")[0]
        self._rings = {(r.x, r.y) for r in self.current_level.get_sprites_by_tag("ring")}
        self._visited: set[tuple[int, int]] = set()
        self._ui.update(len(self._rings), self.level_index)

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
        pos = (nx, ny)
        if pos in self._rings:
            self._visited.add(pos)
        self._ui.update(len(self._rings - self._visited), self.level_index)

        if self._rings <= self._visited and self._player.x == self._goal.x and self._player.y == self._goal.y:
            self.next_level()

        self.complete_action()
