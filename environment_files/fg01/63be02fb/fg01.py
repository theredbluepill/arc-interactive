"""Fog of war: only sprites within Chebyshev radius r of the player stay visible."""

from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Fg01UI(RenderableUserDisplay):
    def __init__(self, r: int) -> None:
        self._r = r

    def update(self, r: int) -> None:
        self._r = r

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, _w = frame.shape
        for i in range(min(self._r + 1, 8)):
            frame[h - 2, 1 + i] = 10
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


def mk(sl: list, d: int, r: int) -> Level:
    return Level(sprites=sl, grid_size=(10, 10), data={"difficulty": d, "fog_r": r})


levels = [
    mk(
        [
            sprites["player"].clone().set_position(1, 5),
            sprites["goal"].clone().set_position(4, 5),
        ],
        1,
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["goal"].clone().set_position(9, 9),
            sprites["wall"].clone().set_position(5, 5),
        ],
        2,
        2,
    ),
    mk(
        [
            sprites["player"].clone().set_position(2, 2),
            sprites["goal"].clone().set_position(7, 7),
        ]
        + [sprites["wall"].clone().set_position(4, y) for y in range(10) if y != 5],
        3,
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["goal"].clone().set_position(8, 8),
        ],
        4,
        2,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 9),
            sprites["goal"].clone().set_position(9, 0),
        ],
        5,
        3,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Fg01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Fg01UI(3)
        super().__init__(
            "fg01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._goal = self.current_level.get_sprites_by_tag("goal")[0]
        self._r = int(level.get_data("fog_r") or 3)
        self._ui.update(self._r)
        self._apply_fog()

    def _apply_fog(self) -> None:
        px, py = self._player.x, self._player.y
        for s in self.current_level._sprites:
            if s is self._player:
                s.set_visible(True)
                continue
            d = max(abs(s.x - px), abs(s.y - py))
            s.set_visible(d <= self._r)

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
        self._apply_fog()

        if self._player.x == self._goal.x and self._player.y == self._goal.y:
            self.next_level()

        self.complete_action()
