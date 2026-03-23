"""Vertex cover lite: click vertex cells to select; every edge must touch a selected vertex."""

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
VERTEX_COLOR = 10
SELECT_COLOR = 14
CAM = 16


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


GW = GH = 8
CAM_PX = 16


def _vertex_center_frame(
    gx: int, gy: int, *, fh: int, fw: int, cw: int = CAM_PX, ch: int = CAM_PX
) -> tuple[int, int]:
    scale = min(fw // cw, fh // ch)
    x_pad = (fw - cw * scale) // 2
    y_pad = (fh - ch * scale) // 2
    tcx = int((gx + 0.5) * cw / GW)
    tcy = int((gy + 0.5) * ch / GH)
    return tcx * scale + x_pad + scale // 2, tcy * scale + y_pad + scale // 2


def _line_frame(
    frame,
    h: int,
    w: int,
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    color: int,
) -> None:
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    x, y = x0, y0
    while True:
        _rp(frame, h, w, x, y, color)
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x += sx
        if e2 <= dx:
            err += dx
            y += sy


class Cs01UI(RenderableUserDisplay):
    def __init__(self, sel: int, cap: int, level_index: int = 0, num_levels: int = 7) -> None:
        self._sel = sel
        self._cap = cap
        self._level_index = level_index
        self._num_levels = num_levels
        self._state = None
        self._edges: list[tuple[tuple[int, int], tuple[int, int]]] = []

    def update(
        self,
        sel: int,
        cap: int,
        *,
        level_index: int | None = None,
        num_levels: int | None = None,
        state=None,
        edges: list[tuple[tuple[int, int], tuple[int, int]]] | None = None,
    ) -> None:
        self._sel = sel
        self._cap = cap
        if level_index is not None:
            self._level_index = level_index
        if num_levels is not None:
            self._num_levels = num_levels
        if state is not None:
            self._state = state
        if edges is not None:
            self._edges = edges

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for a, b in self._edges:
            xa, ya = _vertex_center_frame(a[0], a[1], fh=h, fw=w)
            xb, yb = _vertex_center_frame(b[0], b[1], fh=h, fw=w)
            _line_frame(frame, h, w, xa, ya, xb, yb, 4)
        _r_dots(frame, h, w, self._level_index, self._num_levels, 0)
        for i in range(min(self._sel, 12)):
            frame[h - 2, 2 + i] = 14
        frame[h - 2, 30] = 11 if self._cap <= 0 or self._sel <= self._cap else 8
        go = self._state == GameState.GAME_OVER
        win = self._state == GameState.WIN
        _r_bar(frame, h, w, go, win)
        return frame


sprites = {
    "vertex": Sprite(
        pixels=[[VERTEX_COLOR]],
        name="vertex",
        visible=True,
        collidable=False,
        tags=["vertex"],
    ),
    "sel": Sprite(
        pixels=[[SELECT_COLOR]],
        name="sel",
        visible=True,
        collidable=False,
        tags=["selected_mark"],
    ),
}


def mk(
    vertices: list[tuple[int, int]],
    edges: list[tuple[tuple[int, int], tuple[int, int]]],
    budget: int,
    diff: int,
) -> Level:
    sl: list[Sprite] = []
    for vx, vy in vertices:
        sl.append(sprites["vertex"].clone().set_position(vx, vy))
    return Level(
        sprites=sl,
        grid_size=(8, 8),
        data={
            "difficulty": diff,
            "vertices": [list(p) for p in vertices],
            "edges": [[list(a), list(b)] for a, b in edges],
            "budget": budget,
        },
    )


levels = [
    mk([(1, 1), (3, 1), (2, 3)], [((1, 1), (3, 1)), ((1, 1), (2, 3)), ((3, 1), (2, 3))], 6, 1),
    mk([(1, 2), (4, 2), (2, 5), (5, 5)], [((1, 2), (4, 2)), ((4, 2), (5, 5)), ((2, 5), (5, 5))], 8, 2),
    mk([(0, 0), (7, 0), (0, 7), (7, 7)], [((0, 0), (7, 0)), ((0, 0), (0, 7)), ((7, 7), (7, 0)), ((7, 7), (0, 7))], 8, 3),
    mk([(2, 2), (5, 2), (2, 5), (5, 5)], [((2, 2), (5, 2)), ((2, 2), (2, 5)), ((5, 5), (5, 2)), ((5, 5), (2, 5))], 6, 4),
    mk([(1, 3), (3, 3), (5, 3), (2, 6), (4, 6)], [((1, 3), (3, 3)), ((3, 3), (5, 3)), ((2, 6), (4, 6)), ((1, 3), (2, 6)), ((5, 3), (4, 6))], 9, 5),
    mk([(0, 4), (4, 0), (7, 4), (4, 7)], [((0, 4), (4, 0)), ((4, 0), (7, 4)), ((7, 4), (4, 7)), ((4, 7), (0, 4))], 8, 6),
    mk([(1, 1), (1, 6), (6, 1), (6, 6), (3, 4)], [((1, 1), (1, 6)), ((6, 1), (6, 6)), ((1, 1), (3, 4)), ((6, 6), (3, 4))], 10, 7),
]


class Cs01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Cs01UI(0, 99, 0, len(levels))
        super().__init__(
            "cs01",
            levels,
            Camera(0, 0, CAM, CAM, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 6],
        )

    def on_set_level(self, level: Level) -> None:
        raw_v = self.current_level.get_data("vertices") or []
        self._vertices = {tuple(int(t) for t in p) for p in raw_v}
        raw_e = self.current_level.get_data("edges") or []
        self._edges: list[tuple[tuple[int, int], tuple[int, int]]] = []
        for item in raw_e:
            a, b = item
            self._edges.append(
                (tuple(int(x) for x in a), tuple(int(x) for x in b)),
            )
        self._budget = int(self.current_level.get_data("budget") or 99)
        self._selected: set[tuple[int, int]] = set()
        self._refresh_marks()
        self._sync_ui()

    def _sync_ui(self) -> None:
        self._ui.update(
            len(self._selected),
            self._budget,
            level_index=self.level_index,
            num_levels=len(levels),
            state=self._state,
            edges=self._edges,
        )

    def _refresh_marks(self) -> None:
        for s in list(self.current_level.get_sprites_by_tag("selected_mark")):
            self.current_level.remove_sprite(s)
        for p in self._selected:
            self.current_level.add_sprite(sprites["sel"].clone().set_position(p[0], p[1]))
        self._sync_ui()

    def _covered(self) -> bool:
        for a, b in self._edges:
            if a not in self._selected and b not in self._selected:
                return False
        return True

    def step(self) -> None:
        if self.action.id.value in (1, 2, 3, 4):
            self.complete_action()
            return

        if self.action.id != GameAction.ACTION6:
            self.complete_action()
            return

        px = int(self.action.data.get("x", 0))
        py = int(self.action.data.get("y", 0))
        hit = self.camera.display_to_grid(px, py)
        if hit is None:
            self.complete_action()
            return
        gx, gy = int(hit[0]), int(hit[1])
        p = (gx, gy)
        if p not in self._vertices:
            self.complete_action()
            return

        if p in self._selected:
            self._selected.remove(p)
        else:
            if len(self._selected) >= self._budget:
                self.complete_action()
                return
            self._selected.add(p)

        self._refresh_marks()
        if self._covered() and len(self._selected) <= self._budget:
            self.next_level()

        self._sync_ui()
        self.complete_action()
