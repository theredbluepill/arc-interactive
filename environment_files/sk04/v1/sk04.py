"""sk04: fixed player — ACTION6 on orth-adjacent crate pulls it one step toward player."""

from __future__ import annotations

from arcengine import ARCBaseGame, Camera, GameAction, Level, RenderableUserDisplay, Sprite

BG, PAD = 5, 4
G = 10
CAM = 16

P = Sprite(pixels=[[9]], name="p", visible=True, collidable=True, tags=["player"])
C = Sprite(pixels=[[11]], name="c", visible=True, collidable=True, tags=["crate"])
K = Sprite(pixels=[[14]], name="k", visible=True, collidable=False, tags=["pad"])


class Sk04UI(RenderableUserDisplay):
    def render_interface(self, frame):
        return frame


def mk(px, py, crates, pads, d):
    sl = [P.clone().set_position(px, py)]
    for x, y in crates:
        sl.append(C.clone().set_position(x, y))
    for x, y in pads:
        sl.append(K.clone().set_position(x, y))
    return Level(
        sprites=sl,
        grid_size=(G, G),
        data={"difficulty": d},
    )


def bd():
    return (
        [(x, 0) for x in range(G)]
        + [(x, G - 1) for x in range(G)]
        + [(0, y) for y in range(G)]
        + [(G - 1, y) for y in range(G)]
    )


levels = [
    mk(2, 5, [(4, 5)], [(7, 5)], 1),
    mk(1, 4, [(3, 4), (5, 4)], [(8, 4)], 2),
    mk(2, 2, [(5, 2)], [(8, 8)], 3),
    mk(3, 6, [(6, 6)], [(8, 6)], 4),
    mk(1, 1, [(4, 4), (6, 6)], [(8, 8)], 5),
    mk(2, 7, [(5, 7)], [(7, 7)], 6),
    mk(4, 4, [(6, 4), (4, 6)], [(8, 4), (8, 6)], 7),
]


class Sk04(ARCBaseGame):
    def __init__(self) -> None:
        super().__init__(
            "sk04",
            levels,
            Camera(0, 0, CAM, CAM, BG, PAD, [Sk04UI()]),
            False,
            1,
            [6],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]

    def step(self) -> None:
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
        px, py = self._player.x, self._player.y
        if abs(gx - px) + abs(gy - py) != 1:
            self.complete_action()
            return
        cr = self.current_level.get_sprite_at(gx, gy, ignore_collidable=True)
        if not cr or "crate" not in cr.tags:
            self.complete_action()
            return
        dx = px - gx
        dy = py - gy
        nx, ny = gx + dx, gy + dy
        if 0 <= nx < G and 0 <= ny < G:
            sp = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
            if not sp or "crate" not in sp.tags:
                cr.set_position(nx, ny)
        pads = {(s.x, s.y) for s in self.current_level.get_sprites_by_tag("pad")}
        crates = {(s.x, s.y) for s in self.current_level.get_sprites_by_tag("crate")}
        if pads and pads <= crates:
            self.next_level()
        self.complete_action()
