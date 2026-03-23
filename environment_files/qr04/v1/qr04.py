"""3×3 twist: tiles 0–3. ACTION6 rotates the 3×3 block anchored at top-left of click clockwise. Match target."""

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


class Qr04UI(RenderableUserDisplay):
    def __init__(self, steps: int, target: list[list[int]]) -> None:
        self._steps = steps
        self._target = target
        self._reject_frames = 0
        self._click: tuple[int, int] | None = None

    def update(self, steps: int, target: list[list[int]]) -> None:
        self._steps = steps
        self._target = target

    def set_click(self, fx: int, fy: int) -> None:
        self._click = (fx, fy)

    def flash_reject(self, frames: int = 8) -> None:
        self._reject_frames = frames

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for yy in range(GH):
            for xx in range(GW):
                px, py = 1 + xx, h - 10 + yy
                if 0 <= px < w and 0 <= py < h:
                    frame[py, px] = int(BASE[self._target[yy][xx] % 4])
        for i in range(min(self._steps, 15)):
            frame[h - 2, 1 + i] = 10
        if self._reject_frames > 0:
            for dx in range(3):
                for dy in range(2):
                    px, py = w - 3 + dx, dy
                    if 0 <= px < w and 0 <= py < h:
                        frame[py, px] = 8
            self._reject_frames -= 1
        if self._click:
            cx, cy = self._click
            for dx, dy in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
                px, py = cx + dx, cy + dy
                if 0 <= px < w and 0 <= py < h:
                    frame[py, px] = 11
            self._click = None
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
    mk([(0, y) for y in range(8)], _board(2), _board(1), 200, 6),
    mk([(7, y) for y in range(8)] + [(x, 0) for x in range(1, 7)], _board(0), _board(2), 240, 7),
]


class Qr04(ARCBaseGame):
    def __init__(self) -> None:
        z = [[0] * GW for _ in range(GH)]
        self._ui = Qr04UI(0, z)
        super().__init__(
            "qr04",
            levels,
            Camera(0, 0, CAM, CAM, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [6],
        )

    def _grid_to_frame_pixel(self, gx: int, gy: int) -> tuple[int, int]:
        cam = self.camera
        cw, ch = cam.width, cam.height
        scale = min(int(64 / cw), int(64 / ch))
        x_pad = int((64 - (cw * scale)) / 2)
        y_pad = int((64 - (ch * scale)) / 2)
        px = gx * scale + scale // 2 + x_pad
        py = gy * scale + scale // 2 + y_pad
        return px, py

    def on_set_level(self, level: Level) -> None:
        self._g = [row[:] for row in self.current_level.get_data("init")]
        self._target = self.current_level.get_data("target")
        self._steps_left = int(self.current_level.get_data("max_steps") or 150)
        self._ui.update(self._steps_left, self._target)
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
            self._ui.flash_reject()
            self.complete_action()
            return
        gx, gy = coords
        self._ui.set_click(*self._grid_to_frame_pixel(gx, gy))
        if gx + 2 >= GW or gy + 2 >= GH:
            self._ui.flash_reject()
            self.complete_action()
            return
        for dy in (0, 1, 2):
            for dx in (0, 1, 2):
                sp = self.current_level.get_sprite_at(
                    gx + dx, gy + dy, ignore_collidable=True
                )
                if sp and "wall" in sp.tags:
                    self._ui.flash_reject()
                    self.complete_action()
                    return

        sub = [[self._g[gy + j][gx + i] for i in range(3)] for j in range(3)]
        ns = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        for i in range(3):
            for j in range(3):
                ns[j][i] = sub[2 - i][j]
        for j in range(3):
            for i in range(3):
                self._g[gy + j][gx + i] = ns[j][i]

        self._paint()
        self._steps_left -= 1
        self._ui.update(self._steps_left, self._target)
        if self._win():
            self.next_level()

        self.complete_action()
