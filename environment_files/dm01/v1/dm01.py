"""Domino cover: place 1×2 dominoes on adjacent pairs to cover every marked cell exactly once (two-click ACTION6)."""

from arcengine import (
    ARCBaseGame,
    Camera,
    GameAction,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Dm01UI(RenderableUserDisplay):
    def __init__(self, pending: bool, done: int, total: int) -> None:
        self._pending = pending
        self._done = done
        self._total = total

    def update(self, pending: bool, done: int, total: int) -> None:
        self._pending = pending
        self._done = done
        self._total = total

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        frame[h - 2, 2] = 11 if self._pending else 5
        for i in range(min(self._done, 12)):
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
        tags=["domino"],
    ),
}


def mk(cells: list[tuple[int, int]], d: int):
    sl = []
    for x, y in cells:
        sl.append(sprites["mark"].clone().set_position(x, y))
    return Level(
        sprites=sl,
        grid_size=(8, 8),
        data={"difficulty": d, "cells": [list(c) for c in cells]},
    )


levels = [
    mk([(2, 2), (3, 2), (2, 3), (3, 3)], 1),
    mk([(1, 1), (2, 1), (1, 2), (2, 2), (4, 4), (5, 4)], 2),
    mk([(0, 0), (1, 0), (0, 1), (1, 1), (6, 6), (7, 6), (6, 7), (7, 7)], 3),
    mk([(2, y) for y in range(2, 6)] + [(3, y) for y in range(2, 6)], 4),
    mk([(x, 3) for x in range(2, 6)] + [(x, 4) for x in range(2, 6)], 5),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Dm01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Dm01UI(False, 0, 1)
        super().__init__(
            "dm01",
            levels,
            Camera(0, 0, 8, 8, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [6],
        )

    def on_set_level(self, level: Level) -> None:
        raw = self.current_level.get_data("cells") or []
        self._must = {(int(t[0]), int(t[1])) for t in raw}
        self._covered: set[tuple[int, int]] = set()
        self._pending: tuple[int, int] | None = None
        self._total_pairs = len(self._must) // 2
        self._ui.update(False, 0, self._total_pairs)

    def step(self) -> None:
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

        if self._pending is None:
            if (gx, gy) in self._must and (gx, gy) not in self._covered:
                self._pending = (gx, gy)
                self._ui.update(True, len(self._covered) // 2, self._total_pairs)
            self.complete_action()
            return

        ax, ay = self._pending
        self._pending = None
        if abs(ax - gx) + abs(ay - gy) != 1:
            self._ui.update(False, len(self._covered) // 2, self._total_pairs)
            self.complete_action()
            return

        pair = {(ax, ay), (gx, gy)}
        if not pair.issubset(self._must) or pair & self._covered:
            self._ui.update(False, len(self._covered) // 2, self._total_pairs)
            self.complete_action()
            return

        self._covered |= pair
        cx, cy = (ax + gx) // 2, (ay + gy) // 2
        self.current_level.add_sprite(sprites["domino"].clone().set_position(cx, cy))
        done = len(self._covered) // 2
        self._ui.update(False, done, self._total_pairs)
        if self._covered == self._must:
            self.next_level()

        self.complete_action()
