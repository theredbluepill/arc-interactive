"""Polyomino pack: cover marked cells with dominoes (two orth-adjacent clicks) or straight trominoes (three collinear unit steps).

Spec:
- Tags: ``mark`` (cells to cover), ``piece`` (placed domino/tromino overlay, non-collidable).
- ``level.data``: ``cells`` — list of [x,y] marked floor; must partition into dominoes and trominoes per level (all marked cells covered exactly once).
- Actions: **5** toggles placement mode (domino vs tromino). **6** click grid (`display_to_grid`): domino = pick two orth-adjacent marked cells; tromino = pick three consecutive cells in a row or column.
- Win: ``covered == marks``. Lose: none (mis-clicks just reset pending).
- Camera: 10×10 or 12×12 grids.
"""

from arcengine import (
    ARCBaseGame,
    Camera,
    GameAction,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Pk01UI(RenderableUserDisplay):
    def __init__(self, mode: str, pending: int, done: int, total: int) -> None:
        self._mode = mode
        self._pending = pending
        self._done = done
        self._total = total
        self._li = 0
        self._nlv = 1

    def update(
        self,
        mode: str,
        pending: int,
        done: int,
        total: int,
        level_index: int | None = None,
        num_levels: int | None = None,
    ) -> None:
        self._mode = mode
        self._pending = pending
        self._done = done
        self._total = total
        if level_index is not None:
            self._li = level_index
        if num_levels is not None:
            self._nlv = num_levels

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for i in range(min(self._nlv, 14)):
            cx = 1 + i * 2
            if cx >= w:
                break
            dot = 14 if i < self._li else (11 if i == self._li else 3)
            frame[0, cx] = dot
        frame[h - 2, 1] = 7 if self._mode == "tromino" else 10
        frame[h - 2, 2] = 11 if self._pending else 5
        for i in range(min(self._done, 14)):
            frame[h - 2, 4 + i] = 14
        return frame


sprites = {
    "mark": Sprite(
        pixels=[[2]],
        name="mark",
        visible=True,
        collidable=False,
        tags=["mark"],
    ),
    "domino": Sprite(
        pixels=[[6]],
        name="domino",
        visible=True,
        collidable=False,
        tags=["piece", "domino"],
    ),
    "tromino": Sprite(
        pixels=[[13]],
        name="tromino",
        visible=True,
        collidable=False,
        tags=["piece", "tromino"],
    ),
}


def _cells_level(cells: list[tuple[int, int]], diff: int, grid: tuple[int, int]) -> Level:
    sl = [sprites["mark"].clone().set_position(x, y) for x, y in cells]
    return Level(
        sprites=sl,
        grid_size=grid,
        data={"difficulty": diff, "cells": [list(c) for c in cells]},
    )


levels = [
    _cells_level([(2, 2), (3, 2), (2, 3), (3, 3)], 1, (8, 8)),
    _cells_level([(1, 1), (2, 1), (3, 1), (5, 5), (6, 5), (7, 5)], 2, (10, 10)),
    _cells_level([(0, 0), (1, 0), (2, 0), (4, 4), (5, 4), (6, 4)], 3, (10, 10)),
    _cells_level(
        [(2, y) for y in range(2, 6)] + [(3, y) for y in range(2, 6)] + [(4, 3), (5, 3), (6, 3)],
        4,
        (10, 10),
    ),
    _cells_level(
        [(x, 4) for x in range(2, 7)] + [(x, 5) for x in range(2, 7)] + [(3, 3), (4, 3), (5, 3)],
        5,
        (12, 12),
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


def _straight_tromino(cells: list[tuple[int, int]]) -> bool:
    if len(cells) != 3:
        return False
    xs = [c[0] for c in cells]
    ys = [c[1] for c in cells]
    if len(set(xs)) == 1:
        ys_sorted = sorted(ys)
        return ys_sorted[1] - ys_sorted[0] == 1 and ys_sorted[2] - ys_sorted[1] == 1
    if len(set(ys)) == 1:
        xs_sorted = sorted(xs)
        return xs_sorted[1] - xs_sorted[0] == 1 and xs_sorted[2] - xs_sorted[1] == 1
    return False


class Pk01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Pk01UI("domino", 0, 0, 1)
        super().__init__(
            "pk01",
            levels,
            Camera(0, 0, 12, 12, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [5, 6],
        )

    def on_set_level(self, level: Level) -> None:
        raw = self.current_level.get_data("cells") or []
        self._must = {(int(t[0]), int(t[1])) for t in raw}
        self._covered: set[tuple[int, int]] = set()
        self._pending: list[tuple[int, int]] = []
        self._mode_domino = True
        self._total_cells = len(self._must)
        self._sync_ui()

    def _sync_ui(self) -> None:
        mode = "domino" if self._mode_domino else "tromino"
        done = len(self._covered)
        self._ui.update(
            mode,
            len(self._pending),
            done,
            self._total_cells,
            level_index=self.level_index,
            num_levels=len(levels),
        )

    def _add_piece(self, cells: list[tuple[int, int]], kind: str) -> None:
        ax = sum(c[0] for c in cells) / len(cells)
        ay = sum(c[1] for c in cells) / len(cells)
        cx, cy = int(round(ax)), int(round(ay))
        sp = (
            sprites["domino"].clone().set_position(cx, cy)
            if kind == "domino"
            else sprites["tromino"].clone().set_position(cx, cy)
        )
        self.current_level.add_sprite(sp)

    def step(self) -> None:
        if self.action.id == GameAction.ACTION5:
            self._mode_domino = not self._mode_domino
            self._pending = []
            self._sync_ui()
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
        g = (gx, gy)

        if g not in self._must or g in self._covered:
            self._pending = []
            self._sync_ui()
            self.complete_action()
            return

        if g in self._pending:
            self._pending.remove(g)
            self._sync_ui()
            self.complete_action()
            return

        self._pending.append(g)
        need = 2 if self._mode_domino else 3

        if len(self._pending) < need:
            self._sync_ui()
            self.complete_action()
            return

        cells = self._pending[:]
        self._pending = []

        if self._mode_domino:
            if len(cells) != 2:
                self._sync_ui()
                self.complete_action()
                return
            (ax, ay), (bx, by) = cells
            if abs(ax - bx) + abs(ay - by) != 1:
                self._sync_ui()
                self.complete_action()
                return
            pair = {cells[0], cells[1]}
            if not pair.issubset(self._must) or pair & self._covered:
                self._sync_ui()
                self.complete_action()
                return
            self._covered |= pair
            self._add_piece(cells, "domino")
        else:
            if not _straight_tromino(cells):
                self._sync_ui()
                self.complete_action()
                return
            trip = set(cells)
            if not trip.issubset(self._must) or trip & self._covered:
                self._sync_ui()
                self.complete_action()
                return
            self._covered |= trip
            self._add_piece(cells, "tromino")

        self._sync_ui()
        if self._covered == self._must:
            self.next_level()

        self.complete_action()
