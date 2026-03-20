"""pj04: bolt from fixed shooter; mirrors like ml04; sink on receptor."""

from __future__ import annotations

from arcengine import ARCBaseGame, Camera, GameAction, Level, RenderableUserDisplay, Sprite

BG, PAD = 5, 4
G = 12
CAM = 16
DX = (1, 0, -1, 0)
DY = (0, 1, 0, -1)
REF_SLASH = {0: 3, 3: 0, 1: 2, 2: 1}
REF_BSL = {0: 1, 1: 0, 2: 3, 3: 2}


class Pj04UI(RenderableUserDisplay):
    def __init__(self, cd: int) -> None:
        self._cd = cd

    def update(self, cd: int) -> None:
        self._cd = cd

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        frame[h - 2, 2] = 8 if self._cd > 0 else 14
        return frame


W = Sprite(pixels=[[3]], name="w", visible=True, collidable=True, tags=["wall"])
SH = Sprite(pixels=[[9]], name="s", visible=True, collidable=False, tags=["shooter"])
SK = Sprite(pixels=[[11]], name="k", visible=True, collidable=False, tags=["sink"])
MV = Sprite(pixels=[[6]], name="m", visible=True, collidable=False, tags=["mirror"])
BT = Sprite(pixels=[[8]], name="b", visible=True, collidable=False, tags=["bolt"])


def mk(walls, mirrors, shooter, sink, d):
    sl = [W.clone().set_position(x, y) for x, y in walls]
    for x, y, _ in mirrors:
        sl.append(MV.clone().set_position(x, y))
    sl.append(SH.clone().set_position(*shooter))
    sl.append(SK.clone().set_position(*sink))
    return Level(
        sprites=sl,
        grid_size=(G, G),
        data={"mirrors": [[x, y, t] for x, y, t in mirrors], "difficulty": d},
    )


def bd():
    return (
        [(x, 0) for x in range(G)]
        + [(x, G - 1) for x in range(G)]
        + [(0, y) for y in range(G)]
        + [(G - 1, y) for y in range(G)]
    )


levels = [
    mk(bd(), [(4, 6, 0), (6, 6, 1)], (1, 6), (10, 6), 1),
    mk(bd(), [(x, 6, x % 3) for x in range(3, 9)], (1, 6), (10, 6), 2),
    mk(bd(), [(6, y, y % 3) for y in range(3, 9)], (6, 1), (6, 10), 3),
    mk(bd(), [(5, 5, 1), (7, 7, 2)], (2, 2), (9, 9), 4),
    mk(bd(), [(4, 5, 0), (5, 5, 1), (6, 5, 2)], (2, 5), (9, 5), 5),
    mk(bd(), [(x, x, 0) for x in range(3, 9)], (2, 3), (9, 8), 6),
    mk(bd(), [(5, 4, 1), (5, 7, 2)], (5, 2), (5, 10), 7),
]


class Pj04(ARCBaseGame):
    def __init__(self) -> None:
        self._bolt: Sprite | None = None
        self._cd = 0
        self._hud = Pj04UI(0)
        super().__init__(
            "pj04",
            levels,
            Camera(0, 0, CAM, CAM, BG, PAD, [self._hud]),
            False,
            1,
            [5, 6],
        )

    def on_set_level(self, level: Level) -> None:
        self._mir = {}
        for r in level.get_data("mirrors") or []:
            self._mir[(int(r[0]), int(r[1]))] = int(r[2]) % 3
        s = self.current_level.get_sprites_by_tag("shooter")[0]
        self._sx, self._sy = s.x, s.y
        self._dir = 0
        self._bx = self._by = -1
        self._cd = 0
        self._clear()
        self._hud.update(self._cd)

    def _clear(self) -> None:
        if self._bolt:
            self.current_level.remove_sprite(self._bolt)
            self._bolt = None

    def _spawn(self) -> None:
        self._clear()
        self._bx = self._sx + DX[self._dir]
        self._by = self._sy + DY[self._dir]
        if 0 <= self._bx < G and 0 <= self._by < G:
            self._bolt = BT.clone().set_position(self._bx, self._by)
            self.current_level.add_sprite(self._bolt)

    def _adv(self) -> bool:
        if self._bx < 0:
            return False
        x, y, d = self._bx, self._by, self._dir
        sp = self.current_level.get_sprite_at(x, y, ignore_collidable=True)
        if sp and "sink" in sp.tags:
            return True
        if sp and "wall" in sp.tags:
            self._clear()
            return False
        if (x, y) in self._mir:
            t = self._mir[(x, y)]
            if t == 1:
                d = REF_SLASH[d]
            elif t == 2:
                d = REF_BSL[d]
        self._dir = d
        nx, ny = x + DX[d], y + DY[d]
        if not (0 <= nx < G and 0 <= ny < G):
            self._clear()
            return False
        self._bx, self._by = nx, ny
        if self._bolt:
            self._bolt.set_position(nx, ny)
        sp2 = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
        return sp2 is not None and "sink" in sp2.tags

    def step(self) -> None:
        if self.action.id == GameAction.ACTION5:
            if self._cd > 0:
                self._cd -= 1
                self._hud.update(self._cd)
                self.complete_action()
                return
            if self._bx < 0:
                self._spawn()
            elif self._adv():
                self.next_level()
                self.complete_action()
                return
            else:
                self._cd = 2
            self._hud.update(self._cd)
            self.complete_action()
            return
        if self.action.id == GameAction.ACTION6:
            c = self.camera.display_to_grid(
                self.action.data.get("x", 0), self.action.data.get("y", 0)
            )
            if c:
                gx, gy = int(c[0]), int(c[1])
                if (gx, gy) in self._mir:
                    self._mir[(gx, gy)] = (self._mir[(gx, gy)] + 1) % 3
            self.complete_action()
            return
        self.complete_action()
