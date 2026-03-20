"""pt04: swap two 1×1 color cells per two clicks; match target bitmap."""

from __future__ import annotations

from arcengine import ARCBaseGame, Camera, GameAction, Level, RenderableUserDisplay, Sprite

BG, PAD = 5, 4
GW, GH = 8, 8
CAM = 16


def cell_sprite(c: int) -> Sprite:
    return Sprite(
        pixels=[[c]],
        name="cell",
        visible=True,
        collidable=False,
        tags=["cell"],
    )


BASE = cell_sprite(0)


class Pt04UI(RenderableUserDisplay):
    def __init__(self, sel: tuple[int, int] | None) -> None:
        self._sel = sel

    def update(self, sel: tuple[int, int] | None) -> None:
        self._sel = sel

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        if self._sel:
            sx, sy = self._sel
            scale = min(64 // CAM, 64 // CAM)
            pad = (64 - CAM * scale) // 2
            px = sx * scale + pad
            py = sy * scale + pad
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                x, y = px + dx, py + dy
                if 0 <= x < w and 0 <= y < h:
                    frame[y, x] = 0
        return frame


def level_from_grids(init: list[list[int]], target: list[list[int]], diff: int) -> Level:
    sl: list[Sprite] = []
    for y in range(GH):
        for x in range(GW):
            c = init[y][x]
            sl.append(cell_sprite(c).clone().set_position(x, y))
    return Level(
        sprites=sl,
        grid_size=(GW, GH),
        data={
            "difficulty": diff,
            "target": [list(row) for row in target],
        },
    )


def z() -> list[list[int]]:
    return [[3 for _ in range(GW)] for _ in range(GH)]


levels = [
    level_from_grids(
        [[3, 3, 9, 3, 3, 3, 3, 3]] + [[3] * GW for _ in range(7)],
        [[3, 3, 3, 3, 9, 3, 3, 3]] + [[3] * GW for _ in range(7)],
        1,
    ),
    level_from_grids(
        [[9, 11, 3, 3, 3, 3, 3, 3], [11, 9, 3, 3, 3, 3, 3, 3]] + [[3] * GW for _ in range(6)],
        [[11, 9, 3, 3, 3, 3, 3, 3], [9, 11, 3, 3, 3, 3, 3, 3]] + [[3] * GW for _ in range(6)],
        2,
    ),
    level_from_grids(z(), [[14 if x == y else 3 for x in range(GW)] for y in range(GH)], 3),
    level_from_grids(
        [[10, 3, 3, 3, 3, 3, 3, 3]] + [[3] * GW for _ in range(7)],
        [[3, 3, 3, 3, 3, 3, 3, 10]] + [[3] * GW for _ in range(7)],
        4,
    ),
    level_from_grids(
        [[3, 3, 3, 8, 3, 3, 3, 3]] * 2 + [[3] * GW for _ in range(6)],
        [[3, 3, 8, 3, 3, 3, 3, 3]] * 2 + [[3] * GW for _ in range(6)],
        5,
    ),
    level_from_grids(
        [[9, 11, 14, 3, 3, 3, 3, 3], [11, 14, 9, 3, 3, 3, 3, 3], [14, 9, 11, 3, 3, 3, 3, 3]]
        + [[3] * GW for _ in range(5)],
        [[11, 9, 14, 3, 3, 3, 3, 3], [14, 11, 9, 3, 3, 3, 3, 3], [9, 14, 11, 3, 3, 3, 3, 3]]
        + [[3] * GW for _ in range(5)],
        6,
    ),
    level_from_grids(
        [[12 if x < 4 else 3 for x in range(GW)] for y in range(GH)],
        [[12 if x >= 4 else 3 for x in range(GW)] for y in range(GH)],
        7,
    ),
]


class Pt04(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Pt04UI(None)
        self._sel: tuple[int, int] | None = None
        super().__init__(
            "pt04",
            levels,
            Camera(0, 0, CAM, CAM, BG, PAD, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 6],
        )

    def on_set_level(self, level: Level) -> None:
        self._target = level.get_data("target")
        self._sel = None
        self._ui.update(None)
        self._sprite_at: dict[tuple[int, int], Sprite] = {}
        for sp in self.current_level.get_sprites_by_tag("cell"):
            self._sprite_at[(sp.x, sp.y)] = sp

    def _color_at(self, x: int, y: int) -> int:
        px = self._sprite_at[(x, y)].pixels[0][0]
        return int(px)

    def _set_color(self, x: int, y: int, c: int) -> None:
        sp = self._sprite_at[(x, y)]
        sp.pixels = [[c]]

    def _win(self) -> bool:
        for y in range(GH):
            for x in range(GW):
                if self._color_at(x, y) != self._target[y][x]:
                    return False
        return True

    def step(self) -> None:
        if self.action.id == GameAction.ACTION6:
            coords = self.camera.display_to_grid(
                self.action.data.get("x", 0), self.action.data.get("y", 0)
            )
            if not coords:
                self.complete_action()
                return
            gx, gy = coords
            if not (0 <= gx < GW and 0 <= gy < GH):
                self.complete_action()
                return
            if self._sel is None:
                self._sel = (gx, gy)
                self._ui.update(self._sel)
            else:
                ax, ay = self._sel
                if (ax, ay) != (gx, gy):
                    ca, cb = self._color_at(ax, ay), self._color_at(gx, gy)
                    self._set_color(ax, ay, cb)
                    self._set_color(gx, gy, ca)
                self._sel = None
                self._ui.update(None)
                if self._win():
                    self.next_level()
            self.complete_action()
            return
        self.complete_action()
