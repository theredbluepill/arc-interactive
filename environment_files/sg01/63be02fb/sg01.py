"""Signal lock: sweep cursor advances every step; ACTION5 in the green window scores (miss shrinks window)."""

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
    for i in range(min(n, 6)):
        cx = 1 + i
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
    for x in range(min(w, 8)):
        _rp(frame, h, w, x, r, c)


class Sg01UI(RenderableUserDisplay):
    def __init__(self, num_levels: int) -> None:
        self._cur = 0
        self._lo = 0
        self._hi = 3
        self._prog = 0
        self._need = 4
        self._cycle = 16
        self._num_levels = num_levels
        self._level_index = 0
        self._gs: GameState | None = None

    def update(
        self,
        cur: int,
        lo: int,
        hi: int,
        prog: int,
        need: int,
        cycle: int,
        *,
        level_index: int | None = None,
        gs: GameState | None = None,
    ) -> None:
        self._cur = cur
        self._lo = lo
        self._hi = hi
        self._prog = prog
        self._need = need
        self._cycle = cycle
        if level_index is not None:
            self._level_index = level_index
        if gs is not None:
            self._gs = gs

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        _r_dots(frame, h, w, self._level_index, self._num_levels, 0)
        bar_len = w - 2
        for i in range(bar_len):
            gi = int(i * self._cycle / max(1, bar_len - 1)) if bar_len > 1 else 0
            c = 5
            if self._lo <= gi <= self._hi:
                c = 14
            frame[1, 1 + i] = c
        cx = 1 + int(self._cur * (bar_len - 1) / max(1, self._cycle - 1))
        cx = min(w - 2, max(1, cx))
        frame[2, cx] = 9
        for i in range(min(self._prog, 10)):
            frame[h - 2, 1 + i] = 11
        go = self._gs == GameState.GAME_OVER
        win = self._gs == GameState.WIN
        _r_bar(frame, h, w, go, win)
        return frame


sprites = {
    "bg": Sprite(
        pixels=[[5]],
        name="bg",
        visible=False,
        collidable=False,
        tags=["decor"],
    ),
}


def mk(cycle: int, win_w: int, need: int, d: int):
    return Level(
        sprites=[sprites["bg"].clone().set_position(0, 0)],
        grid_size=(8, 8),
        data={
            "difficulty": d,
            "cycle": cycle,
            "window": win_w,
            "hits_needed": need,
        },
    )


levels = [
    mk(16, 5, 4, 1),
    mk(20, 4, 5, 2),
    mk(24, 4, 6, 3),
    mk(18, 3, 7, 4),
    mk(22, 3, 8, 5),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4

_NUM_LEVELS = len(levels)


class Sg01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Sg01UI(_NUM_LEVELS)
        super().__init__(
            "sg01",
            levels,
            Camera(0, 0, 8, 8, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 5],
        )

    def on_set_level(self, level: Level) -> None:
        self._cycle = int(self.current_level.get_data("cycle") or 16)
        self._win_w = int(self.current_level.get_data("window") or 3)
        self._need = int(self.current_level.get_data("hits_needed") or 4)
        self._cur = 0
        self._prog = 0
        self._lo = max(0, self._cycle // 2 - self._win_w // 2)
        self._hi = min(self._cycle - 1, self._lo + self._win_w - 1)
        self._sync_ui()

    def _sync_ui(self) -> None:
        self._ui.update(
            self._cur,
            self._lo,
            self._hi,
            self._prog,
            self._need,
            self._cycle,
            level_index=self.level_index,
            gs=self._state,
        )

    def _in_window(self) -> bool:
        return self._lo <= self._cur <= self._hi

    def step(self) -> None:
        if self.action.id == GameAction.ACTION5:
            if self._in_window():
                self._prog += 1
                if self._prog >= self._need:
                    self.next_level()
                    self._cur = (self._cur + 1) % self._cycle
                    self._sync_ui()
                    self.complete_action()
                    return
            else:
                w = self._hi - self._lo + 1
                w = max(1, w - 1)
                mid = (self._lo + self._hi) // 2
                self._lo = max(0, mid - w // 2)
                self._hi = min(self._cycle - 1, self._lo + w - 1)
            self._cur = (self._cur + 1) % self._cycle
            self._sync_ui()
            self.complete_action()
            return

        self._cur = (self._cur + 1) % self._cycle
        self._sync_ui()
        self.complete_action()
