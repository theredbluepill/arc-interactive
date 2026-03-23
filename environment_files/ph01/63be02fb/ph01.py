"""Phase interference: each cell holds phase 0–3. ACTION6 increments a cell; ACTION5 applies a global blur (cell + sum of orthogonal neighbors, mod 4). Match the target phases on marked cells."""

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
CAM_W = CAM_H = 24
WALL_C = 3

# Phase colors (match _palette_sprite); used in HUD for target vs live on marks.
_PHASE_PALETTE = (0, 6, 9, 11)


class Ph01UI(RenderableUserDisplay):
    """Blur budget, mark outlines, per-mark target/current phase ticks, idle ping for ACTION1–4."""

    IDLE_FRAMES = 6

    def __init__(self, cam_w: int, cam_h: int) -> None:
        self._cam_w = cam_w
        self._cam_h = cam_h
        self._rounds = 0
        self._marks: list[tuple[int, int, int, int]] = []
        self._idle = 0

    def update(
        self,
        rounds: int,
        marks: list[tuple[int, int, int, int]] | None = None,
        *,
        idle_flash: bool = False,
    ) -> None:
        self._rounds = rounds
        if marks is not None:
            self._marks = marks
        if idle_flash:
            self._idle = self.IDLE_FRAMES

    def _grid_to_frame_bounds(self, gx: int, gy: int) -> tuple[int, int, int, int]:
        scale = max(1, min(64 // self._cam_w, 64 // self._cam_h))
        x_pad = (64 - self._cam_w * scale) // 2
        y_pad = (64 - self._cam_h * scale) // 2
        x0 = gx * scale + x_pad
        y0 = gy * scale + y_pad
        x1 = x0 + scale - 1
        y1 = y0 + scale - 1
        return x0, y0, x1, y1

    @staticmethod
    def _plot(frame, h: int, w: int, px: int, py: int, c: int) -> None:
        if 0 <= px < w and 0 <= py < h:
            frame[py, px] = c

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for i in range(min(self._rounds, 25)):
            self._plot(frame, h, w, 1 + i, h - 2, 10)

        if self._idle > 0:
            self._plot(frame, h, w, w - 2, h - 2, 11)
            self._idle -= 1

        gray = 2
        for gx, gy, target_ph, cur_ph in self._marks:
            x0, y0, x1, y1 = self._grid_to_frame_bounds(gx, gy)
            for px in range(x0, min(x1 + 1, w)):
                self._plot(frame, h, w, px, y0, gray)
                self._plot(frame, h, w, px, y1, gray)
            for py in range(y0, min(y1 + 1, h)):
                self._plot(frame, h, w, x0, py, gray)
                self._plot(frame, h, w, x1, py, gray)
            tcx = min(x0 + 1, w - 1)
            tcy = min(y0 + 1, h - 1)
            ccx = min(x1 - 1, w - 1)
            ccy = min(y1 - 1, h - 1)
            self._plot(frame, h, w, tcx, tcy, _PHASE_PALETTE[target_ph % 4])
            self._plot(frame, h, w, ccx, ccy, _PHASE_PALETTE[cur_ph % 4])

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


def _palette_sprite(phase: int) -> Sprite:
    colors = list(_PHASE_PALETTE)
    c = colors[phase % 4]
    return Sprite(
        pixels=[[c]],
        name=f"ph_{phase}",
        visible=True,
        collidable=False,
        tags=["phase_cell"],
    )


def mk(
    walls: list[tuple[int, int]],
    target: list[list[int]],
    max_blur: int,
    diff: int,
) -> Level:
    sl: list[Sprite] = []
    for wx, wy in walls:
        sl.append(sprites["wall"].clone().set_position(wx, wy))
    return Level(
        sprites=sl,
        grid_size=(CAM_W, CAM_H),
        data={
            "difficulty": diff,
            "target": target,
            "max_blur": max_blur,
        },
    )


levels = [
    mk([], [[10, 12, 0], [11, 12, 2]], 30, 1),
    mk([(12, y) for y in range(24) if y != 12], [[8, 12, 1], [16, 12, 3]], 40, 2),
    mk([], [[6, 6, 2], [18, 18, 2], [18, 6, 0]], 50, 3),
    mk([(x, 10) for x in range(6, 18)], [[9, 12, 0], [15, 12, 0]], 45, 4),
    mk([], [[5 + i, 12, (i % 4)] for i in range(6)], 60, 5),
]


class Ph01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Ph01UI(CAM_W, CAM_H)
        super().__init__(
            "ph01",
            levels,
            Camera(0, 0, CAM_W, CAM_H, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 5, 6],
        )

    def on_set_level(self, level: Level) -> None:
        gw, gh = self.current_level.grid_size
        self._g = [[0 for _ in range(gh)] for _ in range(gw)]
        raw = self.current_level.get_data("target") or []
        self._target: dict[tuple[int, int], int] = {}
        for row in raw:
            x, y, v = int(row[0]), int(row[1]), int(row[2])
            self._target[(x, y)] = v
        self._blur_left = int(self.current_level.get_data("max_blur") or 40)
        self._sync_ui()
        self._refresh_phase_sprites()

    def _wall_at(self, x: int, y: int) -> bool:
        sp = self.current_level.get_sprite_at(x, y, ignore_collidable=True)
        return sp is not None and "wall" in sp.tags

    def _clear_phase_sprites(self) -> None:
        for s in list(self.current_level.get_sprites_by_tag("phase_cell")):
            self.current_level.remove_sprite(s)

    def _refresh_phase_sprites(self) -> None:
        self._clear_phase_sprites()
        gw, gh = self.current_level.grid_size
        for y in range(gh):
            for x in range(gw):
                if self._wall_at(x, y):
                    continue
                self.current_level.add_sprite(
                    _palette_sprite(self._g[x][y]).clone().set_position(x, y),
                )

    def _sync_ui(self) -> None:
        marks = sorted(
            (x, y, self._target[(x, y)], self._g[x][y]) for (x, y) in self._target
        )
        self._ui.update(self._blur_left, marks)

    def _win(self) -> bool:
        for (x, y), v in self._target.items():
            if self._g[x][y] != v:
                return False
        return True

    def step(self) -> None:
        aid = self.action.id

        if aid in (
            GameAction.ACTION1,
            GameAction.ACTION2,
            GameAction.ACTION3,
            GameAction.ACTION4,
        ):
            self._ui.update(self._blur_left, idle_flash=True)
            self.complete_action()
            return

        if aid == GameAction.ACTION5:
            if self._blur_left <= 0:
                self.lose()
                self.complete_action()
                return
            self._blur_left -= 1
            gw, gh = self.current_level.grid_size
            new_g = [[0 for _ in range(gh)] for _ in range(gw)]
            for y in range(gh):
                for x in range(gw):
                    if self._wall_at(x, y):
                        new_g[x][y] = self._g[x][y]
                        continue
                    s = self._g[x][y]
                    for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < gw and 0 <= ny < gh:
                            s += self._g[nx][ny]
                    new_g[x][y] = s % 4
            self._g = new_g
            self._refresh_phase_sprites()
            self._sync_ui()
            if self._win():
                self.next_level()
            self.complete_action()
            return

        if aid != GameAction.ACTION6:
            self.complete_action()
            return

        px = self.action.data.get("x", 0)
        py = self.action.data.get("y", 0)
        coords = self.camera.display_to_grid(px, py)
        if coords is None:
            self.complete_action()
            return
        gx, gy = coords
        gw, gh = self.current_level.grid_size
        if not (0 <= gx < gw and 0 <= gy < gh):
            self.complete_action()
            return
        if self._wall_at(gx, gy):
            self.complete_action()
            return

        self._g[gx][gy] = (self._g[gx][gy] + 1) % 4
        self._refresh_phase_sprites()
        self._sync_ui()
        if self._win():
            self.next_level()
        self.complete_action()
