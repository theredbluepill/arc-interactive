"""Stencil paint: a 3×3 stencil moves with ACTION1–4; ACTION5 paints every non-wall cell under the stencil yellow. Match all gray hint cells."""

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
CAM_W = CAM_H = 64
WALL_C = 3
HINT_C = 2
PAINT_C = 11


class Sf01UI(RenderableUserDisplay):
    def __init__(self, ok: int, total: int, steps: int) -> None:
        self._ok = ok
        self._total = total
        self._steps = steps

    def update(self, ok: int, total: int, steps: int) -> None:
        self._ok = ok
        self._total = total
        self._steps = steps

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for i in range(min(self._total, 16)):
            frame[1, 1 + i * 2] = 14 if i < self._ok else 8
        for i in range(min(self._steps, 40)):
            frame[2, 1 + i] = 10
        return frame


sprites = {
    "wall": Sprite(
        pixels=[[WALL_C]],
        name="wall",
        visible=True,
        collidable=True,
        tags=["wall"],
    ),
    "hint": Sprite(
        pixels=[[HINT_C]],
        name="hint",
        visible=True,
        collidable=False,
        tags=["hint"],
    ),
    "paint": Sprite(
        pixels=[[PAINT_C]],
        name="paint",
        visible=True,
        collidable=False,
        tags=["paint"],
    ),
}


def mk(
    goal: list[tuple[int, int]],
    walls: list[tuple[int, int]],
    start_stencil: tuple[int, int],
    max_steps: int,
    diff: int,
) -> Level:
    sl: list[Sprite] = []
    for wx, wy in walls:
        sl.append(sprites["wall"].clone().set_position(wx, wy))
    for gx, gy in goal:
        sl.append(sprites["hint"].clone().set_position(gx, gy))
    return Level(
        sprites=sl,
        grid_size=(CAM_W, CAM_H),
        data={
            "difficulty": diff,
            "goal_cells": [list(p) for p in goal],
            "stencil_x": start_stencil[0],
            "stencil_y": start_stencil[1],
            "max_steps": max_steps,
        },
    )


def _box(cx: int, cy: int, r: int) -> list[tuple[int, int]]:
    return [(x, y) for x in range(cx - r, cx + r + 1) for y in range(cy - r, cy + r + 1)]


levels = [
    mk(_box(32, 32, 1), [], (31, 31), 400, 1),
    mk(_box(40, 32, 2), [(x, 20) for x in range(30, 45)], (10, 10), 500, 2),
    mk([(30 + i, 30) for i in range(6)] + [(30, 31), (35, 31)], [], (28, 28), 600, 3),
    mk(
        [(20 + i, 20) for i in range(8)]
        + [(20, 21 + j) for j in range(8)]
        + [(27, 21 + j) for j in range(8)],
        [(24, 22), (24, 25)],
        (18, 18),
        700,
        4,
    ),
    mk(
        [(32 + (i % 4) * 2, 32 + (i // 4) * 2) for i in range(16)],
        [(50, y) for y in range(40, 56)],
        (20, 20),
        800,
        5,
    ),
]


class Sf01(ARCBaseGame):
    ST = 3

    def __init__(self) -> None:
        self._ui = Sf01UI(0, 1, 0)
        super().__init__(
            "sf01",
            levels,
            Camera(0, 0, CAM_W, CAM_H, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 5],
        )

    def on_set_level(self, level: Level) -> None:
        raw = self.current_level.get_data("goal_cells") or []
        self._goal = {tuple(int(t) for t in p) for p in raw}
        self._sx = int(self.current_level.get_data("stencil_x") or 0)
        self._sy = int(self.current_level.get_data("stencil_y") or 0)
        self._steps = int(self.current_level.get_data("max_steps") or 500)
        self._clamp_stencil()
        self._sync_ui()

    def _clamp_stencil(self) -> None:
        gw, gh = self.current_level.grid_size
        self._sx = max(0, min(gw - self.ST, self._sx))
        self._sy = max(0, min(gh - self.ST, self._sy))

    def _painted(self) -> set[tuple[int, int]]:
        return {(s.x, s.y) for s in self.current_level.get_sprites_by_tag("paint")}

    def _sync_ui(self) -> None:
        painted = self._painted()
        ok = len(self._goal & painted)
        self._ui.update(ok, max(1, len(self._goal)), self._steps)

    def _burn(self) -> bool:
        self._steps -= 1
        self._sync_ui()
        if self._steps <= 0:
            self.lose()
            return True
        return False

    def step(self) -> None:
        aid = self.action.id

        if aid == GameAction.ACTION1:
            self._sy = max(0, self._sy - 1)
            if self._burn():
                self.complete_action()
                return
            self.complete_action()
            return
        if aid == GameAction.ACTION2:
            gh = self.current_level.grid_size[1]
            self._sy = min(gh - self.ST, self._sy + 1)
            if self._burn():
                self.complete_action()
                return
            self.complete_action()
            return
        if aid == GameAction.ACTION3:
            self._sx = max(0, self._sx - 1)
            if self._burn():
                self.complete_action()
                return
            self.complete_action()
            return
        if aid == GameAction.ACTION4:
            gw = self.current_level.grid_size[0]
            self._sx = min(gw - self.ST, self._sx + 1)
            if self._burn():
                self.complete_action()
                return
            self.complete_action()
            return

        if aid != GameAction.ACTION5:
            self.complete_action()
            return

        for dy in range(self.ST):
            for dx in range(self.ST):
                gx, gy = self._sx + dx, self._sy + dy
                sp = self.current_level.get_sprite_at(gx, gy, ignore_collidable=True)
                if sp and "wall" in sp.tags:
                    continue
                old = next(
                    (
                        p
                        for p in self.current_level.get_sprites_by_tag("paint")
                        if p.x == gx and p.y == gy
                    ),
                    None,
                )
                if old:
                    self.current_level.remove_sprite(old)
                self.current_level.add_sprite(
                    sprites["paint"].clone().set_position(gx, gy),
                )

        if self._burn():
            self.complete_action()
            return
        self._sync_ui()
        if self._goal <= self._painted():
            self.next_level()
        self.complete_action()
