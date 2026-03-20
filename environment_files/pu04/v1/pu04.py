"""pu04: pipe cells cycle H / V / T (tee); connect source to sink."""

from __future__ import annotations

from collections import deque

from arcengine import ARCBaseGame, Camera, GameAction, Level, RenderableUserDisplay, Sprite

BG, PAD = 5, 4
CAM = 16
H_P = (0, 1, 0, 1)
V_P = (1, 0, 1, 0)
T_P = (1, 1, 1, 0)
OPP = (2, 3, 0, 1)
DX = (0, 1, 0, -1)
DY = (-1, 0, 1, 0)


class Pu04UI(RenderableUserDisplay):
    def __init__(self, ok: bool) -> None:
        self._ok = ok

    def update(self, ok: bool) -> None:
        self._ok = ok

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        frame[h - 2, 2] = 14 if self._ok else 8
        return frame


SP = {
    "wall": Sprite(
        pixels=[[3]], name="w", visible=True, collidable=True, tags=["wall"]
    ),
    "source": Sprite(
        pixels=[[10]], name="s", visible=True, collidable=False, tags=["source"]
    ),
    "sink": Sprite(
        pixels=[[11]], name="k", visible=True, collidable=False, tags=["sink"]
    ),
    "pipe": Sprite(
        pixels=[[12]], name="p", visible=True, collidable=False, tags=["pipe"]
    ),
}


def mk(walls, pipes, src, snk, d):
    sl = [SP["wall"].clone().set_position(wx, wy) for wx, wy in walls]
    for px, py, _ in pipes:
        sl.append(SP["pipe"].clone().set_position(px, py))
    sl.append(SP["source"].clone().set_position(*src))
    sl.append(SP["sink"].clone().set_position(*snk))
    return Level(
        sprites=sl,
        grid_size=(CAM, CAM),
        data={"difficulty": d, "pipes": [[x, y, o] for x, y, o in pipes]},
    )


def border():
    return (
        [(x, 0) for x in range(CAM)]
        + [(x, CAM - 1) for x in range(CAM)]
        + [(0, y) for y in range(CAM)]
        + [(CAM - 1, y) for y in range(CAM)]
    )


levels = [
    mk(
        border(),
        [(x, 8, 0) for x in range(2, 7)] + [(7, 8, 2)] + [(x, 8, 0) for x in range(8, 14)],
        (1, 8),
        (14, 8),
        1,
    ),
    mk(
        border(),
        [(8, y, 1 - (y % 3)) for y in range(2, 14)],
        (8, 1),
        (8, 14),
        2,
    ),
    mk(
        border(),
        [(x, 8, x % 3) for x in range(2, 14)],
        (1, 8),
        (14, 8),
        3,
    ),
    mk(
        border(),
        [(4, y, 1) for y in range(3, 13)] + [(11, y, 1) for y in range(3, 13)],
        (4, 2),
        (11, 13),
        4,
    ),
    mk(
        border(),
        [(x, 6, 0) for x in range(3, 13)] + [(6, y, 2) for y in range(7, 10)],
        (2, 6),
        (13, 9),
        5,
    ),
    mk(
        border(),
        [(x, 7, x % 3) for x in range(2, 14)],
        (1, 7),
        (14, 7),
        6,
    ),
    mk(
        border(),
        [(5, y, y % 3) for y in range(2, 14)] + [(10, y, (y + 1) % 3) for y in range(2, 14)],
        (5, 1),
        (10, 14),
        7,
    ),
]


class Pu04(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Pu04UI(False)
        super().__init__(
            "pu04",
            levels,
            Camera(0, 0, CAM, CAM, BG, PAD, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 6],
        )

    def on_set_level(self, level: Level) -> None:
        raw = level.get_data("pipes") or []
        self._pipe: dict[tuple[int, int], int] = {}
        for row in raw:
            x, y, o = int(row[0]), int(row[1]), int(row[2])
            self._pipe[(x, y)] = o % 3
        s = self.current_level.get_sprites_by_tag("source")[0]
        k = self.current_level.get_sprites_by_tag("sink")[0]
        self._src = (s.x, s.y)
        self._snk = (k.x, k.y)
        self._ui.update(self._ok())

    def _sh(self, x: int, y: int) -> tuple[int, int, int, int]:
        if (x, y) == self._src:
            return (0, 1, 0, 0)
        if (x, y) == self._snk:
            return (0, 0, 0, 1)
        o = self._pipe.get((x, y), 0)
        return (H_P, V_P, T_P)[o]

    def _ok(self) -> bool:
        q = deque([self._src])
        seen = {self._src}
        gw, gh = self.current_level.grid_size
        while q:
            x, y = q.popleft()
            if (x, y) == self._snk:
                return True
            sh = self._sh(x, y)
            for d in range(4):
                if not sh[d]:
                    continue
                nx, ny = x + DX[d], y + DY[d]
                if not (0 <= nx < gw and 0 <= ny < gh):
                    continue
                sp = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
                if sp and "wall" in sp.tags:
                    continue
                nh = self._sh(nx, ny)
                if not nh[OPP[d]]:
                    continue
                if (nx, ny) not in seen:
                    seen.add((nx, ny))
                    q.append((nx, ny))
        return False

    def step(self) -> None:
        if self.action.id.value in (1, 2, 3, 4):
            self.complete_action()
            return
        if self.action.id != GameAction.ACTION6:
            self.complete_action()
            return
        c = self.camera.display_to_grid(
            self.action.data.get("x", 0), self.action.data.get("y", 0)
        )
        if not c:
            self.complete_action()
            return
        gx, gy = int(c[0]), int(c[1])
        if (gx, gy) in self._pipe:
            self._pipe[(gx, gy)] = (self._pipe[(gx, gy)] + 1) % 3
            ok = self._ok()
            self._ui.update(ok)
            if ok:
                self.next_level()
        self.complete_action()
