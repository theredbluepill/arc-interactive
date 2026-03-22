"""Twin meters: oxygen and heat decay each step; cyan / magenta pads refill; survive T steps per level."""

from arcengine import (
    ARCBaseGame,
    Camera,
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


class Tm01UI(RenderableUserDisplay):
    def __init__(
        self,
        o2: int,
        ht: int,
        left: int,
        level_index: int = 0,
        num_levels: int = 5,
    ) -> None:
        self._o2 = o2
        self._ht = ht
        self._left = left
        self._level_index = level_index
        self._num_levels = num_levels
        self._end: GameState | None = None

    def update(
        self,
        o2: int,
        ht: int,
        left: int,
        *,
        level_index: int | None = None,
        num_levels: int | None = None,
        end: GameState | None = None,
    ) -> None:
        self._o2 = o2
        self._ht = ht
        self._left = left
        if level_index is not None:
            self._level_index = level_index
        if num_levels is not None:
            self._num_levels = num_levels
        if end is not None:
            self._end = end

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        _r_dots(frame, h, w, self._level_index, self._num_levels, 0)
        for i in range(min(self._o2 // 10, 16)):
            frame[2, 2 + i] = 10
        for i in range(min(self._ht // 10, 16)):
            frame[3, 2 + i] = 6
        for i in range(min(self._left, 16)):
            frame[4, 2 + i] = 14
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
    "o2_pad": Sprite(
        pixels=[[10]],
        name="o2_pad",
        visible=True,
        collidable=False,
        tags=["o2_pad"],
    ),
    "heat_pad": Sprite(
        pixels=[[7]],
        name="heat_pad",
        visible=True,
        collidable=False,
        tags=["heat_pad"],
    ),
}


def mk(sl: list, d: int, need: int) -> Level:
    return Level(sprites=sl, grid_size=(10, 10), data={"difficulty": d, "survive": need})


levels = [
    mk(
        [
            sprites["player"].clone().set_position(5, 5),
            sprites["o2_pad"].clone().set_position(2, 5),
            sprites["heat_pad"].clone().set_position(7, 5),
        ],
        1,
        40,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 5),
            sprites["o2_pad"].clone().set_position(5, 2),
            sprites["heat_pad"].clone().set_position(5, 8),
        ],
        2,
        45,
    ),
    mk(
        [
            sprites["player"].clone().set_position(5, 1),
            sprites["o2_pad"].clone().set_position(1, 1),
            sprites["heat_pad"].clone().set_position(8, 8),
        ],
        3,
        50,
    ),
    mk(
        [
            sprites["player"].clone().set_position(3, 5),
            sprites["o2_pad"].clone().set_position(6, 3),
            sprites["heat_pad"].clone().set_position(6, 7),
        ],
        4,
        50,
    ),
    mk(
        [
            sprites["player"].clone().set_position(5, 5),
            sprites["o2_pad"].clone().set_position(2, 2),
            sprites["heat_pad"].clone().set_position(7, 7),
        ],
        5,
        55,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Tm01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Tm01UI(100, 100, 40, 0, len(levels))
        super().__init__(
            "tm01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._need = int(level.get_data("survive") or 50)
        self._left = self._need
        self._o2 = 100
        self._heat = 100
        self._ui.update(
            self._o2,
            self._heat,
            self._left,
            level_index=self.level_index,
            num_levels=len(self._levels),
            end=self._state,
        )

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
            if 0 <= nx < gw and 0 <= ny < gh:
                self._player.set_position(nx, ny)

        self._o2 = max(0, self._o2 - 3)
        self._heat = max(0, self._heat - 3)

        sp = self.current_level.get_sprite_at(self._player.x, self._player.y, ignore_collidable=True)
        if sp and "o2_pad" in sp.tags:
            self._o2 = 100
        if sp and "heat_pad" in sp.tags:
            self._heat = 100

        self._left -= 1
        self._ui.update(
            self._o2,
            self._heat,
            self._left,
            level_index=self.level_index,
            num_levels=len(self._levels),
            end=self._state,
        )

        if self._o2 <= 0 or self._heat <= 0:
            self.lose()
            self._ui.update(
                self._o2,
                self._heat,
                self._left,
                end=self._state,
            )
            self.complete_action()
            return

        if self._left <= 0:
            self.next_level()

        self.complete_action()
