"""Kirchhoff-lite ladder: three series resistors between fixed 12 V and ground; cycle each R ∈ {1,2,4} and match probe voltages.

Spec:
- No grid entities; puzzle is driven purely by internal state (shown in HUD).
- ``level.data``: ``r0``, ``r1``, ``r2`` — initial ohm values (each in {1,2,4}); ``t1_num``, ``t1_den``, ``t2_num``, ``t2_den`` — target ``Fraction`` for V(node1) and V(node2) with V0=12, V3=0 and nodes 0—1—2—3 in series.
- Actions: **1** cycles ``r0**, **2** cycles ``r1**, **3** cycles ``r2** through (1,2,4). **5** checks win (no-op if wrong).
- Win: ``V1 == t1`` and ``V2 == t2`` as exact ``Fraction``s. Lose: none.
- Camera: 8×8 (minimal letterbox); optional decorative ``wall`` sprites optional — omitted here.
"""

from __future__ import annotations

from fractions import Fraction

from arcengine import (
    ARCBaseGame,
    Camera,
    GameAction,
    Level,
    RenderableUserDisplay,
)


class Kv01UI(RenderableUserDisplay):
    def __init__(
        self,
        r0: int,
        r1: int,
        r2: int,
        v1n: int,
        v1d: int,
        v2n: int,
        v2d: int,
        t1n: int,
        t1d: int,
        t2n: int,
        t2d: int,
    ) -> None:
        self._r0 = r0
        self._r1 = r1
        self._r2 = r2
        self._v1n = v1n
        self._v1d = v1d
        self._v2n = v2n
        self._v2d = v2d
        self._t1n = t1n
        self._t1d = t1d
        self._t2n = t2n
        self._t2d = t2d
        self._bad_check = False
        self._li = 0
        self._nlv = 1

    def update(
        self,
        r0: int,
        r1: int,
        r2: int,
        v1n: int,
        v1d: int,
        v2n: int,
        v2d: int,
        t1n: int,
        t1d: int,
        t2n: int,
        t2d: int,
        *,
        bad_check: bool | None = None,
        level_index: int | None = None,
        num_levels: int | None = None,
    ) -> None:
        self._r0 = r0
        self._r1 = r1
        self._r2 = r2
        self._v1n = v1n
        self._v1d = v1d
        self._v2n = v2n
        self._v2d = v2d
        self._t1n = t1n
        self._t1d = t1d
        self._t2n = t2n
        self._t2d = t2d
        if bad_check is not None:
            self._bad_check = bad_check
        if level_index is not None:
            self._li = level_index
        if num_levels is not None:
            self._nlv = num_levels

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape

        def _c(x: int) -> int:
            return min(15, max(0, int(x)))

        frame[h - 5, 0] = 11
        frame[h - 1, 0] = 5
        for i, rv in enumerate((self._r0, self._r1, self._r2)):
            c = 6 + (rv % 3) * 3
            frame[h - 4, 2 + i] = c
        # Current probe voltages (numerator / denominator) — full small integers, no mod wrap.
        frame[h - 3, 1] = _c(self._v1n)
        frame[h - 3, 2] = _c(self._v1d)
        frame[h - 3, 4] = _c(self._v2n)
        frame[h - 3, 5] = _c(self._v2d)
        frame[h - 3, 0] = 10
        frame[h - 3, 3] = 5
        # Targets to match (same encoding).
        frame[h - 2, 1] = _c(self._t1n)
        frame[h - 2, 2] = _c(self._t1d)
        frame[h - 2, 4] = _c(self._t2n)
        frame[h - 2, 5] = _c(self._t2d)
        frame[h - 2, 0] = 11
        frame[h - 2, 3] = 5
        frame[h - 2, 7] = 8 if self._bad_check else 5
        for i in range(min(self._nlv, 14)):
            cx = 1 + i * 2
            if cx >= w:
                break
            dot = 14 if i < self._li else (11 if i == self._li else 3)
            frame[0, cx] = dot
        return frame


def _cycle_r(x: int) -> int:
    opts = (1, 2, 4)
    i = opts.index(x) if x in opts else 0
    return opts[(i + 1) % len(opts)]


def _voltages(r0: int, r1: int, r2: int) -> tuple[Fraction, Fraction]:
    s = r0 + r1 + r2
    if s == 0:
        return Fraction(0), Fraction(0)
    v1 = Fraction(12 * (r1 + r2), s)
    v2 = Fraction(12 * r2, s)
    return v1, v2


def make_kv_level(
    difficulty: int,
    init_r0: int,
    init_r1: int,
    init_r2: int,
    t1: tuple[int, int],
    t2: tuple[int, int],
) -> Level:
    return Level(
        sprites=[],
        grid_size=(8, 8),
        data={
            "difficulty": difficulty,
            "r0": init_r0,
            "r1": init_r1,
            "r2": init_r2,
            "t1_num": t1[0],
            "t1_den": t1[1],
            "t2_num": t2[0],
            "t2_den": t2[1],
        },
    )


# Targets are V1,V2 with V0=12, V3=0; a solution exists by cycling each R in {1,2,4}.
levels = [
    make_kv_level(1, 2, 4, 2, (8, 1), (4, 1)),
    make_kv_level(2, 1, 1, 1, (9, 1), (3, 1)),
    make_kv_level(3, 1, 2, 4, (8, 1), (4, 1)),
    make_kv_level(4, 2, 2, 2, (10, 1), (2, 1)),
    make_kv_level(5, 1, 2, 1, (4, 1), (2, 1)),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Kv01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Kv01UI(1, 1, 1, 8, 1, 4, 1, 8, 1, 4, 1)
        super().__init__(
            "kv01",
            levels,
            Camera(0, 0, 8, 8, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 5],
        )

    def on_set_level(self, level: Level) -> None:
        self._r0 = int(level.get_data("r0"))
        self._r1 = int(level.get_data("r1"))
        self._r2 = int(level.get_data("r2"))
        self._t1 = Fraction(int(level.get_data("t1_num")), int(level.get_data("t1_den")))
        self._t2 = Fraction(int(level.get_data("t2_num")), int(level.get_data("t2_den")))
        self._bad_check = False
        self._paint_ui()

    def _paint_ui(self) -> None:
        v1, v2 = _voltages(self._r0, self._r1, self._r2)
        self._ui.update(
            self._r0,
            self._r1,
            self._r2,
            v1.numerator,
            v1.denominator,
            v2.numerator,
            v2.denominator,
            self._t1.numerator,
            self._t1.denominator,
            self._t2.numerator,
            self._t2.denominator,
            bad_check=self._bad_check,
            level_index=self.level_index,
            num_levels=len(levels),
        )

    def step(self) -> None:
        aid = self.action.id
        if aid == GameAction.ACTION1:
            self._r0 = _cycle_r(self._r0)
            self._bad_check = False
            self._paint_ui()
        elif aid == GameAction.ACTION2:
            self._r1 = _cycle_r(self._r1)
            self._bad_check = False
            self._paint_ui()
        elif aid == GameAction.ACTION3:
            self._r2 = _cycle_r(self._r2)
            self._bad_check = False
            self._paint_ui()
        elif aid == GameAction.ACTION5:
            v1, v2 = _voltages(self._r0, self._r1, self._r2)
            if v1 == self._t1 and v2 == self._t2:
                self.next_level()
            else:
                self._bad_check = True
                self._paint_ui()
        self.complete_action()
