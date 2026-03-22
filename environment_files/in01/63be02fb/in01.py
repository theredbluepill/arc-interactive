"""Ink trail: leaving a cell drops permanent blocking ink; you cannot re-enter ink."""

from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class In01UI(RenderableUserDisplay):
    def __init__(self, n: int) -> None:
        self._n = n

    def update(self, n: int) -> None:
        self._n = n

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, _w = frame.shape
        for i in range(min(self._n, 12)):
            frame[h - 2, 1 + i] = 5
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
    "ink": Sprite(
        pixels=[[13]],
        name="ink",
        visible=True,
        collidable=True,
        tags=["ink"],
    ),
}


def mk(sl: list, d: int) -> Level:
    return Level(sprites=sl, grid_size=(10, 10), data={"difficulty": d})


def _row_walls(y: int, xs: range) -> list:
    return [sprites["wall"].clone().set_position(x, y) for x in xs]


# Layouts stress **ink blocks re-entry** (narrow channels, detours)—distinct from pm01 prime-cadence levels.
levels = [
    mk(
        [
            sprites["player"].clone().set_position(0, 5),
            sprites["goal"].clone().set_position(9, 5),
            *_row_walls(4, range(10)),
            *_row_walls(6, range(10)),
        ],
        1,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 3),
            sprites["goal"].clone().set_position(8, 3),
            # Force north detour; ink can trap if you paint the return lane.
            *[sprites["wall"].clone().set_position(x, 3) for x in (3, 4, 5, 6)],
            *[sprites["wall"].clone().set_position(x, 1) for x in range(10)],
            *[sprites["wall"].clone().set_position(x, 5) for x in range(10)],
        ],
        2,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 7),
            sprites["goal"].clone().set_position(8, 2),
            *[sprites["wall"].clone().set_position(0, y) for y in range(10)],
            *[sprites["wall"].clone().set_position(9, y) for y in range(10)],
            *[sprites["wall"].clone().set_position(x, 0) for x in range(10)],
            *[sprites["wall"].clone().set_position(x, 9) for x in range(10)],
            sprites["wall"].clone().set_position(5, 4),
            sprites["wall"].clone().set_position(5, 5),
            sprites["wall"].clone().set_position(5, 6),
        ],
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 4),
            sprites["goal"].clone().set_position(8, 4),
            # Two-lane detour: row-3 barrier with gaps at x=2,7; row-5 solid; ink can block the upper bypass.
            *[sprites["wall"].clone().set_position(x, 3) for x in range(10) if x not in (2, 7)],
            *_row_walls(5, range(10)),
            *[sprites["wall"].clone().set_position(x, 4) for x in (4, 5)],
        ],
        4,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["goal"].clone().set_position(9, 9),
            *[sprites["wall"].clone().set_position(x, 2) for x in (3, 4, 5, 6, 7)],
            *[sprites["wall"].clone().set_position(2, y) for y in (5, 6, 7)],
        ],
        5,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class In01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = In01UI(0)
        super().__init__(
            "in01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._goal = self.current_level.get_sprites_by_tag("goal")[0]
        self._ink_count = 0
        self._ui.update(0)

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
        if sp and ("wall" in sp.tags or "ink" in sp.tags):
            self.complete_action()
            return

        ox, oy = self._player.x, self._player.y
        ink = sprites["ink"].clone().set_position(ox, oy)
        self.current_level.add_sprite(ink)
        self._ink_count += 1
        self._ui.update(self._ink_count)

        self._player.set_position(nx, ny)

        if self._player.x == self._goal.x and self._player.y == self._goal.y:
            self.next_level()

        self.complete_action()
