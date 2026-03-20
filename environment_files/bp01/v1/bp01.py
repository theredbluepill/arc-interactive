"""Battery mesh: activate every tower with ACTION5 while standing on it; then reach the goal."""

from arcengine import (
    ARCBaseGame,
    Camera,
    GameAction,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Bp01UI(RenderableUserDisplay):
    def __init__(self, n: int, need: int) -> None:
        self._n = n
        self._need = need

    def update(self, n: int, need: int) -> None:
        self._n = n
        self._need = need

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for i in range(min(self._need, 8)):
            frame[h - 2, 1 + i] = 14 if i < self._n else 5
        return frame


sprites = {
    "player": Sprite(
        pixels=[[9]],
        name="player",
        visible=True,
        collidable=True,
        tags=["player"],
    ),
    "tower": Sprite(
        pixels=[[10]],
        name="tower",
        visible=True,
        collidable=False,
        tags=["tower"],
    ),
    "tower_on": Sprite(
        pixels=[[14]],
        name="tower_on",
        visible=True,
        collidable=False,
        tags=["tower", "powered"],
    ),
    "goal": Sprite(
        pixels=[[11]],
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
    return Level(sprites=sl, grid_size=(14, 14), data={"difficulty": d})


levels = [
    mk(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["tower"].clone().set_position(4, 1),
            sprites["tower"].clone().set_position(7, 4),
            sprites["goal"].clone().set_position(12, 12),
        ],
        1,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["tower"].clone().set_position(3, 3),
            sprites["tower"].clone().set_position(10, 3),
            sprites["tower"].clone().set_position(6, 8),
            sprites["goal"].clone().set_position(13, 13),
        ],
        2,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 7),
            sprites["tower"].clone().set_position(4, 7),
            sprites["tower"].clone().set_position(9, 7),
            sprites["goal"].clone().set_position(7, 1),
        ]
        + [sprites["wall"].clone().set_position(7, y) for y in range(4, 10) if y != 7],
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["tower"].clone().set_position(2, 2),
            sprites["tower"].clone().set_position(11, 2),
            sprites["tower"].clone().set_position(2, 11),
            sprites["tower"].clone().set_position(11, 11),
            sprites["goal"].clone().set_position(7, 7),
        ],
        4,
    ),
    mk(
        [
            sprites["player"].clone().set_position(7, 13),
            sprites["tower"].clone().set_position(3, 5),
            sprites["tower"].clone().set_position(10, 5),
            sprites["tower"].clone().set_position(6, 9),
            sprites["goal"].clone().set_position(7, 0),
        ],
        5,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Bp01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Bp01UI(0, 1)
        super().__init__(
            "bp01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 5],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._need = sum(
            1
            for s in self.current_level.get_sprites_by_tag("tower")
            if "powered" not in s.tags
        )
        self._on = 0
        self._ui.update(0, self._need)

    def step(self) -> None:
        if self.action.id == GameAction.ACTION5:
            sp = self.current_level.get_sprite_at(
                self._player.x, self._player.y, ignore_collidable=True
            )
            if sp and "tower" in sp.tags and "powered" not in sp.tags:
                self.current_level.remove_sprite(sp)
                self.current_level.add_sprite(
                    sprites["tower_on"]
                    .clone()
                    .set_position(self._player.x, self._player.y)
                )
                self._on += 1
                self._ui.update(self._on, self._need)
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
            t = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
            if not t or not t.is_collidable:
                self._player.set_position(nx, ny)

        gl = self.current_level.get_sprites_by_tag("goal")
        if (
            gl
            and self._player.x == gl[0].x
            and self._player.y == gl[0].y
            and self._on >= self._need
        ):
            self.next_level()

        self.complete_action()
