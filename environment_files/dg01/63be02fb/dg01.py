"""Dig mud: ACTION5 removes one orth-adjacent mud tile (budget); reach the goal."""

from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Dg01UI(RenderableUserDisplay):
    def __init__(self, digs: int) -> None:
        self._digs = digs
        self._reject_frames = 0

    def update(self, digs: int) -> None:
        self._digs = digs

    def flash_reject(self) -> None:
        self._reject_frames = 3

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for i in range(min(self._digs, 10)):
            frame[h - 2, 1 + i] = 12
        if self._reject_frames > 0:
            frame[2, min(3, w - 1)] = 11
            self._reject_frames -= 1
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
    "mud": Sprite(
        pixels=[[2]],
        name="mud",
        visible=True,
        collidable=True,
        tags=["mud"],
    ),
}


def mk(sl: list, d: int, budget: int) -> Level:
    return Level(sprites=sl, grid_size=(10, 10), data={"difficulty": d, "dig_budget": budget})


levels = [
    mk(
        [
            sprites["player"].clone().set_position(1, 5),
            sprites["mud"].clone().set_position(4, 5),
            sprites["mud"].clone().set_position(5, 5),
            sprites["mud"].clone().set_position(6, 5),
            sprites["goal"].clone().set_position(8, 5),
        ],
        1,
        5,
    ),
    mk(
        [sprites["player"].clone().set_position(0, 5)]
        + [sprites["mud"].clone().set_position(2, y) for y in range(3, 8)]
        + [sprites["goal"].clone().set_position(9, 5)],
        2,
        6,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["goal"].clone().set_position(8, 8),
        ]
        + [sprites["mud"].clone().set_position(x, 5) for x in range(3, 7)],
        3,
        5,
    ),
    mk(
        [
            sprites["player"].clone().set_position(2, 2),
            sprites["goal"].clone().set_position(7, 7),
            sprites["wall"].clone().set_position(4, 4),
            sprites["wall"].clone().set_position(5, 5),
        ]
        + [sprites["mud"].clone().set_position(4, 5), sprites["mud"].clone().set_position(5, 4)],
        4,
        4,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["goal"].clone().set_position(9, 9),
        ]
        + [sprites["mud"].clone().set_position(i, i) for i in range(2, 8)],
        5,
        8,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Dg01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Dg01UI(0)
        super().__init__(
            "dg01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 5],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._goal = self.current_level.get_sprites_by_tag("goal")[0]
        self._budget = int(level.get_data("dig_budget") or 5)
        self._ui.update(self._budget)

    def step(self) -> None:
        if self.action.id.value == 5:
            if self._budget <= 0:
                self.complete_action()
                return
            px, py = self._player.x, self._player.y
            best = None
            for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                nx, ny = px + dx, py + dy
                sp = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
                if sp and "mud" in sp.tags:
                    best = sp
                    break
            if best is None:
                self._ui.flash_reject()
                self.complete_action()
                return
            self.current_level.remove_sprite(best)
            self._budget -= 1
            self._ui.update(self._budget)
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
        if sp and "wall" in sp.tags:
            self.complete_action()
            return
        if sp and "mud" in sp.tags:
            self.complete_action()
            return

        self._player.set_position(nx, ny)
        if self._player.x == self._goal.x and self._player.y == self._goal.y:
            self.next_level()

        self.complete_action()
