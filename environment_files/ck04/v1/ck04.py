"""ck04: directed wires — each tile sends flow one way; **ACTION6** cycles dir; reach out_port."""

from __future__ import annotations

from collections import deque

from arcengine import ARCBaseGame, Camera, GameAction, Level, RenderableUserDisplay, Sprite

BG, PAD = 5, 4
G = 14
CAM = 16
DX = (0, 1, 0, -1)
DY = (-1, 0, 1, 0)
OPP = (2, 3, 0, 1)


class Ck04UI(RenderableUserDisplay):
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
INP = Sprite(pixels=[[10]], name="i", visible=True, collidable=False, tags=["in_port"])
OUT = Sprite(pixels=[[11]], name="o", visible=True, collidable=False, tags=["out_port"])
WR = Sprite(pixels=[[12]], name="r", visible=True, collidable=False, tags=["wire"])


def mk(walls, wires, inp, outp, d):
    sl = [W.clone().set_position(x, y) for x, y in walls]
    for x, y, dr in wires:
        sl.append(WR.clone().set_position(x, y))
    sl.append(INP.clone().set_position(*inp))
    sl.append(OUT.clone().set_position(*outp))
    ser = {f"{x},{y}": dr for x, y, dr in wires}
    return Level(
        sprites=sl,
        grid_size=(G, G),
        data={"difficulty": d, "wires": ser},
    )


def bd():
    return (
        [(x, 0) for x in range(G)]
        + [(x, G - 1) for x in range(G)]
        + [(0, y) for y in range(G)]
        + [(G - 1, y) for y in range(G)]
    )


levels = [
    mk(bd(), [(x, 7, 1) for x in range(2, 12)], (1, 7), (12, 7), 1),
    mk(bd(), [(3, y, 2) for y in range(2, 11)] + [(x, 10, 1) for x in range(3, 11)], (3, 2), (10, 10), 2),
    mk(bd(), [(x, 5, 1) for x in range(2, 8)] + [(8, y, 2) for y in range(5, 10)], (1, 5), (8, 10), 3),
    mk(bd(), [(5, y, 0) for y in range(2, 12)], (5, 11), (5, 2), 4),
    mk(bd(), [(x, 6, x % 4) for x in range(2, 12)], (1, 6), (12, 6), 5),
    mk(bd(), [(6, y, (y + 1) % 4) for y in range(2, 12)], (6, 1), (6, 12), 6),
    mk(
        bd(),
        [(x, 7, 1) for x in range(2, 6)]
        + [(6, 7, 2), (6, 8, 2)]
        + [(x, 8, 1) for x in range(7, 12)],
        (1, 7),
        (12, 8),
        7,
    ),
]


class Ck04(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Ck04UI(False)
        super().__init__(
            "ck04",
            levels,
            Camera(0, 0, CAM, CAM, BG, PAD, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 6],
        )

    def on_set_level(self, level: Level) -> None:
        self._w = {}
        for k, v in (level.get_data("wires") or {}).items():
            a, b = k.split(",")
            self._w[(int(a), int(b))] = int(v) % 4
        i = self.current_level.get_sprites_by_tag("in_port")[0]
        o = self.current_level.get_sprites_by_tag("out_port")[0]
        self._inp = (i.x, i.y)
        self._out = (o.x, o.y)
        self._ui.update(self._reach())

    def _nei(self, x: int, y: int) -> list[tuple[int, int]]:
        out: list[tuple[int, int]] = []
        if (x, y) in self._w:
            d = self._w[(x, y)]
            nx, ny = x + DX[d], y + DY[d]
            if 0 <= nx < G and 0 <= ny < G:
                sp = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
                if not sp or "wall" not in sp.tags:
                    out.append((nx, ny))
        for d in range(4):
            nx, ny = x + DX[d], y + DY[d]
            if not (0 <= nx < G and 0 <= ny < G):
                continue
            if (nx, ny) not in self._w:
                continue
            nd = self._w[(nx, ny)]
            if OPP[nd] == d:
                out.append((nx, ny))
        return out

    def _reach(self) -> bool:
        q = deque([self._inp])
        seen = {self._inp}
        while q:
            x, y = q.popleft()
            if (x, y) == self._out:
                return True
            for nb in self._nei(x, y):
                if nb not in seen:
                    seen.add(nb)
                    q.append(nb)
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
        if (gx, gy) in self._w:
            self._w[(gx, gy)] = (self._w[(gx, gy)] + 1) % 4
            ok = self._reach()
            self._ui.update(ok)
            if ok:
                self.next_level()
        self.complete_action()
