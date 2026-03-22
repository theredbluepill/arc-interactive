"""cx01: toggle **gate** cells until **S** and **T** are disconnected (no 4-neighbor path)."""

from __future__ import annotations

from collections import deque

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

G = 10
CAM = 16
OPEN, SHUT = 12, 3


class Cx01UI(RenderableUserDisplay):
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


def cell_sprite(x: int, y: int, c: int, tags: list[str]) -> Sprite:
    return (
        Sprite(
            pixels=[[c]],
            name="c",
            visible=True,
            collidable=False,
            tags=tags,
        )
        .clone()
        .set_position(x, y)
    )


def mk(s: tuple[int, int], t: tuple[int, int], walls: set[tuple[int, int]], gates: list[tuple[int, int]], d: int) -> Level:
    sl: list[Sprite] = []
    for y in range(G):
        for x in range(G):
            if (x, y) == s:
                sl.append(cell_sprite(x, y, 9, ["s", "mark"]))
            elif (x, y) == t:
                sl.append(cell_sprite(x, y, 11, ["t", "mark"]))
            elif (x, y) in walls:
                sl.append(cell_sprite(x, y, 5, ["wall", "mark"]))
            elif (x, y) in gates:
                sl.append(cell_sprite(x, y, OPEN, ["gate", "mark"]))
            else:
                sl.append(cell_sprite(x, y, 1, ["floor", "mark"]))
    return Level(
        sprites=sl,
        grid_size=(G, G),
        data={
            "s": list(s),
            "t": list(t),
            "walls": [list(p) for p in walls],
            "gates": [list(p) for p in gates],
            "difficulty": d,
        },
    )


def col_cut(gx: int, ys_open: list[int]) -> tuple[set[tuple[int, int]], list[tuple[int, int]]]:
    walls = {(gx, y) for y in range(G) if y not in ys_open}
    gates = [(gx, y) for y in ys_open]
    return walls, gates


levels = [
    mk((0, 4), (9, 4), *col_cut(5, [4]), 1),
    mk((0, 4), (9, 4), *col_cut(5, [3, 4]), 2),
    mk((0, 0), (9, 9), *col_cut(5, [2, 7]), 3),
    mk((2, 5), (8, 5), *col_cut(5, [4, 5]), 4),
    mk((1, 1), (8, 8), *col_cut(3, [4]), 5),
    mk((0, 6), (9, 6), *col_cut(6, [5, 6]), 6),
    mk((0, 5), (9, 5), *col_cut(5, [3, 4, 5]), 7),
]


class Cx01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Cx01UI(0, len(levels), 1)
        super().__init__(
            "cx01",
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
        d = level.get_data
        self._s = tuple(int(x) for x in d("s"))
        self._t = tuple(int(x) for x in d("t"))
        self._walls = {tuple(int(t) for t in p) for p in d("walls")}
        self._gate_set = {tuple(int(t) for t in p) for p in d("gates")}
        self._open = {tuple(int(t) for t in p) for p in d("gates")}

    def _passable(self, x: int, y: int) -> bool:
        if not (0 <= x < G and 0 <= y < G):
            return False
        if (x, y) in self._walls:
            return False
        if (x, y) == self._s or (x, y) == self._t:
            return True
        if (x, y) in self._gate_set:
            return (x, y) in self._open
        return True

    def _connected(self) -> bool:
        if self._s == self._t:
            return True
        q = deque([self._s])
        seen = {self._s}
        while q:
            x, y = q.popleft()
            if (x, y) == self._t:
                return True
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                nx, ny = x + dx, y + dy
                if (nx, ny) in seen:
                    continue
                if self._passable(nx, ny):
                    seen.add((nx, ny))
                    q.append((nx, ny))
        return False

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
            if (gx, gy) in self._gate_set:
                if (gx, gy) in self._open:
                    self._open.discard((gx, gy))
                else:
                    self._open.add((gx, gy))
                sp = self.current_level.get_sprite_at(gx, gy, ignore_collidable=True)
                if sp and "gate" in sp.tags:
                    sp.pixels = np.array(
                        [[OPEN if (gx, gy) in self._open else SHUT]], dtype=np.int8
                    )
        if not self._connected():
            self.next_level()
        self._sync_ui()
        self.complete_action()
