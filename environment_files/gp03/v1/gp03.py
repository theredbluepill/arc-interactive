"""Three-state grid paint: ACTION6 cycles each cell empty / yellow / orange; match per-cell goal in level data."""

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
WALL_C = 3
CAM = 16


class Gp03UI(RenderableUserDisplay):
    def __init__(self, ok: int, tot: int) -> None:
        self._ok = ok
        self._tot = tot

    def update(self, ok: int, tot: int) -> None:
        self._ok = ok
        self._tot = tot

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for i in range(min(self._tot, 10)):
            frame[1, 1 + i] = 14 if i < self._ok else 8
        return frame


sprites = {
    "wall": Sprite(
        pixels=[[WALL_C]],
        name="wall",
        visible=True,
        collidable=True,
        tags=["wall"],
    ),
}


def cell_sprite(st: int) -> Sprite | None:
    if st == 0:
        return None
    c = 11 if st == 1 else 12
    return Sprite(
        pixels=[[c]],
        name="paint",
        visible=True,
        collidable=False,
        tags=["paint"],
    )


def mk(walls: list[tuple[int, int]], goal: dict[tuple[int, int], int], d: int):
    sl: list[Sprite] = []
    for wx, wy in walls:
        sl.append(sprites["wall"].clone().set_position(wx, wy))
    gk = {f"{x},{y}": v for (x, y), v in goal.items()}
    return Level(
        sprites=sl,
        grid_size=(8, 8),
        data={"difficulty": d, "goal": gk},
    )


levels = [
    mk([], {(2, 2): 1, (3, 2): 2, (2, 3): 1}, 1),
    mk([(4, 4)], {(1, 1): 2, (1, 2): 1, (6, 6): 1}, 2),
    mk([], {(x, 0): 1 for x in range(8)} | {(x, 7): 2 for x in range(8)}, 3),
    mk([(3, y) for y in range(8) if y != 4], {(0, 4): 1, (7, 4): 2, (4, 4): 1}, 4),
    mk([], {(i % 8, i // 8): (i % 3) for i in range(24)}, 5),
]


class Gp03(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Gp03UI(0, 1)
        super().__init__(
            "gp03",
            levels,
            Camera(0, 0, CAM, CAM, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 6],
        )

    def on_set_level(self, level: Level) -> None:
        raw = self.current_level.get_data("goal") or {}
        self._goal: dict[tuple[int, int], int] = {}
        for k, v in raw.items():
            if isinstance(k, str):
                a, b = k.split(",")
                self._goal[(int(a), int(b))] = int(v)
        # Avoid ``self._state`` — reserved on ARCBaseGame for GameState.
        self._paint: dict[tuple[int, int], int] = {p: 0 for p in self._goal}
        for s in list(self.current_level.get_sprites_by_tag("paint")):
            self.current_level.remove_sprite(s)
        self._sync_ui()

    def _sprite_at_cell(self, gx: int, gy: int) -> Sprite | None:
        for s in self.current_level.get_sprites_by_tag("paint"):
            if s.x == gx and s.y == gy:
                return s
        return None

    def _sync_ui(self) -> None:
        ok = sum(1 for p, g in self._goal.items() if self._paint.get(p, 0) == g)
        self._ui.update(ok, max(1, len(self._goal)))

    def _grid_to_frame_pixel(self, gx: int, gy: int) -> tuple[int, int]:
        cw, ch = self.camera.width, self.camera.height
        scale = min(64 // cw, 64 // ch)
        x_pad = (64 - cw * scale) // 2
        y_pad = (64 - ch * scale) // 2
        return gx * scale + scale // 2 + x_pad, gy * scale + scale // 2 + y_pad

    def step(self) -> None:
        if self.action.id.value in (1, 2, 3, 4):
            self.complete_action()
            return
        if self.action.id != GameAction.ACTION6:
            self.complete_action()
            return

        x = int(self.action.data.get("x", 0))
        y = int(self.action.data.get("y", 0))
        hit = self.camera.display_to_grid(x, y)
        if hit is None:
            self.complete_action()
            return
        gx, gy = int(hit[0]), int(hit[1])
        gw, gh = self.current_level.grid_size
        if not (0 <= gx < gw and 0 <= gy < gh):
            self.complete_action()
            return
        sp0 = self.current_level.get_sprite_at(gx, gy, ignore_collidable=True)
        if sp0 and "wall" in sp0.tags:
            self.complete_action()
            return
        if (gx, gy) not in self._goal:
            self.complete_action()
            return

        cur = self._paint.get((gx, gy), 0)
        nxt = (cur + 1) % 3
        self._paint[(gx, gy)] = nxt
        old = self._sprite_at_cell(gx, gy)
        if old:
            self.current_level.remove_sprite(old)
        ns = cell_sprite(nxt)
        if ns:
            self.current_level.add_sprite(ns.set_position(gx, gy))

        self._sync_ui()
        if all(self._paint.get(p, 0) == g for p, g in self._goal.items()):
            self.next_level()

        self.complete_action()
