"""Rotating hazard: a lethal row index advances every N steps; lose if you stand on it when active."""

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


class Rh01UI(RenderableUserDisplay):
    """HUD + lethal row tint on the letterboxed grid (camera 16×16 → 64×64 frame)."""

    _CAM_W = 16
    _CAM_H = 16

    def __init__(self, row: int, level_index: int = 0, num_levels: int = 5) -> None:
        self._row = row
        self._ticks = 0
        self._period = 3
        self._gw = 10
        self._gh = 10
        self._level_index = level_index
        self._num_levels = num_levels
        self._state: GameState | None = None

    def update(
        self,
        row: int,
        *,
        ticks: int = 0,
        period: int = 3,
        grid_size: tuple[int, int] | None = None,
        level_index: int | None = None,
        num_levels: int | None = None,
        state: GameState | None = None,
    ) -> None:
        self._row = row
        self._ticks = ticks
        self._period = max(period, 1)
        if grid_size is not None:
            self._gw, self._gh = grid_size
        if level_index is not None:
            self._level_index = level_index
        if num_levels is not None:
            self._num_levels = num_levels
        if state is not None:
            self._state = state

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        _r_dots(frame, h, w, self._level_index, self._num_levels, 0)
        scale = min(w // self._CAM_W, h // self._CAM_H)
        scale = max(scale, 1)
        x_pad = (w - self._CAM_W * scale) // 2
        y_pad = (h - self._CAM_H * scale) // 2
        gy = self._row % max(self._gh, 1)
        for gx in range(min(self._gw, self._CAM_W)):
            x0 = gx * scale + x_pad
            y0 = gy * scale + y_pad
            for dy in range(scale):
                for dx in range(scale):
                    px, py = x0 + dx, y0 + dy
                    if 0 <= px < w and 0 <= py < h:
                        frame[py, px] = 8
        for i in range(min(self._row + 1, 12)):
            if 18 + i < w:
                frame[h - 2, 18 + i] = 8
        until = self._period - self._ticks
        for i in range(min(max(until, 0), 8)):
            if 1 + i < w:
                frame[h - 3, 1 + i] = 10
        go = self._state == GameState.GAME_OVER
        win = self._state == GameState.WIN
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


def mk(sl: list, d: int, n: int) -> Level:
    return Level(sprites=sl, grid_size=(10, 10), data={"difficulty": d, "period": n})


levels = [
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["goal"].clone().set_position(9, 9),
        ],
        1,
        4,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["goal"].clone().set_position(8, 8),
        ],
        2,
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 5),
            sprites["goal"].clone().set_position(9, 5),
            sprites["wall"].clone().set_position(5, 5),
        ],
        3,
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(2, 2),
            sprites["goal"].clone().set_position(7, 7),
        ],
        4,
        2,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 8),
            sprites["goal"].clone().set_position(9, 1),
        ],
        5,
        3,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Rh01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Rh01UI(0, 0, len(levels))
        super().__init__(
            "rh01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._goal = self.current_level.get_sprites_by_tag("goal")[0]
        self._period = int(level.get_data("period") or 3)
        self._ticks = 0
        self._danger_y = 9
        gw, gh = self.current_level.grid_size
        self._ui.update(
            self._danger_y % max(gw, 1),
            ticks=self._ticks,
            period=self._period,
            grid_size=(gw, gh),
            level_index=self.level_index,
            num_levels=len(self._levels),
            state=self._state,
        )

    def _tick_hazard(self) -> None:
        self._ticks += 1
        if self._ticks >= self._period:
            self._ticks = 0
            _gw, gh = self.current_level.grid_size
            self._danger_y = (self._danger_y + 1) % gh
            gw, gh2 = self.current_level.grid_size
            self._ui.update(
                self._danger_y,
                ticks=self._ticks,
                period=self._period,
                grid_size=(gw, gh2),
                state=self._state,
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

        nx = self._player.x + dx
        ny = self._player.y + dy
        gw, gh = self.current_level.grid_size
        moved = False
        if dx != 0 or dy != 0:
            if (0 <= nx < gw and 0 <= ny < gh):
                sp = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
                if not (sp and "wall" in sp.tags):
                    self._player.set_position(nx, ny)
                    moved = True

        self._tick_hazard()

        if self._player.x == self._goal.x and self._player.y == self._goal.y:
            self.next_level()
            gw, gh = self.current_level.grid_size
            self._ui.update(
                self._danger_y,
                ticks=self._ticks,
                period=self._period,
                grid_size=(gw, gh),
                state=self._state,
            )
            self.complete_action()
            return

        if self._player.y == self._danger_y:
            gw, gh = self.current_level.grid_size
            self._ui.update(
                self._danger_y,
                ticks=self._ticks,
                period=self._period,
                grid_size=(gw, gh),
                state=self._state,
            )
            self.lose()
            self.complete_action()
            return

        gw, gh = self.current_level.grid_size
        self._ui.update(
            self._danger_y,
            ticks=self._ticks,
            period=self._period,
            grid_size=(gw, gh),
            state=self._state,
        )
        self.complete_action()
