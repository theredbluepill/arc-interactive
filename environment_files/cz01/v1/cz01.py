"""Row pick: ACTION1–4 choose row 0–3; ACTION6 XOR-flips that row (binary grid). Match target."""

from __future__ import annotations

from arcengine import ARCBaseGame, Camera, GameAction, Level, RenderableUserDisplay, Sprite

BG, PAD = 5, 4
GW, GH = 8, 8
CAM = 16
ROWS = 4
WALL_C = 3
ON, OFF = 11, 2
TARG_ON, TARG_OFF = 6, 3


class Cz01UI(RenderableUserDisplay):
    def __init__(self, row: int, steps: int) -> None:
        self._row = row
        self._steps = steps
        self._target: list[list[int]] = [[0] * GW for _ in range(ROWS)]

    def update(
        self,
        row: int,
        steps: int,
        target: list[list[int]] | None = None,
    ) -> None:
        self._row = row
        self._steps = steps
        if target is not None:
            self._target = [r[:] for r in target]

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        frame[h - 2, 2 + self._row] = 10
        for i in range(min(self._steps, 15)):
            frame[h - 2, 8 + i] = 14
        ox, oy = 46, 4
        for yy in range(ROWS):
            for xx in range(GW):
                c = TARG_ON if self._target[yy][xx] else TARG_OFF
                if 0 <= ox + xx < w and 0 <= oy + yy < h:
                    frame[oy + yy, ox + xx] = c
        return frame


def cell(on: bool) -> Sprite:
    return Sprite(
        pixels=[[ON if on else OFF]],
        name="bit",
        visible=True,
        collidable=False,
        tags=["bit"],
    )


def mk(init: list[list[int]], targ: list[list[int]], max_steps: int, diff: int) -> Level:
    sl: list[Sprite] = []
    for y in range(ROWS, GH):
        for x in range(GW):
            sl.append(
                Sprite(
                    pixels=[[WALL_C]],
                    name="w",
                    visible=True,
                    collidable=True,
                    tags=["wall"],
                ).set_position(x, y),
            )
    return Level(
        sprites=sl,
        grid_size=(GW, GH),
        data={
            "difficulty": diff,
            "init": init,
            "target": targ,
            "max_steps": max_steps,
        },
    )


levels = [
    mk([[0] * GW for _ in range(ROWS)], [[1, 0, 0, 0, 0, 0, 0, 0], [0] * GW, [0] * GW, [0] * GW], 40, 1),
    mk([[0] * GW for _ in range(ROWS)], [[1, 1, 0, 0, 0, 0, 0, 0], [0, 0, 1, 1, 0, 0, 0, 0], [0] * GW, [0] * GW], 50, 2),
    mk([[1, 0, 1, 0, 1, 0, 1, 0] for _ in range(ROWS)], [[0] * GW for _ in range(ROWS)], 60, 3),
    mk([[0] * GW for _ in range(ROWS)], [[1 if x % 2 == 0 else 0 for x in range(GW)] for _ in range(ROWS)], 70, 4),
    mk([[0] * GW for _ in range(ROWS)], [[(x + y) % 2 for x in range(GW)] for y in range(ROWS)], 80, 5),
    mk([[0] * GW for _ in range(ROWS)], [[1, 1, 1, 0, 0, 0, 0, 0], [0, 0, 0, 1, 1, 1, 0, 0], [0] * GW, [0] * GW], 90, 6),
    mk([[1] * GW, [0] * GW, [1] * GW, [0] * GW], [[0] * GW for _ in range(ROWS)], 100, 7),
]


class Cz01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Cz01UI(0, 0)
        super().__init__(
            "cz01",
            levels,
            Camera(0, 0, CAM, CAM, BG, PAD, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 6],
        )

    def on_set_level(self, level: Level) -> None:
        self._g = [row[:] for row in self.current_level.get_data("init")]
        self._target = self.current_level.get_data("target")
        self._steps_left = int(self.current_level.get_data("max_steps") or 60)
        self._active_row = 0
        self._paint()
        self._ui.update(self._active_row, self._steps_left, target=self._target)

    def _paint(self) -> None:
        for s in list(self.current_level.get_sprites_by_tag("bit")):
            self.current_level.remove_sprite(s)
        for y in range(ROWS):
            for x in range(GW):
                self.current_level.add_sprite(
                    cell(bool(self._g[y][x])).set_position(x, y),
                )

    def _win(self) -> bool:
        for y in range(ROWS):
            for x in range(GW):
                if self._g[y][x] != self._target[y][x]:
                    return False
        return True

    def step(self) -> None:
        v = self.action.id.value
        if v in (1, 2, 3, 4):
            self._active_row = min(v - 1, ROWS - 1)
            self._ui.update(
                self._active_row,
                self._steps_left,
                target=self._target,
            )
            self.complete_action()
            return

        if self.action.id != GameAction.ACTION6:
            self.complete_action()
            return

        if self._steps_left <= 0:
            self.lose()
            self.complete_action()
            return

        for x in range(GW):
            self._g[self._active_row][x] ^= 1

        self._paint()
        self._steps_left -= 1
        self._ui.update(
            self._active_row,
            self._steps_left,
            target=self._target,
        )
        if self._win():
            self.next_level()

        self.complete_action()
