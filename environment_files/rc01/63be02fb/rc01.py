"""Recall pad: ACTION5 once per level snaps you back to your start cell."""

from arcengine import (
    ARCBaseGame,
    Camera,
    GameAction,
    GameState,
    Level,
    RenderableUserDisplay,
    Sprite,
)


def _rp(frame, h, w, x, y, c):
    if 0 <= x < w and 0 <= y < h:
        frame[y, x] = c


def _r_dots(frame, h, w, li, n, y0=0):
    for i in range(min(n, 14)):
        cx = 1 + i * 2
        if cx >= w:
            break
        c = 14 if i < li else (11 if i == li else 3)
        _rp(frame, h, w, cx, y0, c)


def _r_bar(frame, h, w, game_over, win):
    if not (game_over or win):
        return
    r = h - 3
    if r < 0:
        return
    c = 14 if win else 8
    for x in range(min(w, 16)):
        _rp(frame, h, w, x, r, c)


class Rc01UI(RenderableUserDisplay):
    def __init__(self, left: int, level_index: int = 0, num_levels: int = 5) -> None:
        self._left = left
        self._level_index = level_index
        self._num_levels = num_levels
        self._recall_flash = 0
        self._end: GameState | None = None

    def update(
        self,
        left: int,
        *,
        level_index: int | None = None,
        num_levels: int | None = None,
        recall_pulse: bool = False,
        end: GameState | None = None,
    ) -> None:
        self._left = left
        if level_index is not None:
            self._level_index = level_index
        if num_levels is not None:
            self._num_levels = num_levels
        if recall_pulse:
            self._recall_flash = 10
        if end is not None:
            self._end = end

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        _r_dots(frame, h, w, self._level_index, self._num_levels, 0)
        rf = self._recall_flash > 0
        if rf:
            self._recall_flash -= 1
        for i in range(3):
            c = 11 if self._left > 0 else 2
            if rf:
                c = 15
            _rp(frame, h, w, 28 + i, h - 2, c)
        go = self._end == GameState.GAME_OVER
        win = self._end == GameState.WIN
        _r_bar(frame, h, w, go, win)
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


def mk(sl: list, d: int) -> Level:
    return Level(sprites=sl, grid_size=(10, 10), data={"difficulty": d})


levels = [
    mk(
        [
            sprites["player"].clone().set_position(0, 5),
            sprites["goal"].clone().set_position(9, 5),
        ],
        1,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["goal"].clone().set_position(8, 8),
        ],
        2,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["goal"].clone().set_position(9, 9),
            sprites["wall"].clone().set_position(5, 4),
            sprites["wall"].clone().set_position(5, 5),
            sprites["wall"].clone().set_position(5, 6),
        ],
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(2, 5),
            sprites["goal"].clone().set_position(7, 5),
        ],
        4,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 9),
            sprites["goal"].clone().set_position(9, 0),
        ],
        5,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Rc01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Rc01UI(1, 0, len(levels))
        super().__init__(
            "rc01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 5],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._goal = self.current_level.get_sprites_by_tag("goal")[0]
        self._mx = self._player.x
        self._my = self._player.y
        self._recalls = 1
        self._ui.update(
            self._recalls,
            level_index=self.level_index,
            num_levels=len(self._levels),
            end=self._state,
        )

    def step(self) -> None:
        if self.action.id.value == 5:
            if self._recalls > 0:
                self._recalls = 0
                self._player.set_position(self._mx, self._my)
                self._ui.update(
                    self._recalls,
                    recall_pulse=True,
                    end=self._state,
                )
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

        self._player.set_position(nx, ny)

        if self._player.x == self._goal.x and self._player.y == self._goal.y:
            self.next_level()

        self._ui.update(self._recalls, end=self._state)
        self.complete_action()
