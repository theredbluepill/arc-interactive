"""Sand fall: tan sand piles move down after each player step while the cell below is empty; distinct layouts from av01 (gray rocks)."""

from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Sb01UI(RenderableUserDisplay):
    def __init__(self, n_levels: int) -> None:
        self._d = 1
        self._n_levels = n_levels
        self._li = 0

    def update(self, d: int, level_index: int | None = None) -> None:
        self._d = d
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
        for i in range(min(self._d, 12)):
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
    "sand": Sprite(
        pixels=[[12]],
        name="sand",
        visible=True,
        collidable=True,
        tags=["sand"],
    ),
}


def mk(sl: list, d: int) -> Level:
    return Level(sprites=sl, grid_size=(10, 10), data={"difficulty": d})


levels = [
    mk(
        [
            sprites["player"].clone().set_position(3, 2),
            sprites["goal"].clone().set_position(8, 7),
            sprites["sand"].clone().set_position(6, 1),
        ],
        1,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 6),
            sprites["goal"].clone().set_position(9, 3),
            sprites["sand"].clone().set_position(4, 1),
            sprites["sand"].clone().set_position(7, 2),
        ],
        2,
    ),
    mk(
        [
            sprites["player"].clone().set_position(2, 1),
            sprites["goal"].clone().set_position(7, 8),
            sprites["wall"].clone().set_position(4, 5),
            sprites["wall"].clone().set_position(5, 5),
            sprites["sand"].clone().set_position(5, 2),
        ],
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 4),
            sprites["goal"].clone().set_position(9, 4),
            sprites["sand"].clone().set_position(3, 2),
            sprites["sand"].clone().set_position(6, 2),
        ],
        4,
    ),
    mk(
        [
            sprites["player"].clone().set_position(8, 1),
            sprites["goal"].clone().set_position(1, 8),
            sprites["sand"].clone().set_position(5, 0),
            sprites["sand"].clone().set_position(2, 3),
        ],
        5,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Sb01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Sb01UI(len(levels))
        super().__init__(
            "sb01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._goal = self.current_level.get_sprites_by_tag("goal")[0]
        self._ui.update(int(level.get_data("difficulty") or 1), self.level_index)

    def _blocked(self, x: int, y: int, ignore: Sprite | None = None) -> bool:
        gw, gh = self.current_level.grid_size
        if not (0 <= x < gw and 0 <= y < gh):
            return True
        sp = self.current_level.get_sprite_at(x, y, ignore_collidable=True)
        if sp is ignore:
            return False
        if not sp:
            return False
        if "goal" in sp.tags:
            return False
        return sp.is_collidable

    def _fall_sand(self) -> None:
        changed = True
        while changed:
            changed = False
            for s in list(self.current_level.get_sprites_by_tag("sand")):
                nx, ny = s.x, s.y + 1
                if not self._blocked(nx, ny, ignore=s):
                    s.set_position(nx, ny)
                    changed = True

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
        if sp and "sand" in sp.tags:
            self.complete_action()
            return

        self._player.set_position(nx, ny)
        self._fall_sand()

        for s in self.current_level.get_sprites_by_tag("sand"):
            if s.x == self._player.x and s.y == self._player.y:
                self.lose()
                self.complete_action()
                return

        if self._player.x == self._goal.x and self._player.y == self._goal.y:
            self.next_level()

        self.complete_action()
