"""Quad twist: 6×6 tiles with states 0–3 (hue). ACTION6 on a cell rotates the 2×2 block anchored there clockwise. Match the target pattern in level data."""

from __future__ import annotations

from arcengine import (
    ARCBaseGame,
    Camera,
    GameAction,
    Level,
    RenderableUserDisplay,
    Sprite,
)

BACKGROUND_COLOR = 5
PADDING_COLOR = 4
GW = GH = 8
CAM = 16
WALL_C = 3
BASE = [2, 6, 9, 11]


class Qr01UI(RenderableUserDisplay):
    def __init__(self, steps: int) -> None:
        self._steps = steps

    def update(self, steps: int) -> None:
        self._steps = steps

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for i in range(min(self._steps, 15)):
            frame[h - 2, 1 + i] = 10
        return frame


def cell_sprite(st: int) -> Sprite:
    return Sprite(
        pixels=[[BASE[st % 4]]],
        name="qt",
        visible=True,
        collidable=False,
        tags=["qtile"],
    )


def mk(
    walls: list[tuple[int, int]],
    init: list[list[int]],
    target: list[list[int]],
    max_steps: int,
    diff: int,
) -> Level:
    sl = []
    for wx, wy in walls:
        sl.append(
            Sprite(
                pixels=[[WALL_C]],
                name="wall",
                visible=True,
                collidable=True,
                tags=["wall"],
            ).set_position(wx, wy),
        )
    return Level(
        sprites=sl,
        grid_size=(GW, GH),
        data={
            "difficulty": diff,
            "init": init,
            "target": target,
            "max_steps": max_steps,
        },
    )


def _board(z: int) -> list[list[int]]:
    return [[(x + y + z) % 4 for x in range(GW)] for y in range(GH)]


levels = [
    mk([], _board(0), _board(1), 120, 1),
    mk([(4, y) for y in range(8)], _board(2), _board(3), 150, 2),
    mk([], [[0] * GW for _ in range(GH)], [[1] * GW for _ in range(GH)], 200, 3),
    mk([(x, 4) for x in range(8) if x != 4], _board(1), _board(0), 180, 4),
    mk([], _board(3), _board(0), 220, 5),
]


class Qr01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Qr01UI(0)
        super().__init__(
            "qr01",
            levels,
            Camera(0, 0, CAM, CAM, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 6],
        )

    def on_set_level(self, level: Level) -> None:
        self._g = [row[:] for row in self.current_level.get_data("init")]
        self._target = self.current_level.get_data("target")
        self._steps_left = int(self.current_level.get_data("max_steps") or 150)
        self._paint()

    def _paint(self) -> None:
        for s in list(self.current_level.get_sprites_by_tag("qtile")):
            self.current_level.remove_sprite(s)
        for y in range(GH):
            for x in range(GW):
                sp = self.current_level.get_sprite_at(x, y, ignore_collidable=True)
                if sp and "wall" in sp.tags:
                    continue
                self.current_level.add_sprite(
                    cell_sprite(self._g[y][x]).set_position(x, y),
                )

    def _win(self) -> bool:
        for y in range(GH):
            for x in range(GW):
                sp = self.current_level.get_sprite_at(x, y, ignore_collidable=True)
                if sp and "wall" in sp.tags:
                    continue
                if self._g[y][x] != self._target[y][x]:
                    return False
        return True

    def step(self) -> None:
        if self.action.id.value in (1, 2, 3, 4):
            self.complete_action()
            return

        if self.action.id != GameAction.ACTION6:
            self.complete_action()
            return

        if self._steps_left <= 0:
            self.lose()
            self.complete_action()
            return

        px = self.action.data.get("x", 0)
        py = self.action.data.get("y", 0)
        coords = self.camera.display_to_grid(px, py)
        if not coords:
            self.complete_action()
            return
        gx, gy = coords
        if gx + 1 >= GW or gy + 1 >= GH:
            self.complete_action()
            return
        for dy in (0, 1):
            for dx in (0, 1):
                sp = self.current_level.get_sprite_at(gx + dx, gy + dy, ignore_collidable=True)
                if sp and "wall" in sp.tags:
                    self.complete_action()
                    return

        a = self._g[gy][gx]
        b = self._g[gy][gx + 1]
        c = self._g[gy + 1][gx]
        d = self._g[gy + 1][gx + 1]
        self._g[gy][gx] = c
        self._g[gy][gx + 1] = a
        self._g[gy + 1][gx] = d
        self._g[gy + 1][gx + 1] = b

        self._paint()
        self._steps_left -= 1
        self._ui.update(self._steps_left)
        if self._win():
            self.next_level()

        self.complete_action()
