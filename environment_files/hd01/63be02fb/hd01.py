"""Heat front: a deadly band advances from the north every `heat_interval` steps. ACTION5 on a cyan station grants brief immunity. Reach the south goal."""

from __future__ import annotations

from arcengine import (
    ARCBaseGame,
    Camera,
    GameAction,
    GameState,
    Level,
    RenderableUserDisplay,
    Sprite,
)

BACKGROUND_COLOR = 5
PADDING_COLOR = 4
CAM = 16
WALL_C = 3
STATION_C = 10


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


class Hd01UI(RenderableUserDisplay):
    def __init__(
        self,
        heat: int,
        immune: int,
        *,
        level_index: int = 0,
        num_levels: int = 5,
        steps_mod: int = 0,
        interval: int = 8,
        gs: GameState | None = None,
    ) -> None:
        self._heat = heat
        self._immune = immune
        self._level_index = level_index
        self._num_levels = num_levels
        self._steps_mod = steps_mod
        self._interval = max(1, interval)
        self._gs = gs

    def update(
        self,
        heat: int,
        immune: int,
        *,
        level_index: int | None = None,
        num_levels: int | None = None,
        steps_mod: int | None = None,
        interval: int | None = None,
        gs: GameState | None = None,
    ) -> None:
        self._heat = heat
        self._immune = immune
        if level_index is not None:
            self._level_index = level_index
        if num_levels is not None:
            self._num_levels = num_levels
        if steps_mod is not None:
            self._steps_mod = steps_mod
        if interval is not None:
            self._interval = max(1, interval)
        if gs is not None:
            self._gs = gs

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        _r_dots(frame, h, w, self._level_index, self._num_levels, 0)
        for i in range(min(self._heat + 1, 14)):
            frame[2 + i, 1] = 8
        frame[h - 2, w - 3] = 14 if self._immune > 0 else 3
        rem = (self._interval - (self._steps_mod % self._interval)) % self._interval
        if rem == 0:
            rem = self._interval
        for i in range(min(rem, 8)):
            _rp(frame, h, w, 2 + i, h - 2, 10)
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
    "goal": Sprite(
        pixels=[[11]],
        name="goal",
        visible=True,
        collidable=False,
        tags=["goal"],
    ),
    "wall": Sprite(
        pixels=[[WALL_C]],
        name="wall",
        visible=True,
        collidable=True,
        tags=["wall"],
    ),
    "station": Sprite(
        pixels=[[STATION_C]],
        name="station",
        visible=True,
        collidable=False,
        tags=["station"],
    ),
}


def mk(
    p: tuple[int, int],
    g: tuple[int, int],
    walls: list[tuple[int, int]],
    stations: list[tuple[int, int]],
    interval: int,
    diff: int,
) -> Level:
    sl = [
        sprites["player"].clone().set_position(*p),
        sprites["goal"].clone().set_position(*g),
    ]
    for wx, wy in walls:
        sl.append(sprites["wall"].clone().set_position(wx, wy))
    for sx, sy in stations:
        sl.append(sprites["station"].clone().set_position(sx, sy))
    return Level(
        sprites=sl,
        grid_size=(CAM, CAM),
        data={"difficulty": diff, "heat_interval": interval},
    )


levels = [
    mk((8, 2), (8, 14), [], [(3, 8), (12, 8)], 8, 1),
    mk((1, 1), (14, 14), [(8, y) for y in range(16) if y != 8], [(5, 5), (11, 11)], 7, 2),
    mk((0, 8), (15, 8), [], [(8, 4), (8, 12)], 6, 3),
    mk((2, 2), (13, 13), [(x, 6) for x in range(16)], [(8, 3)], 5, 4),
    mk((8, 0), (8, 15), [], [(4, 8), (12, 8)], 6, 5),
]

_NUM_LEVELS = len(levels)


class Hd01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Hd01UI(0, 0, num_levels=_NUM_LEVELS)
        super().__init__(
            "hd01",
            levels,
            Camera(0, 0, CAM, CAM, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 5],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._heat_row = -1
        self._steps = 0
        self._immune = 0
        self._interval = int(self.current_level.get_data("heat_interval") or 8)
        self._ui.update(
            self._heat_row,
            self._immune,
            level_index=self.level_index,
            num_levels=_NUM_LEVELS,
            steps_mod=self._steps,
            interval=self._interval,
            gs=self._state,
        )

    def _in_heat(self) -> bool:
        return self._immune <= 0 and self._player.y <= self._heat_row

    def step(self) -> None:
        aid = self.action.id

        if aid == GameAction.ACTION5:
            sp = self.current_level.get_sprite_at(
                self._player.x, self._player.y, ignore_collidable=True
            )
            if sp and "station" in sp.tags:
                self._immune = 12
        elif aid == GameAction.ACTION1:
            dx, dy = 0, -1
        elif aid == GameAction.ACTION2:
            dx, dy = 0, 1
        elif aid == GameAction.ACTION3:
            dx, dy = -1, 0
        elif aid == GameAction.ACTION4:
            dx, dy = 1, 0
        else:
            self.complete_action()
            return

        if aid != GameAction.ACTION5:
            nx, ny = self._player.x + dx, self._player.y + dy
            gw, gh = self.current_level.grid_size
            if 0 <= nx < gw and 0 <= ny < gh:
                sp = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
                if not sp or "wall" not in sp.tags:
                    self._player.set_position(nx, ny)

        self._steps += 1
        if self._steps % self._interval == 0:
            self._heat_row += 1
        self._immune = max(0, self._immune - 1)

        if self._in_heat():
            self.lose()
            self._ui.update(
                self._heat_row,
                self._immune,
                level_index=self.level_index,
                num_levels=_NUM_LEVELS,
                steps_mod=self._steps,
                interval=self._interval,
                gs=self._state,
            )
            self.complete_action()
            return

        gl = self.current_level.get_sprites_by_tag("goal")[0]
        if self._player.x == gl.x and self._player.y == gl.y:
            self.next_level()

        self._ui.update(
            self._heat_row,
            self._immune,
            level_index=self.level_index,
            num_levels=_NUM_LEVELS,
            steps_mod=self._steps,
            interval=self._interval,
            gs=self._state,
        )
        self.complete_action()
