"""rp04: toggle relays with ACTION6; ACTION5 pulses from source through ON relays; light all lamps."""

from __future__ import annotations

from collections import deque

from arcengine import ARCBaseGame, Camera, GameAction, Level, RenderableUserDisplay, Sprite

BG, PAD = 5, 4
G = 12
CAM = 16


class Rp04UI(RenderableUserDisplay):
    def __init__(self, lit: int, need: int, tok: int) -> None:
        self._l, self._n, self._t = lit, need, tok

    def update(self, lit: int, need: int, tok: int) -> None:
        self._l, self._n, self._t = lit, need, tok

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for i in range(min(self._n, 10)):
            frame[h - 2, 1 + i] = 14 if i < self._l else 8
        frame[h - 2, 20] = 11 if self._t > 0 else 8
        return frame


SRC = Sprite(pixels=[[10]], name="s", visible=True, collidable=False, tags=["source"])
REL = Sprite(pixels=[[12]], name="r", visible=True, collidable=False, tags=["relay"])
LMP = Sprite(pixels=[[11]], name="l", visible=True, collidable=False, tags=["lamp"])
W = Sprite(pixels=[[3]], name="w", visible=True, collidable=True, tags=["wall"])


def mk(walls, relays, lamps, src, max_pulses, d):
    sl = [W.clone().set_position(x, y) for x, y in walls]
    for x, y in relays:
        sl.append(REL.clone().set_position(x, y))
    for x, y in lamps:
        sl.append(LMP.clone().set_position(x, y))
    sl.append(SRC.clone().set_position(*src))
    return Level(
        sprites=sl,
        grid_size=(G, G),
        data={
            "relays": [list(p) for p in relays],
            "lamps": [list(p) for p in lamps],
            "max_pulses": max_pulses,
            "difficulty": d,
        },
    )


def bd():
    return (
        [(x, 0) for x in range(G)]
        + [(x, G - 1) for x in range(G)]
        + [(0, y) for y in range(G)]
        + [(G - 1, y) for y in range(G)]
    )


levels = [
    mk(bd(), [(4, 5), (5, 5), (6, 5)], [(7, 5)], (3, 5), 12, 1),
    mk(bd(), [(5, y) for y in range(3, 9)], [(5, 9)], (5, 2), 15, 2),
    mk(bd(), [(x, 6) for x in range(3, 9)], [(9, 6)], (2, 6), 14, 3),
    mk(bd(), [(4, 4), (5, 4), (5, 5), (6, 5)], [(6, 6)], (4, 3), 18, 4),
    mk(bd(), [(3, 5), (4, 5), (6, 5), (7, 5)], [(8, 5)], (2, 5), 16, 5),
    mk(bd(), [(5, y) for y in range(4, 8)], [(5, 8)], (5, 3), 20, 6),
    mk(bd(), [(x, 7) for x in range(3, 9)], [(9, 7)], (2, 7), 22, 7),
]


class Rp04(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Rp04UI(0, 1, 0)
        super().__init__(
            "rp04",
            levels,
            Camera(0, 0, CAM, CAM, BG, PAD, [self._ui]),
            False,
            1,
            [5, 6],
        )

    def on_set_level(self, level: Level) -> None:
        self._relay_all = {tuple(int(t) for t in p) for p in level.get_data("relays")}
        self._relay_on = set(self._relay_all)
        self._lamps = {tuple(int(t) for t in p) for p in level.get_data("lamps")}
        self._left = int(level.get_data("max_pulses") or 15)
        s = self.current_level.get_sprites_by_tag("source")[0]
        self._src = (s.x, s.y)
        self._lit = set()
        self._sync()

    def _sync(self) -> None:
        n = len(self._lit & self._lamps)
        self._ui.update(n, len(self._lamps), self._left)

    def _pass(self, x: int, y: int) -> bool:
        if (x, y) == self._src:
            return True
        if (x, y) in self._lamps:
            return True
        if (x, y) in self._relay_on:
            return True
        return False

    def _pulse(self) -> None:
        q = deque([self._src])
        seen = {self._src}
        while q:
            x, y = q.popleft()
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                nx, ny = x + dx, y + dy
                if not (0 <= nx < G and 0 <= ny < G):
                    continue
                sp = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
                if sp and "wall" in sp.tags:
                    continue
                if not self._pass(nx, ny):
                    continue
                if (nx, ny) not in seen:
                    seen.add((nx, ny))
                    q.append((nx, ny))
        self._lit |= seen

    def step(self) -> None:
        if self.action.id == GameAction.ACTION5:
            if self._left <= 0:
                self.lose()
                self.complete_action()
                return
            self._left -= 1
            self._pulse()
            self._sync()
            if self._lamps <= self._lit:
                self.next_level()
            elif self._left <= 0:
                self.lose()
            self.complete_action()
            return
        if self.action.id == GameAction.ACTION6:
            c = self.camera.display_to_grid(
                self.action.data.get("x", 0), self.action.data.get("y", 0)
            )
            if c:
                gx, gy = int(c[0]), int(c[1])
                p = (gx, gy)
                if p in self._relay_all:
                    if p in self._relay_on:
                        self._relay_on.discard(p)
                    else:
                        self._relay_on.add(p)
            self._sync()
            self.complete_action()
            return
        self.complete_action()
