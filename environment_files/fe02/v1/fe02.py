"""fe02: **vote** with ACTION1–4, **ACTION5** ratifies the leading rule and applies a tiny world tick; survive **N** ratifications."""

from __future__ import annotations

from arcengine import ARCBaseGame, Camera, GameAction, Level, RenderableUserDisplay

BG, PAD = 5, 4


class Fe02UI(RenderableUserDisplay):
    def __init__(self) -> None:
        self._a = self._b = self._c = 5
        self._rat = 0
        self._votes = (0, 0, 0, 0)

    def sync(self, a: int, b: int, c: int, rat: int, votes: tuple[int, ...]) -> None:
        self._a, self._b, self._c = a, b, c
        self._rat = rat
        self._votes = votes

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for i, v in enumerate(self._votes[: min(4, w - 2)]):
            frame[h - 2, 2 + i] = min(15, 5 + min(v, 5))
        frame[h - 3, 2] = min(15, self._a + 5)
        frame[h - 3, 4] = min(15, self._b + 5)
        frame[h - 3, 6] = min(15, self._c + 5)
        frame[h - 4, 2] = min(15, 10 + self._rat)
        return frame


# Four policies as (dA, dB, dC)
RULES = (
    (1, -1, 0),
    (-1, 1, 1),
    (0, 1, -1),
    (1, 1, -1),
)

levels = [
    Level(sprites=[], grid_size=(8, 8), data={"need": 5, "difficulty": i + 1})
    for i in range(7)
]


class Fe02(ARCBaseGame):
    def __init__(self) -> None:
        self._hud = Fe02UI()
        super().__init__(
            "fe02",
            levels,
            Camera(0, 0, 8, 8, BG, PAD, [self._hud]),
            False,
            1,
            [1, 2, 3, 4, 5],
        )

    def on_set_level(self, level: Level) -> None:
        self._a = self._b = self._c = 5
        self._rat = 0
        self._votes = [0, 0, 0, 0]
        self._need = int(level.get_data("need"))
        self._hud.sync(self._a, self._b, self._c, self._rat, tuple(self._votes))

    def step(self) -> None:
        aid = self.action.id
        if aid in (GameAction.ACTION1, GameAction.ACTION2, GameAction.ACTION3, GameAction.ACTION4):
            i = aid.value - 1
            self._votes[i] += 1
            self._hud.sync(self._a, self._b, self._c, self._rat, tuple(self._votes))
            self.complete_action()
            return
        if aid == GameAction.ACTION5:
            j = max(range(4), key=lambda k: (self._votes[k], -k))
            da, db, dc = RULES[j]
            self._a += da
            self._b += db
            self._c += dc
            self._votes = [0, 0, 0, 0]
            self._rat += 1
            self._hud.sync(self._a, self._b, self._c, self._rat, tuple(self._votes))
            if self._a <= 0 or self._b <= 0 or self._c <= 0 or self._a > 9 or self._b > 9 or self._c > 9:
                self.lose()
            elif self._rat >= self._need:
                self.next_level()
            self.complete_action()
            return
        self.complete_action()
