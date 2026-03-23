"""fe02: **vote** with ACTION1–4, **ACTION5** ratifies the leading rule and applies a tiny world tick; survive **N** ratifications."""

from __future__ import annotations

from arcengine import (
    ARCBaseGame,
    Camera,
    GameAction,
    GameState,
    Level,
    RenderableUserDisplay,
)

BG, PAD = 5, 4


def _rp(frame, h, w, x, y, c):
    if 0 <= x < w and 0 <= y < h:
        frame[y, x] = c


def _r_dots(frame, h, w, li, n, y0=0):
    for i in range(min(n, 7)):
        cx = 1 + i * 2
        if cx >= w:
            break
        c = 14 if i < li else (11 if i == li else 3)
        _rp(frame, h, w, cx, y0, c)


def _r_bar(frame, h, w, game_over, win):
    if not (game_over or win):
        return
    r = max(0, h - 2)
    c = 14 if win else 8
    for x in range(min(w, 8)):
        _rp(frame, h, w, x, r, c)


class Fe02UI(RenderableUserDisplay):
    """HUD rows (bottom-up on letterboxed frame): ratification target ticks; leading-rule index; a,b,c; vote tallies; top = level dots."""

    def __init__(self) -> None:
        self._a = self._b = self._c = 5
        self._rat = 0
        self._votes = (0, 0, 0, 0)
        self._need = 5
        self._level_index = 0
        self._num_levels = 7
        self._leading = 0
        self._gs: GameState | None = None

    def sync(
        self,
        a: int,
        b: int,
        c: int,
        rat: int,
        votes: tuple[int, ...],
        *,
        need: int | None = None,
        level_index: int | None = None,
        num_levels: int | None = None,
        leading: int | None = None,
        gs: GameState | None = None,
    ) -> None:
        self._a, self._b, self._c = a, b, c
        self._rat = rat
        self._votes = votes
        if need is not None:
            self._need = need
        if level_index is not None:
            self._level_index = level_index
        if num_levels is not None:
            self._num_levels = num_levels
        if leading is not None:
            self._leading = leading
        if gs is not None:
            self._gs = gs

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        _r_dots(frame, h, w, self._level_index, self._num_levels, 0)
        go = self._gs == GameState.GAME_OVER
        win = self._gs == GameState.WIN
        if not (go or win):
            for i, v in enumerate(self._votes[: min(4, w - 2)]):
                frame[h - 2, 2 + i] = min(15, 5 + min(v, 5))
        frame[h - 3, 2] = min(15, self._a + 5)
        frame[h - 3, 4] = min(15, self._b + 5)
        frame[h - 3, 6] = min(15, self._c + 5)
        for ri in range(4):
            col = 9 if ri == self._leading else 3
            _rp(frame, h, w, 2 + ri, h - 4, col)
        for i in range(min(self._need, 8)):
            tick_col = 14 if i < self._rat else 2
            _rp(frame, h, w, 2 + i, h - 5, tick_col)
        _r_bar(frame, h, w, go, win)
        return frame


# Four policies as (dA, dB, dC)
RULES = (
    (1, -1, 0),
    (-1, 1, 1),
    (0, 1, -1),
    (1, 1, -1),
)

levels = [
    Level(sprites=[], grid_size=(8, 8), data={"need": 5, "difficulty": i + 1})
    for i in range(7)
]
_NUM_LEVELS = len(levels)


class Fe02(ARCBaseGame):
    def __init__(self) -> None:
        self._hud = Fe02UI()
        super().__init__(
            "fe02",
            levels,
            Camera(0, 0, 8, 8, BG, PAD, [self._hud]),
            False,
            1,
            [1, 2, 3, 4, 5],
        )

    def _push_hud(self, leading: int) -> None:
        self._hud.sync(
            self._a,
            self._b,
            self._c,
            self._rat,
            tuple(self._votes),
            need=self._need,
            level_index=self.level_index,
            num_levels=_NUM_LEVELS,
            leading=leading,
            gs=self._state,
        )

    def on_set_level(self, level: Level) -> None:
        self._a = self._b = self._c = 5
        self._rat = 0
        self._votes = [0, 0, 0, 0]
        self._need = int(level.get_data("need"))
        self._push_hud(0)

    def _leading_idx(self) -> int:
        return max(range(4), key=lambda k: (self._votes[k], -k))

    def step(self) -> None:
        aid = self.action.id
        if aid in (GameAction.ACTION1, GameAction.ACTION2, GameAction.ACTION3, GameAction.ACTION4):
            i = aid.value - 1
            self._votes[i] += 1
            self._push_hud(self._leading_idx())
            self.complete_action()
            return
        if aid == GameAction.ACTION5:
            j = max(range(4), key=lambda k: (self._votes[k], -k))
            da, db, dc = RULES[j]
            self._a += da
            self._b += db
            self._c += dc
            self._votes = [0, 0, 0, 0]
            self._rat += 1
            self._push_hud(j)
            if self._a <= 0 or self._b <= 0 or self._c <= 0 or self._a > 9 or self._b > 9 or self._c > 9:
                self.lose()
            elif self._rat >= self._need:
                self.next_level()
            self._push_hud(0 if not any(self._votes) else self._leading_idx())
            self.complete_action()
            return
        self.complete_action()
