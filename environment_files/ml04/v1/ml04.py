"""**ml04** — stepped bolt, fixed mirror slots (10×10 grid).

**Vs ml01–ml03:** **ml04** is **16×16 camera** over a **10×10** playfield. **ACTION5** advances
the laser **one cell** per press (visible **bolt** sprite). **ACTION6** cycles each mirror
tile through **``/`` → ``\\`` → empty** — no inventory, no free placement. **ml01** is
global placement + continuous ray; **ml02**/**ml03** add a moving technician and adjacency
for mirror edits; **ml03** also **consumes** mirrors that reflected the beam.
"""

from __future__ import annotations

from arcengine import ARCBaseGame, Camera, GameAction, Level, RenderableUserDisplay, Sprite

BG, PAD = 5, 4
G = 10
CAM = 16
DX = (1, 0, -1, 0)
DY = (0, 1, 0, -1)
# dir 0=E,1=S,2=W,3=N — / mirror
REF_SLASH = {0: 3, 3: 0, 1: 2, 2: 1}
REF_BSL = {0: 1, 1: 0, 2: 3, 3: 2}


class Ml04UI(RenderableUserDisplay):
    def render_interface(self, frame):
        return frame


W = Sprite(pixels=[[3]], name="w", visible=True, collidable=True, tags=["wall"])
EM = Sprite(pixels=[[10]], name="e", visible=True, collidable=False, tags=["emitter"])
RC = Sprite(pixels=[[11]], name="r", visible=True, collidable=False, tags=["receptor"])
MV = Sprite(pixels=[[6]], name="m", visible=True, collidable=False, tags=["mirror"])
BT = Sprite(pixels=[[12]], name="b", visible=True, collidable=False, tags=["bolt"])


def mk(walls, mirrors, emitter, receptor, d):
    sl = [W.clone().set_position(x, y) for x, y in walls]
    for x, y, _ in mirrors:
        sl.append(MV.clone().set_position(x, y))
    sl.append(EM.clone().set_position(*emitter))
    sl.append(RC.clone().set_position(*receptor))
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
    mk(bd(), [(3, 5, 0), (5, 5, 1)], (1, 5), (8, 5), 1),
    mk(bd(), [(4, y, y % 3) for y in range(3, 8)], (1, 5), (8, 5), 2),
    mk(bd(), [(x, 5, x % 3) for x in range(2, 8)], (1, 5), (8, 5), 3),
    mk(bd(), [(5, 4, 1), (5, 6, 2)], (5, 2), (5, 8), 4),
    mk(bd(), [(3, 3, 0), (6, 6, 1)], (1, 1), (8, 8), 5),
    mk(bd(), [(x, x, x % 3) for x in range(2, 8)], (1, 2), (8, 7), 6),
    mk(bd(), [(4, 5, 0), (5, 5, 1), (6, 5, 2)], (2, 5), (8, 5), 7),
]


class Ml04(ARCBaseGame):
    def __init__(self) -> None:
        self._bolt: Sprite | None = None
        super().__init__(
            "ml04",
            levels,
            Camera(0, 0, CAM, CAM, BG, PAD, [Ml04UI()]),
            False,
            1,
            [5, 6],
        )

    def on_set_level(self, level: Level) -> None:
        self._mir: dict[tuple[int, int], int] = {}
        for r in level.get_data("mirrors") or []:
            self._mir[(int(r[0]), int(r[1]))] = int(r[2]) % 3
        e = self.current_level.get_sprites_by_tag("emitter")[0]
        self._ex, self._ey = e.x, e.y
        self._dir = 0
        self._bx = self._by = -1
        self._clear_bolt()

    def _clear_bolt(self) -> None:
        if self._bolt:
            self.current_level.remove_sprite(self._bolt)
            self._bolt = None

    def _emit(self) -> None:
        self._clear_bolt()
        self._bx = self._ex + DX[self._dir]
        self._by = self._ey + DY[self._dir]
        if 0 <= self._bx < G and 0 <= self._by < G:
            self._bolt = BT.clone().set_position(self._bx, self._by)
            self.current_level.add_sprite(self._bolt)

    def _step_ray(self) -> bool:
        if self._bx < 0:
            self._emit()
            return False
        x, y, d = self._bx, self._by, self._dir
        sp = self.current_level.get_sprite_at(x, y, ignore_collidable=True)
        if sp and "receptor" in sp.tags:
            return True
        if sp and "wall" in sp.tags:
            self._clear_bolt()
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
            self._clear_bolt()
            return False
        self._bx, self._by = nx, ny
        if self._bolt:
            self._bolt.set_position(nx, ny)
        else:
            self._bolt = BT.clone().set_position(nx, ny)
            self.current_level.add_sprite(self._bolt)
        sp2 = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
        return sp2 is not None and "receptor" in sp2.tags

    def step(self) -> None:
        if self.action.id == GameAction.ACTION5:
            if self._step_ray():
                self.next_level()
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
