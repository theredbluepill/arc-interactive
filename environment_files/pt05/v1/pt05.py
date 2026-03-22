"""pt05: click row header (x=0) to cycle that row’s colors left; match key."""

from __future__ import annotations

import numpy as np
from arcengine import (
    ARCBaseGame,
    Camera,
    GameAction,
    GameState,
    Level,
    RenderableUserDisplay,
    Sprite,
)

BG, PAD = 5, 4


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


def _r_ticks(frame, h, w, n, y=None):
    row = (h - 1) if y is None else y
    for i in range(max(0, min(n, 8))):
        _rp(frame, h, w, 1 + i, row, 11)


def _r_bar(frame, h, w, game_over, win):
    if not (game_over or win):
        return
    r = h - 3
    if r < 0:
        return
    c = 14 if win else 8
    for x in range(min(w, 16)):
        _rp(frame, h, w, x, r, c)

W, H = 8, 8
CAM = 16
HEADER_X = 0


def pix(c: int) -> Sprite:
    return Sprite(
        pixels=[[c]],
        name="px",
        visible=True,
        collidable=False,
        tags=["rowcell"],
    )


class Pt05UI(RenderableUserDisplay):
    def __init__(self, level_index: int = 0, num_levels: int = 1, ticks: int = 1) -> None:
        self._level_index = level_index
        self._num_levels = num_levels
        self._ticks = ticks
        self._state = None

    def update(
        self,
        *,
        level_index: int | None = None,
        num_levels: int | None = None,
        ticks: int | None = None,
        state=None,
    ) -> None:
        if level_index is not None:
            self._level_index = level_index
        if num_levels is not None:
            self._num_levels = num_levels
        if ticks is not None:
            self._ticks = ticks
        if state is not None:
            self._state = state

    def render_interface(self, frame):
        import numpy as np


        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        _r_dots(frame, h, w, self._level_index, self._num_levels, 0)
        _r_ticks(frame, h, w, self._ticks)
        go = self._state == GameState.GAME_OVER
        win = self._state == GameState.WIN
        _r_bar(frame, h, w, go, win)
        return frame


def mk_row(rows: list[list[int]], targ: list[list[int]], diff: int) -> Level:
    sl: list[Sprite] = []
    for y in range(1, H):
        sl.append(
            Sprite(
                pixels=[[11]],
                name="hdr",
                visible=True,
                collidable=False,
                tags=["header"],
            ).clone().set_position(HEADER_X, y)
        )
        for x in range(1, W):
            sl.append(pix(rows[y - 1][x - 1]).clone().set_position(x, y))
    return Level(
        sprites=sl,
        grid_size=(W, H),
        data={
            "difficulty": diff,
            "target": [list(r) for r in targ],
        },
    )


def row(vals: list[int]) -> list[int]:
    return vals + [3] * (7 - len(vals))


