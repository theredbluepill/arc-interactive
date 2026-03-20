"""Glass floor: glass tiles crack; the third visit to the same glass cell breaks through (lose)."""

from arcengine import (
    ARCBaseGame,
    Camera,
    GameAction,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Gl01UI(RenderableUserDisplay):
    def __init__(self, stress: int) -> None:
        self._stress = stress

    def update(self, stress: int) -> None:
        self._stress = stress

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        c = 10 if self._stress <= 1 else (11 if self._stress == 2 else 8)
        frame[h - 2, 2] = c
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
    "glass": Sprite(
        pixels=[[1]],
        name="glass",
        visible=True,
        collidable=False,
        tags=["glass"],
    ),
}


def mk(sl, d: int):
    return Level(sprites=sl, grid_size=(10, 10), data={"difficulty": d})


levels = [
    mk(
        [
            sprites["player"].clone().set_position(1, 5),
            sprites["glass"].clone().set_position(3, 5),
            sprites["glass"].clone().set_position(4, 5),
            sprites["goal"].clone().set_position(8, 5),
        ],
        1,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 5),
            sprites["goal"].clone().set_position(9, 5),
        ]
        + [sprites["glass"].clone().set_position(x, 5) for x in range(2, 8)],
        2,
    ),
    mk(
        [
            sprites["player"].clone().set_position(2, 2),
            sprites["goal"].clone().set_position(7, 7),
            sprites["glass"].clone().set_position(4, 4),
            sprites["glass"].clone().set_position(5, 5),
            sprites["glass"].clone().set_position(4, 5),
        ],
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["goal"].clone().set_position(8, 8),
        ]
        + [sprites["glass"].clone().set_position(3, y) for y in range(2, 8)]
        + [sprites["glass"].clone().set_position(6, y) for y in range(2, 8)],
        4,
    ),
    mk(
        [
            sprites["player"].clone().set_position(5, 0),
            sprites["goal"].clone().set_position(5, 9),
            sprites["wall"].clone().set_position(4, 4),
            sprites["wall"].clone().set_position(6, 4),
            sprites["glass"].clone().set_position(5, 3),
            sprites["glass"].clone().set_position(5, 5),
            sprites["glass"].clone().set_position(5, 7),
        ],
        5,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Gl01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Gl01UI(0)
        self._visits: dict[tuple[int, int], int] = {}
        super().__init__(
            "gl01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._goal = self.current_level.get_sprites_by_tag("goal")[0]
        self._visits.clear()
        self._ui.update(0)

    def _glass_at(self, x: int, y: int) -> bool:
        sp = self.current_level.get_sprite_at(x, y, ignore_collidable=True)
        return bool(sp and "glass" in sp.tags)

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

        pos = (nx, ny)
        if self._glass_at(nx, ny):
            v = self._visits.get(pos, 0) + 1
            self._visits[pos] = v
            self._ui.update(v)
            if v >= 3:
                self.lose()
                self.complete_action()
                return

        if self._player.x == self._goal.x and self._player.y == self._goal.y:
            self.next_level()

        self.complete_action()
