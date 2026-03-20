"""dm04: cover marked cells with L-trominoes (three orth-adjacent clicks forming an L in a 2×2)."""

from __future__ import annotations

from arcengine import ARCBaseGame, Camera, GameAction, Level, RenderableUserDisplay, Sprite

BG, PAD = 5, 4
GW, GH = 8, 8


class Dm04UI(RenderableUserDisplay):
    def __init__(self, n: int, need: int) -> None:
        self._n = n
        self._need = need

    def update(self, n: int, need: int) -> None:
        self._n = n
        self._need = need

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for i in range(min(self._n, 10)):
            frame[h - 2, 2 + i] = 14
        frame[h - 2, 20] = 11 if self._need > 0 else 14
        return frame


MARK = Sprite(
    pixels=[[2]], name="m", visible=True, collidable=False, tags=["mark"]
)
TR = Sprite(
    pixels=[[6]], name="t", visible=True, collidable=False, tags=["tromino"]
)


def mk(cells: list[tuple[int, int]], d: int) -> Level:
    sl = [MARK.clone().set_position(x, y) for x, y in cells]
    return Level(
        sprites=sl,
        grid_size=(GW, GH),
        data={"cells": [list(c) for c in cells], "difficulty": d},
    )


def is_l_tromino(cells: list[tuple[int, int]]) -> bool:
    if len(cells) != 3 or len(set(cells)) != 3:
        return False
    xs = [c[0] for c in cells]
    ys = [c[1] for c in cells]
    if max(xs) - min(xs) > 1 or max(ys) - min(ys) > 1:
        return False
    if len(set(xs)) == 1 or len(set(ys)) == 1:
        return False
    corners = {(min(xs), min(ys)), (max(xs), min(ys)), (min(xs), max(ys)), (max(xs), max(ys))}
    return set(cells) <= corners and len(set(cells)) == 3


levels = [
    mk([(2, 2), (3, 2), (2, 3)], 1),
    mk([(1, 1), (2, 1), (1, 2), (4, 4), (5, 4), (4, 5)], 2),
    mk([(0, 0), (1, 0), (0, 1), (6, 6), (7, 6), (6, 7)], 3),
    mk([(2, 2), (3, 2), (2, 3), (4, 4), (5, 4), (4, 5)], 4),
    mk([(2, 3), (3, 3), (2, 4), (5, 5), (6, 5), (5, 6)], 5),
    mk([(1, 2), (2, 2), (1, 3), (3, 5), (4, 5), (3, 6)], 6),
    mk([(2, 1), (3, 1), (2, 2), (5, 2), (6, 2), (5, 3), (4, 6), (5, 6), (4, 7)], 7),
]


class Dm04(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Dm04UI(0, 0)
        super().__init__(
            "dm04",
            levels,
            Camera(0, 0, GW, GH, BG, PAD, [self._ui]),
            False,
            1,
            [6],
        )

    def on_set_level(self, level: Level) -> None:
        raw = level.get_data("cells") or []
        self._must = {(int(a), int(b)) for a, b in raw}
        self._covered: set[tuple[int, int]] = set()
        self._pending: list[tuple[int, int]] = []
        self._tri = len(self._must) // 3
        self._ui.update(0, self._tri)

    def step(self) -> None:
        if self.action.id != GameAction.ACTION6:
            self.complete_action()
            return
        hit = self.camera.display_to_grid(
            self.action.data.get("x", 0), self.action.data.get("y", 0)
        )
        if not hit:
            self.complete_action()
            return
        gx, gy = int(hit[0]), int(hit[1])
        if (gx, gy) not in self._must or (gx, gy) in self._covered:
            self._pending = []
            self._ui.update(len(self._covered) // 3, self._tri - len(self._covered) // 3)
            self.complete_action()
            return
        if (gx, gy) in self._pending:
            self.complete_action()
            return
        self._pending.append((gx, gy))
        if len(self._pending) < 3:
            self.complete_action()
            return
        trip = self._pending
        self._pending = []
        if not is_l_tromino(trip):
            self._ui.update(len(self._covered) // 3, self._tri - len(self._covered) // 3)
            self.complete_action()
            return
        for p in trip:
            self._covered.add(p)
            self.current_level.add_sprite(TR.clone().set_position(p[0], p[1]))
        done = len(self._covered) // 3
        self._ui.update(done, self._tri - done)
        if self._covered >= self._must:
            self.next_level()
        self.complete_action()
