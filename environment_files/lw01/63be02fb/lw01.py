"""Line weave: connect each colored start to its matching end with orthogonal paths; paths may not share cells across colors."""

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
CAM_W = CAM_H = 32
WALL_C = 3


class Lw01UI(RenderableUserDisplay):
    def __init__(self, active: int, n_colors: int, steps_left: int) -> None:
        self._active = active
        self._n = n_colors
        self._steps_left = steps_left

    def update(self, active: int, n_colors: int, steps_left: int) -> None:
        self._active = active
        self._n = n_colors
        self._steps_left = steps_left

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for i in range(min(self._n, 8)):
            c = 11 if i == self._active else 2
            frame[h - 2, 2 + i * 2] = c
        cap = 24
        rem = max(0, min(self._steps_left, cap))
        for t in range(cap):
            frame[h - 1, 1 + t] = 14 if t < rem else 3
        return frame


sprites = {
    "wall": Sprite(
        pixels=[[WALL_C]],
        name="wall",
        visible=True,
        collidable=True,
        tags=["wall"],
    ),
    "s0": Sprite(
        pixels=[[6]],
        name="s0",
        visible=True,
        collidable=False,
        tags=["marker"],
    ),
    "e0": Sprite(
        pixels=[[7]],
        name="e0",
        visible=True,
        collidable=False,
        tags=["marker"],
    ),
    "s1": Sprite(
        pixels=[[8]],
        name="s1",
        visible=True,
        collidable=False,
        tags=["marker"],
    ),
    "e1": Sprite(
        pixels=[[9]],
        name="e1",
        visible=True,
        collidable=False,
        tags=["marker"],
    ),
    "trail": Sprite(
        pixels=[[10]],
        name="trail",
        visible=True,
        collidable=False,
        tags=["trail"],
    ),
}


def _lvl_fix_pairs(pairs, grid, walls, diff, max_steps):
    sl: list[Sprite] = []
    for wx, wy in walls:
        sl.append(sprites["wall"].clone().set_position(wx, wy))
    markers = (sprites["s0"], sprites["e0"], sprites["s1"], sprites["e1"])
    for i, (a, b) in enumerate(pairs):
        sl.append(markers[i * 2].clone().set_position(a[0], a[1]))
        sl.append(markers[i * 2 + 1].clone().set_position(b[0], b[1]))
    ser = [[list(a), list(b)] for a, b in pairs]
    return Level(
        sprites=sl,
        grid_size=grid,
        data={"difficulty": diff, "pairs": ser, "max_steps": max_steps},
    )


levels = [
    _lvl_fix_pairs([((2, 12), (22, 12))], (24, 24), [], 1, 120),
    _lvl_fix_pairs(
        [((2, 6), (20, 6)), ((2, 18), (20, 18))],
        (24, 24),
        [(12, y) for y in range(4, 20) if y not in (6, 18)],
        2,
        200,
    ),
    _lvl_fix_pairs(
        [((1, 1), (30, 30)), ((30, 1), (1, 30))],
        (32, 32),
        [(16, y) for y in range(6, 26)],
        3,
        400,
    ),
    _lvl_fix_pairs(
        [((2, 2), (29, 29)), ((29, 2), (2, 29))],
        (32, 32),
        [(x, 16) for x in range(4, 28) if x % 4 != 0],
        4,
        450,
    ),
    _lvl_fix_pairs(
        [((5, 5), (26, 26)), ((26, 5), (5, 26))],
        (32, 32),
        [(15, y) for y in (6, 7, 24, 25)] + [(x, 15) for x in (6, 7, 24, 25)],
        5,
        500,
    ),
]


