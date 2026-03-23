"""Independent dominating set: toggle floor cells; no two orth-adjacent selected; cover every marked cell (itself or neighbor)."""

from __future__ import annotations

from arcengine import (
    ARCBaseGame,
    Camera,
    GameAction,
    GameState,
    Level,
    RenderableUserDisplay,
    Sprite,
)

BG, PAD = 5, 4
GW = GH = 8
CAM = 16
MARK_C = 2
SEL_C = 14
WALL_C = 3


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


def _r_bar(frame, h, w, game_over, win):
    if not (game_over or win):
        return
    r = h - 3
    if r < 0:
        return
    c = 14 if win else 8
    for x in range(min(w, 16)):
        _rp(frame, h, w, x, r, c)


class Ct01UI(RenderableUserDisplay):
    def __init__(self, ok: bool, level_index: int = 0, num_levels: int = 7) -> None:
        self._ok = ok
        self._level_index = level_index
        self._num_levels = num_levels
        self._state = None
        self._reject_frames = 0

    def pulse_reject(self) -> None:
        self._reject_frames = 14

    def update(
        self,
        ok: bool,
        *,
        level_index: int | None = None,
        num_levels: int | None = None,
        state=None,
    ) -> None:
        self._ok = ok
        if level_index is not None:
            self._level_index = level_index
        if num_levels is not None:
            self._num_levels = num_levels
        if state is not None:
            self._state = state

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        _r_dots(frame, h, w, self._level_index, self._num_levels, 0)
        if self._reject_frames > 0:
            _rp(frame, h, w, 31, h - 2, 12)
            self._reject_frames -= 1
        frame[h - 2, 28] = 14 if self._ok else 8
        go = self._state == GameState.GAME_OVER
        win = self._state == GameState.WIN
        _r_bar(frame, h, w, go, win)
        return frame


sprites = {
    "wall": Sprite(
        pixels=[[WALL_C]],
        name="wall",
        visible=True,
        collidable=True,
        tags=["wall"],
    ),
    "mark": Sprite(
        pixels=[[MARK_C]],
        name="mark",
        visible=True,
        collidable=False,
        tags=["must_cover"],
    ),
    "sel": Sprite(
        pixels=[[SEL_C]],
        name="sel",
        visible=True,
        collidable=False,
        tags=["picked"],
    ),
}


def mk(
    must_cover: list[tuple[int, int]],
    walls: list[tuple[int, int]],
    diff: int,
) -> Level:
    sl: list[Sprite] = []
    for wx, wy in walls:
        sl.append(sprites["wall"].clone().set_position(wx, wy))
    for mx, my in must_cover:
        sl.append(sprites["mark"].clone().set_position(mx, my))
    return Level(
        sprites=sl,
        grid_size=(GW, GH),
        data={
            "difficulty": diff,
            "must_cover": [list(p) for p in must_cover],
        },
    )


levels = [
    mk([(0, 0), (1, 0), (0, 1), (1, 1)], [(2, y) for y in range(8)] + [(x, 2) for x in range(3, 8)], 1),
    mk([(2, 2), (5, 2), (2, 5), (5, 5)], [], 2),
    mk([(x, 3) for x in range(8)], [(x, 0) for x in range(8)] + [(x, 7) for x in range(8)], 3),
    mk([(1, 1), (6, 1), (1, 6), (6, 6), (3, 3)], [(4, 4)], 4),
    mk([(2, 2), (3, 2), (4, 2), (5, 2), (3, 4), (4, 4)], [(2, 4), (5, 4)], 5),
    mk([(0, 2), (2, 0), (5, 5), (7, 7)], [(3, 3), (4, 4)], 6),
    mk([(1, 2), (2, 3), (4, 4), (5, 5), (6, 6)], [], 7),
]


class Ct01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Ct01UI(False, 0, len(levels))
        super().__init__(
            "ct01",
            levels,
            Camera(0, 0, CAM, CAM, BG, PAD, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 6],
        )

    def on_set_level(self, level: Level) -> None:
        raw = self.current_level.get_data("must_cover") or []
        self._must = {tuple(int(t) for t in p) for p in raw}
        self._walls = set()
        for s in self.current_level.get_sprites_by_tag("wall"):
            self._walls.add((s.x, s.y))
        self._floor = {
            (x, y)
            for x in range(GW)
            for y in range(GH)
            if (x, y) not in self._walls
        }
        self._selected: set[tuple[int, int]] = set()
        self._refresh()
        self._sync_ui()

    def _refresh(self) -> None:
        for s in list(self.current_level.get_sprites_by_tag("picked")):
            self.current_level.remove_sprite(s)
        for p in self._selected:
            self.current_level.add_sprite(sprites["sel"].clone().set_position(p[0], p[1]))

    def _independent(self) -> bool:
        for x, y in self._selected:
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                if (x + dx, y + dy) in self._selected:
                    return False
        return True

    def _dominates(self) -> bool:
        for c in self._must:
            if c in self._selected:
                continue
            ok = False
            for dx, dy in ((0, 0), (0, 1), (0, -1), (1, 0), (-1, 0)):
                if (c[0] + dx, c[1] + dy) in self._selected:
                    ok = True
                    break
            if not ok:
                return False
        return True

    def _sync_ui(self) -> None:
        self._ui.update(
            self._independent() and self._dominates(),
            level_index=self.level_index,
            num_levels=len(levels),
            state=self._state,
        )

    def step(self) -> None:
        if self.action.id.value in (1, 2, 3, 4):
            self.complete_action()
            return

        if self.action.id != GameAction.ACTION6:
            self.complete_action()
            return

        hit = self.camera.display_to_grid(
            int(self.action.data.get("x", 0)),
            int(self.action.data.get("y", 0)),
        )
        if hit is None:
            self.complete_action()
            return
        gx, gy = int(hit[0]), int(hit[1])
        p = (gx, gy)
        if p not in self._floor:
            self.complete_action()
            return

        if p in self._selected:
            self._selected.remove(p)
        else:
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                if (gx + dx, gy + dy) in self._selected:
                    self._ui.pulse_reject()
                    self._sync_ui()
                    self.complete_action()
                    return
            self._selected.add(p)

        self._refresh()
        if self._independent() and self._dominates():
            self.next_level()

        self._sync_ui()
        self.complete_action()
