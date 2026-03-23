"""Infection: red plague spreads to a random orth neighbor every K steps; grab the cyan vaccine, then reach the exit."""

import random

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


class Vi01UI(RenderableUserDisplay):
    def __init__(self, vac: bool, k: int, num_levels: int) -> None:
        self._vac = vac
        self._k = k
        self._num_levels = num_levels
        self._level_index = 0
        self._tick = 0
        self._gs: GameState | None = None

    def update(
        self,
        vac: bool,
        k: int,
        *,
        level_index: int | None = None,
        tick: int | None = None,
        gs: GameState | None = None,
    ) -> None:
        self._vac = vac
        self._k = k
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
        frame[h - 2, 2] = 10 if self._vac else 5
        km = max(1, self._k)
        rem = (km - (self._tick % km)) % km
        if rem == 0:
            rem = km
        frame[h - 2, 3] = 8 if rem <= 1 else 11
        for i in range(min(rem, 6)):
            _rp(frame, h, w, 5 + i, h - 2, 12)
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
    "vaccine": Sprite(
        pixels=[[10]],
        name="vaccine",
        visible=True,
        collidable=False,
        tags=["vaccine"],
    ),
    "plague": Sprite(
        pixels=[[8]],
        name="plague",
        visible=True,
        collidable=True,
        tags=["plague"],
    ),
}


def mk(sl, d: int, spread_every: int):
    return Level(
        sprites=sl,
        grid_size=(12, 12),
        data={"difficulty": d, "spread_every": spread_every},
    )


levels = [
    mk(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["vaccine"].clone().set_position(3, 3),
            sprites["goal"].clone().set_position(10, 10),
            sprites["plague"].clone().set_position(8, 8),
        ],
        1,
        4,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["vaccine"].clone().set_position(2, 10),
            sprites["goal"].clone().set_position(11, 0),
            sprites["plague"].clone().set_position(6, 6),
        ],
        2,
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 6),
            sprites["vaccine"].clone().set_position(6, 1),
            sprites["goal"].clone().set_position(10, 6),
            sprites["plague"].clone().set_position(6, 10),
        ],
        3,
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 6),
            sprites["vaccine"].clone().set_position(6, 0),
            sprites["goal"].clone().set_position(11, 11),
            sprites["plague"].clone().set_position(3, 3),
            sprites["plague"].clone().set_position(9, 9),
        ],
        4,
        2,
    ),
    mk(
        [
            sprites["player"].clone().set_position(6, 6),
            sprites["vaccine"].clone().set_position(1, 1),
            sprites["goal"].clone().set_position(10, 10),
            sprites["plague"].clone().set_position(11, 0),
            sprites["plague"].clone().set_position(0, 11),
        ],
        5,
        2,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4

_NUM_LEVELS = len(levels)


class Vi01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Vi01UI(False, 99, _NUM_LEVELS)
        self._tick = 0
        super().__init__(
            "vi01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._goal = self.current_level.get_sprites_by_tag("goal")[0]
        self._vaccinated = False
        self._tick = 0
        k = int(self.current_level.get_data("spread_every") or 3)
        self._ui.update(
            self._vaccinated,
            k,
            level_index=self.level_index,
            tick=self._tick,
            gs=self._state,
        )

    def _spread_plague(self) -> None:
        pl = [s for s in self.current_level.get_sprites_by_tag("plague")]
        if not pl:
            return
        src = random.choice(pl)
        opts = [(0, -1), (0, 1), (-1, 0), (1, 0)]
        random.shuffle(opts)
        gw, gh = self.current_level.grid_size
        for dx, dy in opts:
            nx, ny = src.x + dx, src.y + dy
            if not (0 <= nx < gw and 0 <= ny < gh):
                continue
            sp = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
            if sp and ("wall" in sp.tags or "plague" in sp.tags):
                continue
            if sp and "goal" in sp.tags:
                continue
            self.current_level.add_sprite(
                sprites["plague"].clone().set_position(nx, ny)
            )
            return

    def step(self) -> None:
        k = int(self.current_level.get_data("spread_every") or 3)
        self._tick += 1
        if self._tick % k == 0:
            self._spread_plague()

        dx = dy = 0
        if self.action.id == GameAction.ACTION1:
            dy = -1
        elif self.action.id == GameAction.ACTION2:
            dy = 1
        elif self.action.id == GameAction.ACTION3:
            dx = -1
        elif self.action.id == GameAction.ACTION4:
            dx = 1
        else:
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
        if sp and "plague" in sp.tags:
            if not self._vaccinated:
                self.lose()
                self._ui.update(
                    self._vaccinated,
                    k,
                    level_index=self.level_index,
                    tick=self._tick,
                    gs=self._state,
                )
                self.complete_action()
                return

        if not sp or not sp.is_collidable or ("plague" in sp.tags and self._vaccinated):
            self._player.set_position(nx, ny)

        sp2 = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
        if sp2 and "vaccine" in sp2.tags:
            self.current_level.remove_sprite(sp2)
            self._vaccinated = True
            self._ui.update(
                True,
                k,
                level_index=self.level_index,
                tick=self._tick,
                gs=self._state,
            )

        if self._player.x == self._goal.x and self._player.y == self._goal.y:
            if not self._vaccinated:
                self.complete_action()
                return
            self.next_level()

        self._ui.update(
            self._vaccinated,
            k,
            level_index=self.level_index,
            tick=self._tick,
            gs=self._state,
        )
        self.complete_action()
