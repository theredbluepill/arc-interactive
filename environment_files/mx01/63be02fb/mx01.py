"""Maze melt: ACTION5 removes one orthogonally adjacent wall (budgeted). Reach the goal."""

from arcengine import (
    ARCBaseGame,
    Camera,
    GameAction,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Mx01UI(RenderableUserDisplay):
    def __init__(self, melts: int) -> None:
        self._melts = melts

    def update(self, melts: int) -> None:
        self._melts = melts

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for i in range(min(self._melts, 12)):
            frame[h - 2, 1 + i] = 11
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


def mk(sl, melts: int, d: int):
    return Level(
        sprites=sl,
        grid_size=(10, 10),
        data={"difficulty": d, "melt_budget": melts},
    )


levels = [
    mk(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["goal"].clone().set_position(8, 8),
        ]
        + [sprites["wall"].clone().set_position(5, y) for y in range(10) if y != 4],
        2,
        1,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["goal"].clone().set_position(9, 9),
        ]
        + [sprites["wall"].clone().set_position(x, 5) for x in range(10) if x != 5],
        1,
        2,
    ),
    mk(
        [
            sprites["player"].clone().set_position(2, 2),
            sprites["goal"].clone().set_position(7, 7),
        ]
        + [sprites["wall"].clone().set_position(4, y) for y in range(10) if y != 3]
        + [sprites["wall"].clone().set_position(6, y) for y in range(10) if y != 6],
        3,
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 5),
            sprites["goal"].clone().set_position(9, 5),
        ]
        + [sprites["wall"].clone().set_position(x, 4) for x in range(10)]
        + [sprites["wall"].clone().set_position(x, 6) for x in range(10)],
        2,
        4,
    ),
    mk(
        [
            sprites["player"].clone().set_position(9, 9),
            sprites["goal"].clone().set_position(0, 0),
        ]
        + [sprites["wall"].clone().set_position(x, x) for x in range(10) if x not in (0, 9)],
        4,
        5,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Mx01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Mx01UI(0)
        super().__init__(
            "mx01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 5],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._goal = self.current_level.get_sprites_by_tag("goal")[0]
        self._left = int(self.current_level.get_data("melt_budget") or 3)
        self._ui.update(self._left)

    def step(self) -> None:
        aid = self.action.id

        if aid == GameAction.ACTION5:
            if self._left <= 0:
                self.complete_action()
                return
            px, py = self._player.x, self._player.y
            best = None
            for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                nx, ny = px + dx, py + dy
                sp = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
                if sp and "wall" in sp.tags:
                    best = sp
                    break
            if best:
                self.current_level.remove_sprite(best)
                self._left -= 1
                self._ui.update(self._left)
            self.complete_action()
            return

        dx = dy = 0
        if aid == GameAction.ACTION1:
            dy = -1
        elif aid == GameAction.ACTION2:
            dy = 1
        elif aid == GameAction.ACTION3:
            dx = -1
        elif aid == GameAction.ACTION4:
            dx = 1
        else:
            self.complete_action()
            return

        nx, ny = self._player.x + dx, self._player.y + dy
        gw, gh = self.current_level.grid_size
        if 0 <= nx < gw and 0 <= ny < gh:
            sp = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
            if not sp or not sp.is_collidable:
                self._player.set_position(nx, ny)

        if self._player.x == self._goal.x and self._player.y == self._goal.y:
            self.next_level()

        self.complete_action()
