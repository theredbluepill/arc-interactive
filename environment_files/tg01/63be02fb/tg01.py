"""Tag evasion: a chaser moves toward you every other step; reach the safe zone or survive the step budget."""

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


class Tg01UI(RenderableUserDisplay):
    def __init__(self, left: int, num_levels: int) -> None:
        self._left = left
        self._num_levels = num_levels
        self._level_index = 0
        self._tick = 0
        self._gs: GameState | None = None

    def update(
        self,
        left: int,
        *,
        level_index: int | None = None,
        tick: int | None = None,
        gs: GameState | None = None,
    ) -> None:
        self._left = left
        if level_index is not None:
            self._level_index = level_index
        if tick is not None:
            self._tick = tick
        if gs is not None:
            self._gs = gs

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        _r_dots(frame, h, w, self._level_index, self._num_levels, 0)
        chaser_moves = self._tick % 2 == 0
        _rp(frame, h, w, w - 2, 1, 14 if chaser_moves else 3)
        _rp(frame, h, w, w - 5, 1, 14)
        _rp(frame, h, w, w - 4, 1, 8)
        for i in range(min(self._left, 15)):
            frame[h - 2, 1 + i] = 8
        go = self._gs == GameState.GAME_OVER
        win = self._gs == GameState.WIN
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
    "chaser": Sprite(
        pixels=[[8]],
        name="chaser",
        visible=True,
        collidable=False,
        tags=["chaser"],
    ),
    "safe": Sprite(
        pixels=[[14]],
        name="safe",
        visible=True,
        collidable=False,
        tags=["safe_zone"],
    ),
    "wall": Sprite(
        pixels=[[3]],
        name="wall",
        visible=True,
        collidable=True,
        tags=["wall"],
    ),
}


def mk(sl, survive: int, d: int):
    return Level(
        sprites=sl,
        grid_size=(12, 12),
        data={"difficulty": d, "survive_steps": survive},
    )


levels = [
    mk(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["chaser"].clone().set_position(10, 10),
            sprites["safe"].clone().set_position(0, 11),
        ],
        40,
        1,
    ),
    mk(
        [
            sprites["player"].clone().set_position(2, 5),
            sprites["chaser"].clone().set_position(11, 5),
            sprites["safe"].clone().set_position(0, 0),
        ],
        35,
        2,
    ),
    mk(
        [
            sprites["player"].clone().set_position(5, 5),
            sprites["chaser"].clone().set_position(11, 11),
            sprites["safe"].clone().set_position(1, 1),
        ]
        + [sprites["wall"].clone().set_position(6, y) for y in range(12) if y != 5],
        45,
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["chaser"].clone().set_position(11, 0),
            sprites["safe"].clone().set_position(11, 11),
        ],
        50,
        4,
    ),
    mk(
        [
            sprites["player"].clone().set_position(6, 6),
            sprites["chaser"].clone().set_position(0, 0),
            sprites["safe"].clone().set_position(11, 6),
        ],
        30,
        5,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4

_NUM_LEVELS = len(levels)


class Tg01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Tg01UI(0, _NUM_LEVELS)
        super().__init__(
            "tg01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._chaser = self.current_level.get_sprites_by_tag("chaser")[0]
        self._tick = 0
        self._left = int(self.current_level.get_data("survive_steps") or 40)
        self._ui.update(
            self._left,
            level_index=self.level_index,
            tick=self._tick,
            gs=self._state,
        )

    def _chaser_step(self) -> None:
        cx, cy = self._chaser.x, self._chaser.y
        px, py = self._player.x, self._player.y
        dx = 0 if cx == px else (1 if cx < px else -1)
        dy = 0 if cy == py else (1 if cy < py else -1)
        if abs(px - cx) >= abs(py - cy):
            nx, ny = cx + dx, cy
        else:
            nx, ny = cx, cy + dy
        gw, gh = self.current_level.grid_size
        if 0 <= nx < gw and 0 <= ny < gh:
            sp = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
            if not sp or "wall" not in sp.tags:
                self._chaser.set_position(nx, ny)

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
        else:
            self.complete_action()
            return

        nx, ny = self._player.x + dx, self._player.y + dy
        gw, gh = self.current_level.grid_size
        if 0 <= nx < gw and 0 <= ny < gh:
            sp = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
            if not sp or not sp.is_collidable:
                self._player.set_position(nx, ny)

        self._tick += 1
        if self._tick % 2 == 0:
            self._chaser_step()

        if self._player.x == self._chaser.x and self._player.y == self._chaser.y:
            self.lose()
            self._ui.update(
                max(0, self._left),
                level_index=self.level_index,
                tick=self._tick,
                gs=self._state,
            )
            self.complete_action()
            return

        sz = self.current_level.get_sprites_by_tag("safe_zone")
        if sz and self._player.x == sz[0].x and self._player.y == sz[0].y:
            self.next_level()
            self._ui.update(
                max(0, self._left),
                level_index=self.level_index,
                tick=self._tick,
                gs=self._state,
            )
            self.complete_action()
            return

        self._left -= 1
        self._ui.update(
            max(0, self._left),
            level_index=self.level_index,
            tick=self._tick,
            gs=self._state,
        )
        if self._left <= 0:
            self.next_level()

        self.complete_action()