levels = [
    mk_row(
        [row([9, 11, 14]), row([3, 3, 3]), row([3, 3, 3]), row([3, 3, 3]), row([3, 3, 3]), row([3, 3, 3]), row([3, 3, 3])],
        [row([11, 9, 14]), row([3, 3, 3]), row([3, 3, 3]), row([3, 3, 3]), row([3, 3, 3]), row([3, 3, 3]), row([3, 3, 3])],
        1,
    ),
    mk_row(
        [
            row([10, 10, 10]),
            row([8, 8, 8]),
            row([3, 3, 3]),
            row([3, 3, 3]),
            row([3, 3, 3]),
            row([3, 3, 3]),
            row([3, 3, 3]),
        ],
        [
            row([10, 10, 10]),
            row([8, 8, 8]),
            row([3, 3, 3]),
            row([3, 3, 3]),
            row([3, 3, 3]),
            row([3, 3, 3]),
            row([3, 3, 3]),
        ],
        2,
    ),
    mk_row(
        [
            row([9, 11, 14, 10]),
            row([11, 14, 10, 9]),
            row([3, 3, 3, 3]),
            row([3, 3, 3, 3]),
            row([3, 3, 3, 3]),
            row([3, 3, 3, 3]),
            row([3, 3, 3, 3]),
        ],
        [
            row([14, 10, 9, 11]),
            row([10, 9, 11, 14]),
            row([3, 3, 3, 3]),
            row([3, 3, 3, 3]),
            row([3, 3, 3, 3]),
            row([3, 3, 3, 3]),
            row([3, 3, 3, 3]),
        ],
        3,
    ),
    mk_row(
        [
            row([12, 3, 3, 3]),
            row([3, 12, 3, 3]),
            row([3, 3, 12, 3]),
            row([3, 3, 3, 3]),
            row([3, 3, 3, 3]),
            row([3, 3, 3, 3]),
            row([3, 3, 3, 3]),
        ],
        [
            row([3, 3, 12, 3]),
            row([3, 12, 3, 3]),
            row([12, 3, 3, 3]),
            row([3, 3, 3, 3]),
            row([3, 3, 3, 3]),
            row([3, 3, 3, 3]),
            row([3, 3, 3, 3]),
        ],
        4,
    ),
    mk_row(
        [
            row([9, 9, 11, 11]),
            row([11, 11, 9, 9]),
            row([3, 3, 3, 3]),
            row([3, 3, 3, 3]),
            row([3, 3, 3, 3]),
            row([3, 3, 3, 3]),
            row([3, 3, 3, 3]),
        ],
        [
            row([11, 11, 9, 9]),
            row([9, 9, 11, 11]),
            row([3, 3, 3, 3]),
            row([3, 3, 3, 3]),
            row([3, 3, 3, 3]),
            row([3, 3, 3, 3]),
            row([3, 3, 3, 3]),
        ],
        5,
    ),
    mk_row(
        [
            row([10, 8, 14]),
            row([8, 14, 10]),
            row([14, 10, 8]),
            row([3, 3, 3]),
            row([3, 3, 3]),
            row([3, 3, 3]),
            row([3, 3, 3]),
        ],
        [
            row([14, 10, 8]),
            row([10, 8, 14]),
            row([8, 14, 10]),
            row([3, 3, 3]),
            row([3, 3, 3]),
            row([3, 3, 3]),
            row([3, 3, 3]),
        ],
        6,
    ),
    mk_row(
        [
            row([9, 11, 14, 10, 8]),
            row([3, 3, 3, 3, 3]),
            row([3, 3, 3, 3, 3]),
            row([3, 3, 3, 3, 3]),
            row([3, 3, 3, 3, 3]),
            row([3, 3, 3, 3, 3]),
            row([3, 3, 3, 3, 3]),
        ],
        [
            row([8, 10, 14, 11, 9]),
            row([3, 3, 3, 3, 3]),
            row([3, 3, 3, 3, 3]),
            row([3, 3, 3, 3, 3]),
            row([3, 3, 3, 3, 3]),
            row([3, 3, 3, 3, 3]),
            row([3, 3, 3, 3, 3]),
        ],
        7,
    ),
]


class Pt05(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Pt05UI(0, len(levels), 1)
        super().__init__(
            "pt05",
            levels,
            Camera(0, 0, CAM, CAM, BG, PAD, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 6],
        )


    def _sync_ui(self) -> None:
        self._ui.update(
            level_index=self.level_index,
            num_levels=len(levels),
            ticks=1,
            state=self._state,
        )

    def on_set_level(self, level: Level) -> None:
        self._target = level.get_data("target")
        self._by_pos: dict[tuple[int, int], Sprite] = {}
        for sp in self.current_level.get_sprites_by_tag("rowcell"):
            self._by_pos[(sp.x, sp.y)] = sp
        self._headers: dict[int, Sprite] = {}
        for sp in self.current_level.get_sprites_by_tag("header"):
            self._headers[sp.y] = sp

    def _row_vals(self, y: int) -> list[int]:
        return [int(self._by_pos[(x, y)].pixels[0, 0]) for x in range(1, W)]

    def _cycle_row(self, y: int) -> None:
        vals = self._row_vals(y)
        if not vals:
            return
        nv = vals[1:] + [vals[0]]
        for x in range(1, W):
            self._by_pos[(x, y)].pixels = np.array([[nv[x - 1]]], dtype=np.int8)

    def _win(self) -> bool:
        for yi, row in enumerate(self._target, start=1):
            for xi in range(1, W):
                if int(self._by_pos[(xi, yi)].pixels[0, 0]) != row[xi - 1]:
                    return False
        return True

    def step(self) -> None:
        if self.action.id == GameAction.ACTION6:
            c = self.camera.display_to_grid(
                self.action.data.get("x", 0), self.action.data.get("y", 0)
            )
            if c:
                gx, gy = c
                if gx == HEADER_X and gy in self._headers:
                    self._cycle_row(gy)
                    if self._win():
                        self.next_level()
            self._sync_ui()
            self.complete_action()
            return
        self._sync_ui()
        self.complete_action()
