"""df04: no avatar — ACTION5 diffuses heat; ACTION6 vents 3×3; probe in goal band."""

from __future__ import annotations

from arcengine import ARCBaseGame, Camera, GameAction, Level, RenderableUserDisplay, Sprite

BG, PAD = 5, 4
G = 10
CAM = 16
SRC = 8


class Df04UI(RenderableUserDisplay):
    def __init__(self, t: int, lo: int, hi: int) -> None:
        self._t, self._lo, self._hi = t, lo, hi

    def update(self, t: int, lo: int, hi: int) -> None:
        self._t, self._lo, self._hi = t, lo, hi

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        c = 14 if self._lo <= self._t <= self._hi else 8
        frame[h - 2, 3] = c
        return frame


def mk(
    sources: list[tuple[int, int]],
    px: int,
    py: int,
    lo: int,
    hi: int,
    max_steps: int,
    d: int,
) -> Level:
    sl = [
        Sprite(
            pixels=[[SRC]], name="s", visible=True, collidable=False, tags=["src"]
        ).clone().set_position(x, y)
        for x, y in sources
    ]
    return Level(
        sprites=sl,
        grid_size=(G, G),
        data={
            "sources": [list(p) for p in sources],
            "probe": [px, py],
            "lo": lo,
            "hi": hi,
            "max_steps": max_steps,
            "difficulty": d,
        },
    )


levels = [
    mk([(2, 2), (7, 7)], 5, 5, 3, 8, 80, 1),
    mk([(1, 1), (8, 8)], 4, 4, 2, 9, 100, 2),
    mk([(0, 5), (9, 5)], 5, 5, 4, 7, 90, 3),
    mk([(3, 3), (6, 6), (3, 6)], 5, 5, 5, 7, 110, 4),
    mk([(2, 8), (8, 2)], 5, 5, 4, 8, 120, 5),
    mk([(4, 4)], 5, 5, 6, 9, 100, 6),
    mk([(1, 3), (7, 6), (4, 8)], 5, 5, 5, 8, 130, 7),
]


class Df04(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Df04UI(0, 0, 15)
        super().__init__(
            "df04",
            levels,
            Camera(0, 0, CAM, CAM, BG, PAD, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 5, 6],
        )

    def on_set_level(self, level: Level) -> None:
        self._src = {tuple(int(t) for t in p) for p in level.get_data("sources")}
        pr = level.get_data("probe")
        self._px, self._py = int(pr[0]), int(pr[1])
        self._lo = int(level.get_data("lo") or 0)
        self._hi = int(level.get_data("hi") or 10)
        self._left = int(level.get_data("max_steps") or 100)
        self._t = [[0 for _ in range(G)] for _ in range(G)]
        self._sync()

    def _sync(self) -> None:
        v = self._t[self._py][self._px]
        self._ui.update(v, self._lo, self._hi)

    def _diffuse(self) -> None:
        nxt = [[0.0 for _ in range(G)] for _ in range(G)]
        for y in range(G):
            for x in range(G):
                if (x, y) in self._src:
                    nxt[y][x] = min(15, self._t[y][x] + 2)
                    continue
                s = self._t[y][x]
                n = 0
                for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < G and 0 <= ny < G:
                        s += self._t[ny][nx]
                        n += 1
                nxt[y][x] = int(round(s / max(1, n + 1))) if n else self._t[y][x]
        self._t = [[min(15, int(v)) for v in row] for row in nxt]

    def _vent(self, cx: int, cy: int) -> None:
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                x, y = cx + dx, cy + dy
                if 0 <= x < G and 0 <= y < G:
                    self._t[y][x] = max(0, self._t[y][x] - 3)

    def step(self) -> None:
        if self.action.id == GameAction.ACTION5:
            self._diffuse()
            self._left -= 1
            self._sync()
            if self._lo <= self._t[self._py][self._px] <= self._hi:
                self.next_level()
            elif self._left <= 0:
                self.lose()
            self.complete_action()
            return
        if self.action.id == GameAction.ACTION6:
            c = self.camera.display_to_grid(
                self.action.data.get("x", 0), self.action.data.get("y", 0)
            )
            if c:
                self._vent(int(c[0]), int(c[1]))
            self._left -= 1
            self._sync()
            if self._lo <= self._t[self._py][self._px] <= self._hi:
                self.next_level()
            elif self._left <= 0:
                self.lose()
            self.complete_action()
            return
        self.complete_action()
