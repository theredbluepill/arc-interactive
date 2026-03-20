"""sg04: dual score arms — ACTION5 commits +1 to arm A or B alternating."""

from __future__ import annotations

from arcengine import ARCBaseGame, Camera, GameAction, Level, RenderableUserDisplay

BG, PAD = 5, 4


class Sg04UI(RenderableUserDisplay):
    def __init__(self, a: int, b: int, ta: int, tb: int) -> None:
        self._a, self._b, self._ta, self._tb = a, b, ta, tb

    def update(self, a: int, b: int, ta: int, tb: int) -> None:
        self._a, self._b, self._ta, self._tb = a, b, ta, tb

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for i in range(min(self._ta, 8)):
            frame[h - 2, 1 + i] = 14 if i < self._a else 4
        for i in range(min(self._tb, 8)):
            frame[h - 1, 1 + i] = 11 if i < self._b else 4
        return frame


def mk(ta: int, tb: int, max_steps: int, d: int) -> Level:
    return Level(
        sprites=[],
        grid_size=(8, 8),
        data={"ta": ta, "tb": tb, "max_steps": max_steps, "difficulty": d},
    )


levels = [
    mk(3, 3, 30, 1),
    mk(4, 2, 35, 2),
    mk(2, 5, 40, 3),
    mk(5, 5, 50, 4),
    mk(3, 6, 55, 5),
    mk(6, 3, 60, 6),
    mk(4, 4, 45, 7),
]


class Sg04(ARCBaseGame):
    def __init__(self) -> None:
        self._hud = Sg04UI(0, 0, 1, 1)
        super().__init__(
            "sg04",
            levels,
            Camera(0, 0, 8, 8, BG, PAD, [self._hud]),
            False,
            1,
            [5],
        )

    def on_set_level(self, level: Level) -> None:
        self._ta = int(level.get_data("ta") or 3)
        self._tb = int(level.get_data("tb") or 3)
        self._a = self._b = 0
        self._arm = 0
        self._left = int(level.get_data("max_steps") or 40)
        self._hud.update(self._a, self._b, self._ta, self._tb)

    def step(self) -> None:
        if self.action.id == GameAction.ACTION5:
            if self._left <= 0:
                self.lose()
                self.complete_action()
                return
            self._left -= 1
            if self._arm == 0 and self._a < self._ta:
                self._a += 1
            elif self._arm == 1 and self._b < self._tb:
                self._b += 1
            self._arm = 1 - self._arm
            self._hud.update(self._a, self._b, self._ta, self._tb)
            if self._a >= self._ta and self._b >= self._tb:
                self.next_level()
            self.complete_action()
            return
        self.complete_action()
