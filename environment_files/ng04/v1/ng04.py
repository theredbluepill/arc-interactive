"""ng04: two-layer cell colors — ACTION6 cycles layer visible color; match both targets."""

from __future__ import annotations

from arcengine import ARCBaseGame, Camera, GameAction, Level, RenderableUserDisplay, Sprite

BG, PAD = 5, 4
G = 6
CAM = 16
COLS = (8, 9, 11, 14)


class Ng04UI(RenderableUserDisplay):
    def render_interface(self, frame):
        return frame


def cell(x: int, y: int, c: int) -> Sprite:
    return Sprite(
        pixels=[[c]], name="c", visible=True, collidable=False, tags=["cell"]
    ).clone().set_position(x, y)


def mk(fg: list[list[int]], bg: list[list[int]], targ_fg, targ_bg, d: int) -> Level:
    sl = []
    for y in range(G):
        for x in range(G):
            sl.append(cell(x, y, COLS[fg[y][x] % 4]))
    return Level(
        sprites=sl,
        grid_size=(G, G),
        data={
            "fg": fg,
            "bg": bg,
            "target_fg": targ_fg,
            "target_bg": targ_bg,
            "difficulty": d,
        },
    )


def z():
    return [[0 for _ in range(G)] for _ in range(G)]


levels = [
    mk(z(), z(), [[1, 0, 0, 0, 0, 0]] * G, z(), 1),
    mk([[1 if x == y else 0 for x in range(G)] for y in range(G)], z(), [[1 if x == y else 0 for x in range(G)] for y in range(G)], z(), 2),
    mk([[x % 4 for x in range(G)] for y in range(G)], z(), [[x % 4 for x in range(G)] for y in range(G)], z(), 3),
    mk(z(), [[1, 0, 0, 0, 0, 0]] * G, z(), [[1, 0, 0, 0, 0, 0]] * G, 4),
    mk([[0, 1, 2, 3, 0, 1]] * G, z(), [[0, 1, 2, 3, 0, 1]] * G, z(), 5),
    mk(z(), z(), z(), z(), 6),
    mk([[2] * G for _ in range(G)], [[3] * G for _ in range(G)], [[2] * G for _ in range(G)], [[3] * G for _ in range(G)], 7),
]


class Ng04(ARCBaseGame):
    def __init__(self) -> None:
        super().__init__(
            "ng04",
            levels,
            Camera(0, 0, CAM, CAM, BG, PAD, [Ng04UI()]),
            False,
            1,
            [1, 2, 3, 4, 6],
        )

    def on_set_level(self, level: Level) -> None:
        self._fg = [list(r) for r in level.get_data("fg")]
        self._bg = [list(r) for r in level.get_data("bg")]
        self._tfg = [list(r) for r in level.get_data("target_fg")]
        self._tbg = [list(r) for r in level.get_data("target_bg")]
        self._layer = 0
        self._ref()

    def _ref(self) -> None:
        for s in list(self.current_level.get_sprites_by_tag("cell")):
            self.current_level.remove_sprite(s)
        src = self._fg if self._layer == 0 else self._bg
        for y in range(G):
            for x in range(G):
                self.current_level.add_sprite(
                    cell(x, y, COLS[src[y][x] % 4])
                )

    def _win(self) -> bool:
        return self._fg == self._tfg and self._bg == self._tbg

    def step(self) -> None:
        if self.action.id == GameAction.ACTION6:
            c = self.camera.display_to_grid(
                self.action.data.get("x", 0), self.action.data.get("y", 0)
            )
            if c:
                gx, gy = int(c[0]), int(c[1])
                if 0 <= gx < G and 0 <= gy < G:
                    if self._layer == 0:
                        self._fg[gy][gx] = (self._fg[gy][gx] + 1) % 4
                    else:
                        self._bg[gy][gx] = (self._bg[gy][gx] + 1) % 4
                    self._ref()
                    if self._win():
                        self.next_level()
            else:
                self._layer = 1 - self._layer
                self._ref()
            self.complete_action()
            return
        self.complete_action()