class Lw01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Lw01UI(0, 1, 0)
        super().__init__(
            "lw01",
            levels,
            Camera(0, 0, CAM_W, CAM_H, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 5, 6],
        )

    def _grid_to_frame_pixel(self, gx: int, gy: int) -> tuple[int, int]:
        cam = self.camera
        cw, ch = cam.width, cam.height
        scale = min(64 // cw, 64 // ch)
        x_pad = (64 - cw * scale) // 2
        y_pad = (64 - ch * scale) // 2
        return gx * scale + scale // 2 + x_pad, gy * scale + scale // 2 + y_pad

    def on_set_level(self, level: Level) -> None:
        raw = self.current_level.get_data("pairs") or []
        self._pairs: list[tuple[tuple[int, int], tuple[int, int]]] = []
        for item in raw:
            a, b = item
            self._pairs.append((tuple(a), tuple(b)))
        self._k = len(self._pairs)
        self._active = 0
        self._paths: list[list[tuple[int, int]]] = [[p[0]] for p in self._pairs]
        self._steps_left = int(self.current_level.get_data("max_steps") or 200)
        self._refresh_trail_sprites()
        self._sync_ui()

    def _wall_at(self, x: int, y: int) -> bool:
        sp = self.current_level.get_sprite_at(x, y, ignore_collidable=True)
        return sp is not None and "wall" in sp.tags

    def _occupied_by_other(self, x: int, y: int, skip: int) -> bool:
        for i, trail in enumerate(self._paths):
            if i == skip:
                continue
            if (x, y) in trail:
                return True
            st, en = self._pairs[i]
            if (x, y) in (st, en):
                return True
        return False

    def _clear_trails(self) -> None:
        for sp in list(self.current_level.get_sprites_by_tag("trail")):
            self.current_level.remove_sprite(sp)

    def _refresh_trail_sprites(self) -> None:
        self._clear_trails()
        for i, trail in enumerate(self._paths):
            for j, (x, y) in enumerate(trail):
                if j == 0:
                    continue
                if (x, y) == self._pairs[i][1]:
                    continue
                self.current_level.add_sprite(
                    sprites["trail"].clone().set_position(x, y),
                )

    def _sync_ui(self) -> None:
        self._ui.update(self._active, max(1, self._k), self._steps_left)

    def _win(self) -> bool:
        for i, (_, end) in enumerate(self._pairs):
            if not self._paths[i] or self._paths[i][-1] != end:
                return False
        return True

    def _burn_step(self) -> bool:
        self._steps_left -= 1
        self._sync_ui()
        if self._steps_left <= 0:
            self.lose()
            return True
        return False

    def step(self) -> None:
        aid = self.action.id

        if aid == GameAction.ACTION1:
            if self._k > 0:
                self._active = (self._active - 1) % self._k
            self._sync_ui()
            self.complete_action()
            return

        if aid == GameAction.ACTION2:
            if self._k > 0:
                self._active = (self._active + 1) % self._k
            self._sync_ui()
            self.complete_action()
            return

        if aid in (GameAction.ACTION3, GameAction.ACTION4):
            self.complete_action()
            return

        if aid == GameAction.ACTION5:
            tr = self._paths[self._active]
            if len(tr) > 1:
                tr.pop()
                self._refresh_trail_sprites()
            if self._burn_step():
                self.complete_action()
                return
            self.complete_action()
            return

        if aid != GameAction.ACTION6:
            self.complete_action()
            return

        x = self.action.data.get("x", 0)
        y = self.action.data.get("y", 0)
        coords = self.camera.display_to_grid(x, y)
        if coords is None:
            if self._burn_step():
                self.complete_action()
                return
            self.complete_action()
            return

        gx, gy = coords
        gw, gh = self.current_level.grid_size
        if not (0 <= gx < gw and 0 <= gy < gh):
            if self._burn_step():
                self.complete_action()
                return
            self.complete_action()
            return

        cur = self._paths[self._active][-1]
        if abs(gx - cur[0]) + abs(gy - cur[1]) != 1:
            if self._burn_step():
                self.complete_action()
                return
            self.complete_action()
            return

        if self._wall_at(gx, gy):
            if self._burn_step():
                self.complete_action()
                return
            self.complete_action()
            return

        if self._occupied_by_other(gx, gy, self._active):
            if self._burn_step():
                self.complete_action()
                return
            self.complete_action()
            return

        st, en = self._pairs[self._active]
        if (gx, gy) in self._paths[self._active] and (gx, gy) != st:
            if self._burn_step():
                self.complete_action()
                return
            self.complete_action()
            return

        self._paths[self._active].append((gx, gy))
        self._refresh_trail_sprites()
        if self._burn_step():
            self.complete_action()
            return

        if self._win():
            self.next_level()

        self.complete_action()
