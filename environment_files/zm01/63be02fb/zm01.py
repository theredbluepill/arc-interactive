"""Flood duel: magenta vs yellow territory. ACTION5 switches active color; ACTION6 claims a floor cell orthogonally adjacent to your active region (not wall). Win when the larger region covers need_pct of floor (per level data)."""

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
GW = GH = 16
CAM = 16
WALL_C = 3
MAG_C = 6
YLW_C = 11


class Zm01UI(RenderableUserDisplay):
    def __init__(self, active: int, best_pct: int, need_pct: int) -> None:
        self._active = active
        self._best_pct = best_pct
        self._need_pct = need_pct

    def update(self, active: int, best_pct: int, need_pct: int) -> None:
        self._active = active
        self._best_pct = best_pct
        self._need_pct = need_pct

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        frame[h - 2, 2] = MAG_C if self._active == 0 else YLW_C
        # Dominant region as % of floor (matches win: max(mag,yel)*100//floor >= need_pct).
        filled = min(20, self._best_pct * 20 // 100)
        goal_i = min(19, max(0, (self._need_pct * 20 + 50) // 100 - 1))
        for i in range(20):
            x = 1 + i
            if x >= w:
                break
            if i < filled:
                frame[h - 1, x] = 14
            elif i == goal_i:
                frame[h - 1, x] = 11
            else:
                frame[h - 1, x] = 3
        return frame


sprites = {
    "wall": Sprite(
        pixels=[[WALL_C]],
        name="wall",
        visible=True,
        collidable=True,
        tags=["wall"],
    ),
    "m": Sprite(
        pixels=[[MAG_C]],
        name="m",
        visible=True,
        collidable=False,
        tags=["zone", "magenta"],
    ),
    "y": Sprite(
        pixels=[[YLW_C]],
        name="y",
        visible=True,
        collidable=False,
        tags=["zone", "yellow"],
    ),
}


def mk(
    walls: list[tuple[int, int]],
    m0: tuple[int, int],
    y0: tuple[int, int],
    need_pct: int,
    diff: int,
) -> Level:
    sl = [
        sprites["m"].clone().set_position(*m0),
        sprites["y"].clone().set_position(*y0),
    ]
    for wx, wy in walls:
        sl.append(sprites["wall"].clone().set_position(wx, wy))
    return Level(
        sprites=sl,
        grid_size=(GW, GH),
        data={"difficulty": diff, "need_pct": need_pct},
    )


levels = [
    mk([], (2, 8), (13, 8), 55, 1),
    mk([(8, y) for y in range(16) if y != 8], (1, 1), (14, 14), 60, 2),
    mk([(x, 8) for x in range(16) if x != 8], (4, 4), (12, 12), 58, 3),
    mk([], (0, 0), (15, 15), 65, 4),
    mk([(x, x) for x in range(16) if x % 3 == 0], (1, 14), (14, 1), 62, 5),
]


class Zm01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Zm01UI(0, 0, 60)
        super().__init__(
            "zm01",
            levels,
            Camera(0, 0, CAM, CAM, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [5, 6],
        )

    def on_set_level(self, level: Level) -> None:
        self._active = 0
        self._need = int(self.current_level.get_data("need_pct") or 60)
        self._sync_ui()

    def _zones(self, tag: str) -> set[tuple[int, int]]:
        return {
            (s.x, s.y)
            for s in self.current_level.get_sprites_by_tag("zone")
            if tag in s.tags
        }

    def _floor(self) -> int:
        gw, gh = self.current_level.grid_size
        w = 0
        for y in range(gh):
            for x in range(gw):
                sp = self.current_level.get_sprite_at(x, y, ignore_collidable=True)
                if sp and "wall" in sp.tags:
                    w += 1
        return max(1, gw * gh - w)

    def _best_floor_pct(self) -> int:
        fl = self._floor()
        mag = len(self._zones("magenta"))
        yel = len(self._zones("yellow"))
        return max(mag, yel) * 100 // fl if fl else 0

    def _sync_ui(self) -> None:
        self._ui.update(self._active, self._best_floor_pct(), self._need)

    def step(self) -> None:
        aid = self.action.id

        if aid == GameAction.ACTION5:
            self._active = 1 - self._active
            self._sync_ui()
            self.complete_action()
            return

        if aid != GameAction.ACTION6:
            self.complete_action()
            return

        px = self.action.data.get("x", 0)
        py = self.action.data.get("y", 0)
        coords = self.camera.display_to_grid(px, py)
        if not coords:
            self.complete_action()
            return
        gx, gy = coords
        gw, gh = self.current_level.grid_size
        if not (0 <= gx < gw and 0 <= gy < gh):
            self.complete_action()
            return
        sp0 = self.current_level.get_sprite_at(gx, gy, ignore_collidable=True)
        if sp0 and "wall" in sp0.tags:
            self.complete_action()
            return
        if sp0 and "zone" in sp0.tags:
            self.complete_action()
            return

        tag = "magenta" if self._active == 0 else "yellow"
        reg = self._zones(tag)
        ok = any((gx + dx, gy + dy) in reg for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)))
        if not ok:
            self.complete_action()
            return

        spr = sprites["m"].clone() if self._active == 0 else sprites["y"].clone()
        self.current_level.add_sprite(spr.set_position(gx, gy))

        best = self._best_floor_pct()
        self._sync_ui()
        if best >= self._need:
            self.next_level()

        self.complete_action()
