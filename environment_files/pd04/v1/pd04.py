"""pd04: duct cells toggle full cross (+) open vs closed; connect source to sink."""

from __future__ import annotations

from collections import deque

from arcengine import ARCBaseGame, Camera, GameAction, Level, RenderableUserDisplay, Sprite

BG, PAD = 5, 4
G = 12
CAM = 16
PLUS = (1, 1, 1, 1)
ZERO = (0, 0, 0, 0)
OPP = (2, 3, 0, 1)
DX = (0, 1, 0, -1)
DY = (-1, 0, 1, 0)


class Pd04UI(RenderableUserDisplay):
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


W = Sprite(pixels=[[3]], name="w", visible=True, collidable=True, tags=["wall"])
SRC = Sprite(pixels=[[10]], name="s", visible=True, collidable=False, tags=["source"])
SNK = Sprite(pixels=[[11]], name="k", visible=True, collidable=False, tags=["sink"])
PIP = Sprite(pixels=[[12]], name="p", visible=True, collidable=False, tags=["duct"])


def mk(walls, ducts, s, k, d):
    sl = [W.clone().set_position(x, y) for x, y in walls]
    for x, y, on in ducts:
        sl.append(PIP.clone().set_position(x, y))
    sl.append(SRC.clone().set_position(*s))
    sl.append(SNK.clone().set_position(*k))
    return Level(
        sprites=sl,
        grid_size=(G, G),
        data={"difficulty": d, "ducts": [[x, y, o] for x, y, o in ducts]},
    )


def bdr():
    return (
        [(x, 0) for x in range(G)]
        + [(x, G - 1) for x in range(G)]
        + [(0, y) for y in range(G)]
        + [(G - 1, y) for y in range(G)]
    )


levels = [
    mk(bdr(), [(x, 6, 1) for x in range(2, 10)], (1, 6), (10, 6), 1),
    mk(bdr(), [(5, y, y % 2) for y in range(2, 10)], (5, 1), (5, 10), 2),
    mk(bdr(), [(x, 5, 1) for x in range(2, 6)] + [(x, 5, 0) for x in range(6, 10)], (1, 5), (10, 5), 3),
    mk(bdr(), [(3, 4, 1), (4, 4, 1), (5, 4, 1), (6, 4, 1)], (2, 4), (9, 4), 4),
    mk(bdr(), [(x, 7, 1) for x in range(2, 10)], (1, 7), (10, 7), 5),
    mk(bdr(), [(4, y, 1) for y in range(2, 10)] + [(7, y, 1) for y in range(2, 10)], (4, 1), (7, 10), 6),
    mk(bdr(), [(x, 6, x % 2) for x in range(2, 10)], (1, 6), (10, 6), 7),
]


class Pd04(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Pd04UI(False)
        super().__init__(
            "pd04",
            levels,
            Camera(0, 0, CAM, CAM, BG, PAD, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 6],
        )

    def on_set_level(self, level: Level) -> None:
        self._duct = {}
        for r in level.get_data("ducts") or []:
            self._duct[(int(r[0]), int(r[1]))] = bool(int(r[2]))
        s = self.current_level.get_sprites_by_tag("source")[0]
        k = self.current_level.get_sprites_by_tag("sink")[0]
        self._src = (s.x, s.y)
        self._snk = (k.x, k.y)
        self._ui.update(self._flow())

    def _sh(self, x, y):
        if (x, y) == self._src:
            return (0, 1, 0, 0)
        if (x, y) == self._snk:
            return (0, 0, 0, 1)
        if (x, y) in self._duct:
            return PLUS if self._duct[(x, y)] else ZERO
        return ZERO

    def _flow(self) -> bool:
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
        if (gx, gy) in self._duct:
            self._duct[(gx, gy)] = not self._duct[(gx, gy)]
            ok = self._flow()
            self._ui.update(ok)
            if ok:
                self.next_level()
        self.complete_action()
