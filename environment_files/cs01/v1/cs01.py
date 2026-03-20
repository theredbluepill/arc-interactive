"""Vertex cover lite: click vertex cells to select; every edge must touch a selected vertex."""

from __future__ import annotations

from arcengine import (
    ARCBaseGame,
    Camera,
    GameAction,
    Level,
    RenderableUserDisplay,
    Sprite,
)

BACKGROUND_COLOR = 5
PADDING_COLOR = 4
VERTEX_COLOR = 10
SELECT_COLOR = 14
CAM = 16


class Cs01UI(RenderableUserDisplay):
    def __init__(self, sel: int, cap: int) -> None:
        self._sel = sel
        self._cap = cap

    def update(self, sel: int, cap: int) -> None:
        self._sel = sel
        self._cap = cap

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for i in range(min(self._sel, 12)):
            frame[h - 2, 2 + i] = 14
        frame[h - 2, 30] = 11 if self._cap <= 0 or self._sel <= self._cap else 8
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
        self._ui = Cs01UI(0, 99)
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
        self._ui.update(len(self._selected), self._budget)

    def _refresh_marks(self) -> None:
        for s in list(self.current_level.get_sprites_by_tag("selected_mark")):
            self.current_level.remove_sprite(s)
        for p in self._selected:
            self.current_level.add_sprite(sprites["sel"].clone().set_position(p[0], p[1]))
        self._ui.update(len(self._selected), self._budget)

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

        self.complete_action()
