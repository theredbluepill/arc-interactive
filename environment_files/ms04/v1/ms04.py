"""ms04: edge mine clues — numbers count mines sharing a unit edge; ACTION6 flags a cell."""

from __future__ import annotations

import numpy as np

from arcengine import ARCBaseGame, Camera, GameAction, GameState, Level, RenderableUserDisplay, Sprite

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

G = 8
CAM = 16
FLAG_COLOR = 13  # maroon — distinct from clue grays and background


class Ms04UI(RenderableUserDisplay):
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

        from arcengine import GameState

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        _r_dots(frame, h, w, self._level_index, self._num_levels, 0)
        _r_ticks(frame, h, w, self._ticks)
        go = self._state == GameState.GAME_OVER
        win = self._state == GameState.WIN
        _r_bar(frame, h, w, go, win)
        return frame


def mk(mines: list[tuple[int, int]], d: int) -> Level:
    sl: list[Sprite] = []
    clue = [[0 for _ in range(G)] for _ in range(G)]
    ms = set(mines)
    for y in range(G):
        for x in range(G):
            if (x, y) in ms:
                continue
            n = 0
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                if (x + dx, y + dy) in ms:
                    n += 1
            clue[y][x] = n
            c = min(15, 5 + n)
            sl.append(
                Sprite(
                    pixels=np.array([[c]], dtype=np.uint8),
                    name="c",
                    visible=True,
                    collidable=False,
                    tags=["clue"],
                ).clone().set_position(x, y)
            )
    return Level(
        sprites=sl,
        grid_size=(G, G),
        data={"mines": [list(p) for p in mines], "difficulty": d},
    )


levels = [
    mk([(2, 2), (5, 5)], 1),
    mk([(1, 1), (6, 6), (3, 5)], 2),
    mk([(0, 0), (7, 7)], 3),
    mk([(2, 4), (5, 3), (4, 6)], 4),
    mk([(x, x) for x in range(0, 8, 2)], 5),
    mk([(1, 3), (5, 1), (6, 6)], 6),
    mk([(3, 3), (4, 4), (3, 4), (4, 3)], 7),
]


class Ms04(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Ms04UI(0, len(levels), 1)
        super().__init__(
            "ms04",
            levels,
            Camera(0, 0, CAM, CAM, BG, PAD, [self._ui]),
            False,
            1,
            [6],
        )


    def _sync_ui(self) -> None:
        self._ui.update(
            level_index=self.level_index,
            num_levels=len(levels),
            ticks=1,
            state=self._state,
        )

    def on_set_level(self, level: Level) -> None:
        self._mines = {tuple(int(t) for t in p) for p in level.get_data("mines")}
        self._flags: set[tuple[int, int]] = set()

    def step(self) -> None:
        if self.action.id != GameAction.ACTION6:
            self._sync_ui()
            self.complete_action()
            return
        c = self.camera.display_to_grid(
            self.action.data.get("x", 0), self.action.data.get("y", 0)
        )
        if c:
            gx, gy = int(c[0]), int(c[1])
            self._flags.add((gx, gy))
            sp = self.current_level.get_sprite_at(gx, gy, ignore_collidable=True)
            if sp and "clue" in sp.tags:
                sp.pixels = np.array([[FLAG_COLOR]], dtype=np.uint8)
            elif (gx, gy) in self._mines:
                existing = self.current_level.get_sprite_at(
                    gx, gy, ignore_collidable=True
                )
                if not existing or "flag_mark" not in existing.tags:
                    self.current_level.add_sprite(
                        Sprite(
                            pixels=np.array([[FLAG_COLOR]], dtype=np.uint8),
                            name="f",
                            visible=True,
                            collidable=False,
                            tags=["flag_mark"],
                        )
                        .clone()
                        .set_position(gx, gy)
                    )
            if self._flags >= self._mines:
                self.next_level()
        self._sync_ui()
        self.complete_action()
