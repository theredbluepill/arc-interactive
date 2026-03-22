"""**ml04** — stepped bolt, fixed mirror slots (10×10 grid).

**Vs ml01–ml03:** **ml04** uses a **10×10** grid (camera matches **G** after level load). **ACTION5** advances
the laser **one cell** per press (visible **bolt** sprite). **ACTION6** cycles each mirror
tile through **``/`` → ``\\`` → empty** — no inventory, no free placement. Optional
**``emit_dir``** in level data sets initial bolt facing **0–3** (E/S/W/N); default **0**.
**ml01** is global placement + continuous ray; **ml02**/**ml03** add a moving technician and
adjacency for mirror edits; **ml03** also **consumes** mirrors that reflected the beam.
"""

from __future__ import annotations

from arcengine import ARCBaseGame, Camera, GameAction, GameState, Level, RenderableUserDisplay, Sprite

BG, PAD = 5, 4


def _rp(frame, h, w, x, y, c):
    if 0 <= x < w and 0 <= y < h:
        frame[y, x] = c


def _r_dots(frame, h, w, li, n, y0=0):
    for i in range(min(n, 14)):
        cx = 1 + i * 2
        if cx >= w:
            break
        c = 14 if i < li else (11 if i == li else 3)
        _rp(frame, h, w, cx, y0, c)


def _r_ticks(frame, h, w, n, y=None):
    row = (h - 1) if y is None else y
    for i in range(max(0, min(n, 8))):
        _rp(frame, h, w, 1 + i, row, 11)


def _r_bar(frame, h, w, game_over, win):
    if not (game_over or win):
        return
    r = h - 3
    if r < 0:
        return
    c = 14 if win else 8
    for x in range(min(w, 16)):
        _rp(frame, h, w, x, r, c)

G = 10
DX = (1, 0, -1, 0)
DY = (0, 1, 0, -1)
# dir 0=E,1=S,2=W,3=N — / mirror
REF_SLASH = {0: 3, 3: 0, 1: 2, 2: 1}
REF_BSL = {0: 1, 1: 0, 2: 3, 3: 2}


class Ml04UI(RenderableUserDisplay):
    def __init__(self, level_index: int = 0, num_levels: int = 1, ticks: int = 1) -> None:
        self._level_index = level_index
        self._num_levels = num_levels
        self._ticks = ticks
        self._state = None

    def update(
        self,
        *,
        level_index: int | None = None,
        num_levels: int | None = None,
        ticks: int | None = None,
        state=None,
    ) -> None:
        if level_index is not None:
            self._level_index = level_index
        if num_levels is not None:
            self._num_levels = num_levels
        if ticks is not None:
            self._ticks = ticks
        if state is not None:
            self._state = state

    def render_interface(self, frame):
        import numpy as np

        from arcengine import GameState

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        _r_dots(frame, h, w, self._level_index, self._num_levels, 0)
        _r_ticks(frame, h, w, self._ticks)
        go = self._state == GameState.GAME_OVER
        win = self._state == GameState.WIN
        _r_bar(frame, h, w, go, win)
        return frame


W = Sprite(pixels=[[3]], name="w", visible=True, collidable=True, tags=["wall"])
EM = Sprite(pixels=[[10]], name="e", visible=True, collidable=False, tags=["emitter"])
RC = Sprite(pixels=[[11]], name="r", visible=True, collidable=False, tags=["receptor"])
MV = Sprite(pixels=[[6]], name="m", visible=True, collidable=False, tags=["mirror"])
BT = Sprite(pixels=[[12]], name="b", visible=True, collidable=False, tags=["bolt"])


def mk(walls, mirrors, emitter, receptor, d, emit_dir: int | None = None):
    data: dict = {
        "mirrors": [[x, y, t] for x, y, t in mirrors],
        "difficulty": d,
    }
    if emit_dir is not None:
        data["emit_dir"] = int(emit_dir) % 4
    sl = [W.clone().set_position(x, y) for x, y in walls]
    for x, y, _ in mirrors:
        sl.append(MV.clone().set_position(x, y))
    sl.append(EM.clone().set_position(*emitter))
    sl.append(RC.clone().set_position(*receptor))
    return Level(
        sprites=sl,
        grid_size=(G, G),
        data=data,
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
    # L4 — vertical run (needs initial facing south; east-only would miss column mirrors).
    mk(bd(), [(5, 4, 1), (5, 6, 2)], (5, 2), (5, 8), 4, emit_dir=1),
    # L5–L6 — east corridor puzzles (prior diagonal layouts were unreachable at dir 0).
    mk(bd(), [(4, y, y % 3) for y in range(4, 7)], (1, 5), (8, 5), 5),
    mk(bd(), [(x, 5, (x + 1) % 3) for x in range(3, 7)], (1, 5), (8, 5), 6),
    mk(bd(), [(4, 5, 0), (5, 5, 1), (6, 5, 2)], (2, 5), (8, 5), 7),
]


class Ml04(ARCBaseGame):
    def __init__(self) -> None:
        self._bolt: Sprite | None = None
        self._ui = Ml04UI(0, len(levels), 1)
        super().__init__(
            "ml04",
            levels,
            Camera(0, 0, G, G, BG, PAD, [self._ui]),
            False,
            1,
            [5, 6],
        )


    def _sync_ui(self) -> None:
        self._ui.update(
            level_index=self.level_index,
            num_levels=len(levels),
            ticks=1,
            state=self._state,
        )

    def on_set_level(self, level: Level) -> None:
        self._mir: dict[tuple[int, int], int] = {}
        for r in level.get_data("mirrors") or []:
            self._mir[(int(r[0]), int(r[1]))] = int(r[2]) % 3
        e = self.current_level.get_sprites_by_tag("emitter")[0]
        self._ex, self._ey = e.x, e.y
        ed = self.current_level.get_data("emit_dir")
        self._dir = int(ed) % 4 if ed is not None else 0
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
            self._sync_ui()
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
            self._sync_ui()
            self.complete_action()
            return
        self._sync_ui()
        self.complete_action()
