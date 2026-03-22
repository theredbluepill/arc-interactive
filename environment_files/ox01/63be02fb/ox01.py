"""XOR hazards: two hazard layers alternate which blocks you each step."""

from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Ox01UI(RenderableUserDisplay):
    def __init__(self, n_levels: int) -> None:
        self._a = True
        self._n_levels = n_levels
        self._li = 0

    def update(self, a: bool, level_index: int | None = None) -> None:
        self._a = a
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
        frame[h - 2, 2] = 8 if self._a else 6
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
    "haz_a": Sprite(
        pixels=[[8]],
        name="haz_a",
        visible=True,
        collidable=True,
        tags=["haz_a"],
    ),
    "haz_b": Sprite(
        pixels=[[6]],
        name="haz_b",
        visible=True,
        collidable=False,
        tags=["haz_b"],
    ),
}


def mk(sl: list, d: int) -> Level:
    return Level(sprites=sl, grid_size=(10, 10), data={"difficulty": d})


levels = [
    mk(
        [
            sprites["player"].clone().set_position(0, 5),
            sprites["goal"].clone().set_position(9, 5),
            sprites["haz_a"].clone().set_position(5, 5),
            sprites["haz_b"].clone().set_position(4, 5),
        ],
        1,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["goal"].clone().set_position(8, 8),
            sprites["haz_a"].clone().set_position(5, 4),
            sprites["haz_b"].clone().set_position(5, 6),
        ],
        2,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["goal"].clone().set_position(9, 9),
            sprites["haz_a"].clone().set_position(3, 3),
            sprites["haz_b"].clone().set_position(6, 6),
        ],
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(2, 5),
            sprites["goal"].clone().set_position(7, 5),
            sprites["haz_a"].clone().set_position(4, 5),
            sprites["haz_b"].clone().set_position(6, 5),
        ],
        4,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 9),
            sprites["goal"].clone().set_position(9, 0),
            sprites["haz_a"].clone().set_position(5, 5),
            sprites["haz_b"].clone().set_position(5, 4),
        ],
        5,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Ox01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Ox01UI(len(levels))
        super().__init__(
            "ox01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._goal = self.current_level.get_sprites_by_tag("goal")[0]
        self._ha = list(self.current_level.get_sprites_by_tag("haz_a"))
        self._hb = list(self.current_level.get_sprites_by_tag("haz_b"))
        self._active_a = True
        self._sync()

    def _sync(self) -> None:
        for h in self._ha:
            h.set_collidable(self._active_a)
        for h in self._hb:
            h.set_collidable(not self._active_a)
        self._ui.update(self._active_a, self.level_index)

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

        if dx != 0 or dy != 0:
            nx = self._player.x + dx
            ny = self._player.y + dy
            gw, gh = self.current_level.grid_size
            if (0 <= nx < gw and 0 <= ny < gh):
                sp = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
                if not (sp and sp.is_collidable):
                    self._player.set_position(nx, ny)

        self._active_a = not self._active_a
        self._sync()

        sp2 = self.current_level.get_sprite_at(self._player.x, self._player.y, ignore_collidable=True)
        if sp2 and sp2.is_collidable and ("haz_a" in sp2.tags or "haz_b" in sp2.tags):
            self.lose()
            self.complete_action()
            return

        if self._player.x == self._goal.x and self._player.y == self._goal.y:
            self.next_level()

        self.complete_action()
