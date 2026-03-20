"""cx01: toggle **gate** cells until **S** and **T** are disconnected (no 4-neighbor path)."""

from __future__ import annotations

from collections import deque

from arcengine import ARCBaseGame, Camera, GameAction, Level, RenderableUserDisplay, Sprite

BG, PAD = 5, 4
G = 10
CAM = 16
OPEN, SHUT = 12, 3


class Cx01UI(RenderableUserDisplay):
    def render_interface(self, frame):
        return frame


def cell_sprite(x: int, y: int, c: int, tags: list[str]) -> Sprite:
    return (
        Sprite(
            pixels=[[c]],
            name="c",
            visible=True,
            collidable=False,
            tags=tags,
        )
        .clone()
        .set_position(x, y)
    )


def mk(s: tuple[int, int], t: tuple[int, int], walls: set[tuple[int, int]], gates: list[tuple[int, int]], d: int) -> Level:
    sl: list[Sprite] = []
    for y in range(G):
        for x in range(G):
            if (x, y) == s:
                sl.append(cell_sprite(x, y, 9, ["s", "mark"]))
            elif (x, y) == t:
                sl.append(cell_sprite(x, y, 11, ["t", "mark"]))
            elif (x, y) in walls:
                sl.append(cell_sprite(x, y, 5, ["wall", "mark"]))
            elif (x, y) in gates:
                sl.append(cell_sprite(x, y, OPEN, ["gate", "mark"]))
            else:
                sl.append(cell_sprite(x, y, 1, ["floor", "mark"]))
    return Level(
        sprites=sl,
        grid_size=(G, G),
        data={
            "s": list(s),
            "t": list(t),
            "walls": [list(p) for p in walls],
            "gates": [list(p) for p in gates],
            "difficulty": d,
        },
    )


def col_cut(gx: int, ys_open: list[int]) -> tuple[set[tuple[int, int]], list[tuple[int, int]]]:
    walls = {(gx, y) for y in range(G) if y not in ys_open}
    gates = [(gx, y) for y in ys_open]
    return walls, gates


levels = [
    mk((0, 4), (9, 4), *col_cut(5, [4]), 1),
    mk((0, 4), (9, 4), *col_cut(5, [3, 4]), 2),
    mk((0, 0), (9, 9), *col_cut(5, [2, 7]), 3),
    mk((2, 5), (8, 5), *col_cut(5, [4, 5]), 4),
    mk((1, 1), (8, 8), *col_cut(3, [4]), 5),
    mk((0, 6), (9, 6), *col_cut(6, [5, 6]), 6),
    mk((0, 5), (9, 5), *col_cut(5, [3, 4, 5]), 7),
]


class Cx01(ARCBaseGame):
    def __init__(self) -> None:
        super().__init__(
            "cx01",
            levels,
            Camera(0, 0, CAM, CAM, BG, PAD, [Cx01UI()]),
            False,
            1,
            [6],
        )

    def on_set_level(self, level: Level) -> None:
        d = level.get_data
        self._s = tuple(int(x) for x in d("s"))
        self._t = tuple(int(x) for x in d("t"))
        self._walls = {tuple(int(t) for t in p) for p in d("walls")}
        self._gate_set = {tuple(int(t) for t in p) for p in d("gates")}
        self._open = {tuple(int(t) for t in p) for p in d("gates")}

    def _passable(self, x: int, y: int) -> bool:
        if not (0 <= x < G and 0 <= y < G):
            return False
        if (x, y) in self._walls:
            return False
        if (x, y) == self._s or (x, y) == self._t:
            return True
        if (x, y) in self._gate_set:
            return (x, y) in self._open
        return True

    def _connected(self) -> bool:
        if self._s == self._t:
            return True
        q = deque([self._s])
        seen = {self._s}
        while q:
            x, y = q.popleft()
            if (x, y) == self._t:
                return True
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                nx, ny = x + dx, y + dy
                if (nx, ny) in seen:
                    continue
                if self._passable(nx, ny):
                    seen.add((nx, ny))
                    q.append((nx, ny))
        return False

    def step(self) -> None:
        if self.action.id != GameAction.ACTION6:
            self.complete_action()
            return
        c = self.camera.display_to_grid(
            self.action.data.get("x", 0), self.action.data.get("y", 0)
        )
        if c:
            gx, gy = int(c[0]), int(c[1])
            if (gx, gy) in self._gate_set:
                if (gx, gy) in self._open:
                    self._open.discard((gx, gy))
                else:
                    self._open.add((gx, gy))
                sp = self.current_level.get_sprite_at(gx, gy, ignore_collidable=True)
                if sp and "gate" in sp.tags:
                    sp.pixels = [[OPEN if (gx, gy) in self._open else SHUT]]
        if not self._connected():
            self.next_level()
        self.complete_action()
