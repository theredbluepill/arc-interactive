"""cu01: cover **yellow** cells with **dominoes** (2 orth-adjacent clicks) or **L-trominoes** (3 clicks); **ACTION5** switches tool."""

from __future__ import annotations

from arcengine import ARCBaseGame, Camera, GameAction, Level, RenderableUserDisplay, Sprite

BG, PAD = 5, 4
G = 10
CAM = 16


class Cu01UI(RenderableUserDisplay):
    def render_interface(self, frame):
        return frame


def floor(x: int, y: int) -> Sprite:
    return (
        Sprite(
            pixels=[[1]],
            name="f",
            visible=True,
            collidable=False,
            tags=["floor"],
        )
        .clone()
        .set_position(x, y)
    )


def yel(x: int, y: int) -> Sprite:
    return (
        Sprite(
            pixels=[[11]],
            name="y",
            visible=True,
            collidable=False,
            tags=["yellow", "floor"],
        )
        .clone()
        .set_position(x, y)
    )


def mk(yellow: set[tuple[int, int]], d: int) -> Level:
    sl: list[Sprite] = []
    for y in range(G):
        for x in range(G):
            if (x, y) in yellow:
                sl.append(yel(x, y))
            else:
                sl.append(floor(x, y))
    return Level(
        sprites=sl,
        grid_size=(G, G),
        data={"yellow": [list(p) for p in yellow], "difficulty": d},
    )


levels = [
    mk({(2, 2), (3, 2), (2, 3), (3, 3)}, 1),
    mk({(1, 1), (2, 1), (1, 2), (2, 2), (4, 4), (5, 4)}, 2),
    mk({(x, 5) for x in range(2, 8)}, 3),
    mk({(2, y) for y in range(2, 6)} | {(3, y) for y in range(2, 6)}, 4),
    mk({(1, 1), (2, 1), (1, 2), (2, 2), (5, 5), (6, 5), (5, 6), (6, 6)}, 5),
    mk({(3, 3), (4, 3), (5, 3), (3, 4), (3, 5)}, 6),
    mk({(x, y) for x in range(4, 7) for y in range(4, 7)} - {(5, 5)}, 7),
]


def _is_l_shape(cells: list[tuple[int, int]]) -> bool:
    if len(set(cells)) != 3:
        return False
    xs = [c[0] for c in cells]
    ys = [c[1] for c in cells]
    if max(xs) - min(xs) > 1 or max(ys) - min(ys) > 1:
        return False
    if len(set(xs)) == 1 or len(set(ys)) == 1:
        return False
    return True


class Cu01(ARCBaseGame):
    def __init__(self) -> None:
        super().__init__(
            "cu01",
            levels,
            Camera(0, 0, CAM, CAM, BG, PAD, [Cu01UI()]),
            False,
            1,
            [5, 6],
        )

    def on_set_level(self, level: Level) -> None:
        self._yellow = {tuple(int(t) for t in p) for p in level.get_data("yellow")}
        self._covered: set[tuple[int, int]] = set()
        self._mode = 0
        self._picks: list[tuple[int, int]] = []

    def _paint_covered(self, gx: int, gy: int) -> None:
        sp = self.current_level.get_sprite_at(gx, gy, ignore_collidable=True)
        if sp and "yellow" in sp.tags:
            sp.pixels = [[14]]

    def step(self) -> None:
        if self.action.id == GameAction.ACTION5:
            self._mode = 1 - self._mode
            self._picks = []
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
        if (gx, gy) not in self._yellow or (gx, gy) in self._covered:
            self._picks = []
            self.complete_action()
            return
        self._picks.append((gx, gy))
        if self._mode == 0:
            if len(self._picks) == 2:
                a, b = self._picks
                if abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1:
                    self._covered.add(a)
                    self._covered.add(b)
                    self._paint_covered(*a)
                    self._paint_covered(*b)
                self._picks = []
        else:
            if len(self._picks) == 3:
                pts = self._picks
                if _is_l_shape(pts):
                    for p in pts:
                        self._covered.add(p)
                        self._paint_covered(*p)
                self._picks = []
        if self._covered >= self._yellow:
            self.next_level()
        self.complete_action()
