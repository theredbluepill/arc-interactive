"""Hazard growth: red hazard seeds spread to orthogonal neighbors every M steps."""

from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Hz01UI(RenderableUserDisplay):
    def __init__(self, n_levels: int) -> None:
        self._m = 4
        self._n_levels = n_levels
        self._li = 0

    def update(self, m: int, level_index: int | None = None) -> None:
        self._m = m
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
        for i in range(min(self._m, 10)):
            frame[h - 2, 1 + i] = 8
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
    "hazard": Sprite(
        pixels=[[8]],
        name="hazard",
        visible=True,
        collidable=True,
        tags=["hazard"],
    ),
}


def mk(sl: list, d: int, m: int) -> Level:
    return Level(sprites=sl, grid_size=(10, 10), data={"difficulty": d, "spread_m": m})


levels = [
    mk(
        [
            sprites["player"].clone().set_position(0, 5),
            sprites["goal"].clone().set_position(9, 5),
            sprites["hazard"].clone().set_position(5, 5),
        ],
        1,
        5,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["goal"].clone().set_position(8, 8),
            sprites["hazard"].clone().set_position(5, 5),
        ],
        2,
        4,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["goal"].clone().set_position(9, 9),
            sprites["hazard"].clone().set_position(3, 3),
            sprites["wall"].clone().set_position(5, 5),
        ],
        3,
        4,
    ),
    mk(
        [
            sprites["player"].clone().set_position(2, 5),
            sprites["goal"].clone().set_position(7, 5),
            sprites["hazard"].clone().set_position(5, 2),
        ],
        4,
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 9),
            sprites["goal"].clone().set_position(9, 0),
            sprites["hazard"].clone().set_position(5, 5),
        ],
        5,
        3,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Hz01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Hz01UI(len(levels))
        super().__init__(
            "hz01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._goal = self.current_level.get_sprites_by_tag("goal")[0]
        self._m = int(level.get_data("spread_m") or 4)
        self._ctr = 0
        self._ui.update(self._m, self.level_index)

    def _spread(self) -> None:
        haz = list(self.current_level.get_sprites_by_tag("hazard"))
        gw, gh = self.current_level.grid_size
        new_pos: set[tuple[int, int]] = set()
        for h in haz:
            for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                nx, ny = h.x + dx, h.y + dy
                if not (0 <= nx < gw and 0 <= ny < gh):
                    continue
                sp = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
                if sp and "wall" in sp.tags:
                    continue
                if sp and "hazard" in sp.tags:
                    continue
                if sp and "goal" in sp.tags:
                    continue
                new_pos.add((nx, ny))
        for nx, ny in new_pos:
            self.current_level.add_sprite(sprites["hazard"].clone().set_position(nx, ny))

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
                if not (sp and ("wall" in sp.tags or "hazard" in sp.tags)):
                    self._player.set_position(nx, ny)

        self._ctr += 1
        if self._ctr >= self._m:
            self._ctr = 0
            self._spread()

        sp2 = self.current_level.get_sprite_at(self._player.x, self._player.y, ignore_collidable=True)
        if sp2 and "hazard" in sp2.tags:
            self.lose()
            self.complete_action()
            return

        if self._player.x == self._goal.x and self._player.y == self._goal.y:
            self.next_level()

        self.complete_action()
