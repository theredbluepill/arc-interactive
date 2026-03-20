"""ih01: heat grid; ACTION5 global chill; ACTION6 toggles heaters on marked cells."""

from __future__ import annotations

from arcengine import ARCBaseGame, Camera, GameAction, Level, RenderableUserDisplay, Sprite

BG, PAD = 5, 4
G = 10
CAM = 16
HEAT = 12
OFF = 4


class Ih01UI(RenderableUserDisplay):
    def __init__(self, ok: int, need: int) -> None:
        self._ok, self._need = ok, need

    def update(self, ok: int, need: int) -> None:
        self._ok, self._need = ok, need

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for i in range(min(self._need, 10)):
            frame[h - 2, 1 + i] = 14 if i < self._ok else 8
        return frame


def mk(
    pads: list[tuple[int, int]],
    min_warm: int,
    max_steps: int,
    d: int,
) -> Level:
    sl = [
        Sprite(
            pixels=[[OFF]],
            name="h",
            visible=True,
            collidable=False,
            tags=["heater_pad"],
        ).clone().set_position(x, y)
        for x, y in pads
    ]
    return Level(
        sprites=sl,
        grid_size=(G, G),
        data={
            "heater_pads": [list(p) for p in pads],
            "min_warm": min_warm,
            "max_steps": max_steps,
            "difficulty": d,
        },
    )


levels = [
    mk([(3, 3), (6, 6)], 4, 60, 1),
    mk([(2, 2), (7, 7), (5, 5)], 5, 70, 2),
    mk([(1, 1), (8, 8)], 6, 80, 3),
    mk([(2, 5), (7, 5), (5, 2), (5, 8)], 5, 90, 4),
    mk([(4, 4)], 7, 50, 5),
    mk([(3, 6), (6, 3)], 5, 75, 6),
    mk([(1, 3), (8, 6), (4, 7)], 6, 100, 7),
]


class Ih01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Ih01UI(0, 1)
        super().__init__(
            "ih01",
            levels,
            Camera(0, 0, CAM, CAM, BG, PAD, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 5, 6],
        )

    def on_set_level(self, level: Level) -> None:
        raw = level.get_data("heater_pads") or []
        self._pads = {tuple(int(t) for t in p) for p in raw}
        self._on: set[tuple[int, int]] = set()
        self._h = [[0 for _ in range(G)] for _ in range(G)]
        self._minw = int(level.get_data("min_warm") or 4)
        self._left = int(level.get_data("max_steps") or 60)
        self._sync()

    def _sync(self) -> None:
        ok = sum(1 for y in range(G) for x in range(G) if self._h[y][x] >= self._minw)
        self._ui.update(ok, G * G)

    def _tick(self) -> None:
        for y in range(G):
            for x in range(G):
                if (x, y) in self._on:
                    self._h[y][x] = min(15, self._h[y][x] + 2)
                else:
                    self._h[y][x] = max(0, self._h[y][x] - 1)
                for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < G and 0 <= ny < G and (nx, ny) in self._on:
                        self._h[y][x] = min(15, self._h[y][x] + 1)

    def _win(self) -> bool:
        return all(self._h[y][x] >= self._minw for y in range(G) for x in range(G))

    def step(self) -> None:
        if self.action.id == GameAction.ACTION5:
            self._tick()
            self._left -= 1
            self._sync()
            if self._win():
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
                gx, gy = int(c[0]), int(c[1])
                if (gx, gy) in self._pads:
                    if (gx, gy) in self._on:
                        self._on.remove((gx, gy))
                    else:
                        self._on.add((gx, gy))
            self._left -= 1
            self._sync()
            if self._win():
                self.next_level()
            elif self._left <= 0:
                self.lose()
            self.complete_action()
            return
        self.complete_action()
