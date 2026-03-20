"""kv04: two parallel resistor ladders — ACTION1–3 cycle branch A; ACTION4 cycles r3 on branch B; ACTION5 verify both node pairs."""

from __future__ import annotations

from fractions import Fraction

from arcengine import ARCBaseGame, Camera, GameAction, Level, RenderableUserDisplay


class Kv04UI(RenderableUserDisplay):
    def render_interface(self, frame):
        return frame


def _cycle(x: int) -> int:
    opts = (1, 2, 4)
    i = opts.index(x) if x in opts else 0
    return opts[(i + 1) % 3]


def _v(r0: int, r1: int, r2: int) -> tuple[Fraction, Fraction]:
    s = r0 + r1 + r2
    if s == 0:
        return Fraction(0), Fraction(0)
    return Fraction(12 * (r1 + r2), s), Fraction(12 * r2, s)


def mk(d, r0, r1, r2, r3, r4, r5, t1, t2, t3, t4):
    return Level(
        sprites=[],
        grid_size=(8, 8),
        data={
            "difficulty": d,
            "r0": r0,
            "r1": r1,
            "r2": r2,
            "r3": r3,
            "r4": r4,
            "r5": r5,
            "t1n": t1[0],
            "t1d": t1[1],
            "t2n": t2[0],
            "t2d": t2[1],
            "t3n": t3[0],
            "t3d": t3[1],
            "t4n": t4[0],
            "t4d": t4[1],
        },
    )


levels = [
    mk(1, 2, 4, 2, 2, 4, 2, (8, 1), (4, 1), (8, 1), (4, 1)),
    mk(2, 1, 1, 1, 2, 2, 2, (9, 1), (3, 1), (10, 1), (2, 1)),
    mk(3, 1, 2, 4, 1, 2, 4, (8, 1), (4, 1), (8, 1), (4, 1)),
    mk(4, 2, 2, 2, 1, 1, 1, (10, 1), (2, 1), (9, 1), (3, 1)),
    mk(5, 1, 2, 1, 2, 4, 2, (4, 1), (2, 1), (8, 1), (4, 1)),
    mk(6, 4, 2, 1, 1, 2, 4, (6, 1), (2, 1), (8, 1), (4, 1)),
    mk(7, 2, 1, 4, 4, 1, 2, (10, 1), (8, 1), (10, 1), (2, 1)),
]


class Kv04(ARCBaseGame):
    def __init__(self) -> None:
        super().__init__(
            "kv04",
            levels,
            Camera(0, 0, 8, 8, 5, 4, [Kv04UI()]),
            False,
            1,
            [1, 2, 3, 4, 5],
        )

    def on_set_level(self, level: Level) -> None:
        d = level.get_data
        self._r0 = int(d("r0"))
        self._r1 = int(d("r1"))
        self._r2 = int(d("r2"))
        self._r3 = int(d("r3"))
        self._r4 = int(d("r4"))
        self._r5 = int(d("r5"))
        self._t1 = Fraction(int(d("t1n")), int(d("t1d")))
        self._t2 = Fraction(int(d("t2n")), int(d("t2d")))
        self._t3 = Fraction(int(d("t3n")), int(d("t3d")))
        self._t4 = Fraction(int(d("t4n")), int(d("t4d")))

    def step(self) -> None:
        aid = self.action.id
        if aid == GameAction.ACTION1:
            self._r0 = _cycle(self._r0)
        elif aid == GameAction.ACTION2:
            self._r1 = _cycle(self._r1)
        elif aid == GameAction.ACTION3:
            self._r2 = _cycle(self._r2)
        elif aid == GameAction.ACTION4:
            self._r3 = _cycle(self._r3)
        elif aid == GameAction.ACTION5:
            v1, v2 = _v(self._r0, self._r1, self._r2)
            v3, v4 = _v(self._r3, self._r4, self._r5)
            if v1 == self._t1 and v2 == self._t2 and v3 == self._t3 and v4 == self._t4:
                self.next_level()
        self.complete_action()
