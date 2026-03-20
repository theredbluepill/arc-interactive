"""ph04: one row of residues mod R; ACTION5 replaces row[i] with (row[i]+row[i+1])%R (cyclic)."""

from __future__ import annotations

from arcengine import ARCBaseGame, Camera, GameAction, Level, RenderableUserDisplay, Sprite

BG, PAD = 5, 4
N = 8
CAM = 16


class Ph04UI(RenderableUserDisplay):
    def __init__(self, steps: int) -> None:
        self._s = steps

    def update(self, steps: int) -> None:
        self._s = steps

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for i in range(min(self._s, 20)):
            frame[h - 2, 1 + i] = 10
        return frame


def cell(c: int, x: int, y: int) -> Sprite:
    v = min(15, 5 + c)
    return Sprite(
        pixels=[[v]], name="c", visible=True, collidable=False, tags=["cell"]
    ).clone().set_position(x, y)


def mk(init: list[int], target: list[int], R: int, max_steps: int, d: int) -> Level:
    sl = [cell(init[i], i, 8) for i in range(N)]
    return Level(
        sprites=sl,
        grid_size=(CAM, CAM),
        data={
            "init": list(init),
            "target": list(target),
            "R": R,
            "max_steps": max_steps,
            "difficulty": d,
        },
    )


levels = [
    mk([0, 1, 0, 0, 0, 0, 0, 0], [1, 1, 0, 0, 0, 0, 0, 0], 3, 40, 1),
    mk([1, 1, 1, 0, 0, 0, 0, 0], [0, 2, 1, 0, 0, 0, 0, 0], 3, 50, 2),
    mk([2, 2, 0, 0, 0, 0, 0, 0], [1, 1, 0, 0, 0, 0, 0, 0], 3, 45, 3),
    mk([1, 0, 1, 0, 1, 0, 1, 0], [0, 1, 0, 1, 0, 1, 0, 1], 2, 60, 4),
    mk([3, 3, 3, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0], 4, 55, 5),
    mk([1, 2, 3, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0], 4, 70, 6),
    mk([2, 0, 2, 0, 2, 0, 2, 0], [0, 0, 0, 0, 0, 0, 0, 0], 2, 65, 7),
]


class Ph04(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Ph04UI(0)
        super().__init__(
            "ph04",
            levels,
            Camera(0, 0, CAM, CAM, BG, PAD, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 5],
        )

    def on_set_level(self, level: Level) -> None:
        self._row = [int(x) for x in level.get_data("init")]
        self._target = [int(x) for x in level.get_data("target")]
        self._R = int(level.get_data("R") or 3)
        self._left = int(level.get_data("max_steps") or 50)
        self._ref()

    def _ref(self) -> None:
        for s in list(self.current_level.get_sprites_by_tag("cell")):
            self.current_level.remove_sprite(s)
        for i, v in enumerate(self._row):
            self.current_level.add_sprite(cell(v, i, 8))
        self._ui.update(self._left)

    def _win(self) -> bool:
        return self._row == self._target

    def step(self) -> None:
        if self.action.id == GameAction.ACTION5:
            if self._left <= 0:
                self.lose()
                self.complete_action()
                return
            nxt = [
                (self._row[i] + self._row[(i + 1) % N]) % self._R for i in range(N)
            ]
            self._row = nxt
            self._left -= 1
            self._ref()
            if self._win():
                self.next_level()
            elif self._left <= 0:
                self.lose()
            self.complete_action()
            return
        self.complete_action()
