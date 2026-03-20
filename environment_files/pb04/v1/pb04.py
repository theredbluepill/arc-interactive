"""pb04: winch cell — ACTION5 pulls nearest crate one step along (dx,dy) toward winch."""

from __future__ import annotations

from arcengine import ARCBaseGame, Camera, GameAction, Level, RenderableUserDisplay, Sprite

BG, PAD = 5, 4
G = 10
CAM = 16

WCH = Sprite(pixels=[[10]], name="w", visible=True, collidable=False, tags=["winch"])
C = Sprite(pixels=[[11]], name="c", visible=True, collidable=True, tags=["crate"])
K = Sprite(pixels=[[14]], name="k", visible=True, collidable=False, tags=["pad"])


class Pb04UI(RenderableUserDisplay):
    def render_interface(self, frame):
        return frame


def mk(wx, wy, dx, dy, crates, pads, d):
    sl = [WCH.clone().set_position(wx, wy)]
    for x, y in crates:
        sl.append(C.clone().set_position(x, y))
    for x, y in pads:
        sl.append(K.clone().set_position(x, y))
    return Level(
        sprites=sl,
        grid_size=(G, G),
        data={"winch": [wx, wy], "dir": [dx, dy], "difficulty": d},
    )


levels = [
    mk(2, 5, 1, 0, [(5, 5)], [(7, 5)], 1),
    mk(1, 4, 0, 1, [(4, 6)], [(4, 2)], 2),
    mk(8, 5, -1, 0, [(5, 5)], [(2, 5)], 3),
    mk(3, 3, 1, 1, [(5, 5)], [(7, 7)], 4),
    mk(2, 8, 0, -1, [(2, 5)], [(2, 2)], 5),
    mk(6, 6, -1, 0, [(8, 6)], [(4, 6)], 6),
    mk(5, 5, 1, 0, [(7, 5)], [(9, 5)], 7),
]


class Pb04(ARCBaseGame):
    def __init__(self) -> None:
        super().__init__(
            "pb04",
            levels,
            Camera(0, 0, CAM, CAM, BG, PAD, [Pb04UI()]),
            False,
            1,
            [5],
        )

    def on_set_level(self, level: Level) -> None:
        w = level.get_data("winch")
        self._wx, self._wy = int(w[0]), int(w[1])
        dr = level.get_data("dir")
        self._dx, self._dy = int(dr[0]), int(dr[1])

    def step(self) -> None:
        if self.action.id != GameAction.ACTION5:
            self.complete_action()
            return
        crates = self.current_level.get_sprites_by_tag("crate")
        if not crates:
            self.complete_action()
            return
        cr = min(
            crates,
            key=lambda s: abs(s.x - self._wx) + abs(s.y - self._wy),
        )
        nx = cr.x - self._dx
        ny = cr.y - self._dy
        if 0 <= nx < G and 0 <= ny < G:
            sp = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
            if not sp or "crate" not in sp.tags:
                cr.set_position(nx, ny)
        pads = {(s.x, s.y) for s in self.current_level.get_sprites_by_tag("pad")}
        cpos = {(s.x, s.y) for s in self.current_level.get_sprites_by_tag("crate")}
        if pads and pads <= cpos:
            self.next_level()
        self.complete_action()
