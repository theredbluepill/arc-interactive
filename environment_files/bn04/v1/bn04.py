"""bn04: hidden targets — ACTION5 toggles row/column reveal mode; ACTION6 reveals a full line."""

from __future__ import annotations

from arcengine import ARCBaseGame, Camera, GameAction, Level, RenderableUserDisplay, Sprite

BG, PAD = 5, 4
G = 8
CAM = 16
TGT = 11
HID = 2


class Bn04UI(RenderableUserDisplay):
    def __init__(self, row_mode: bool) -> None:
        self._r = row_mode

    def update(self, row_mode: bool) -> None:
        self._r = row_mode

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        frame[h - 2, 2] = 9 if self._r else 6
        return frame


def mk(targets: list[tuple[int, int]], d: int) -> Level:
    sl = [
        Sprite(
            pixels=[[HID]],
            name="h",
            visible=True,
            collidable=False,
            tags=["hid"],
        ).clone().set_position(x, y)
        for x, y in targets
    ]
    return Level(
        sprites=sl,
        grid_size=(G, G),
        data={"targets": [list(p) for p in targets], "difficulty": d},
    )


levels = [
    mk([(2, 2), (5, 5)], 1),
    mk([(1, 1), (3, 6), (6, 3)], 2),
    mk([(0, 0), (7, 7)], 3),
    mk([(2, 5), (5, 2), (4, 4)], 4),
    mk([(1, y) for y in range(2, 6)], 5),
    mk([(x, 4) for x in range(2, 6)], 6),
    mk([(2, 3), (5, 4), (3, 6), (6, 2)], 7),
]


class Bn04(ARCBaseGame):
    def __init__(self) -> None:
        self._hud = Bn04UI(True)
        super().__init__(
            "bn04",
            levels,
            Camera(0, 0, CAM, CAM, BG, PAD, [self._hud]),
            False,
            1,
            [5, 6],
        )

    def on_set_level(self, level: Level) -> None:
        self._tgt = {tuple(int(t) for t in p) for p in level.get_data("targets")}
        self._rev: set[tuple[int, int]] = set()
        self._row_mode = True
        self._hud.update(self._row_mode)

    def _flash(self, cells: set[tuple[int, int]]) -> None:
        self._rev |= cells & self._tgt

    def step(self) -> None:
        if self.action.id == GameAction.ACTION5:
            self._row_mode = not self._row_mode
            self._hud.update(self._row_mode)
            self.complete_action()
            return
        if self.action.id == GameAction.ACTION6:
            c = self.camera.display_to_grid(
                self.action.data.get("x", 0), self.action.data.get("y", 0)
            )
            if c:
                gx, gy = int(c[0]), int(c[1])
                if self._row_mode:
                    self._flash({(x, gy) for x in range(G)})
                else:
                    self._flash({(gx, y) for y in range(G)})
                if self._tgt <= self._rev:
                    self.next_level()
            self.complete_action()
            return
        self.complete_action()
