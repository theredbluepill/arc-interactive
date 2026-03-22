"""sf04: ACTION5 rotates 3-cell L stencil; ACTION6 paints stencil anchor on grid."""

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
GW, GH = 16, 16
CAM = 16
WALL_C, HINT_C, PNT_C = 3, 2, 11


def rot(dx: int, dy: int, q: int) -> tuple[int, int]:
    for _ in range(q % 4):
        dx, dy = -dy, dx
    return dx, dy


BASE_STENCIL = [(0, 0), (1, 0), (0, 1)]


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


class Sf04UI(RenderableUserDisplay):
    def __init__(self, rotq: int, ok: int, tot: int, li: int = 0, nl: int = 7) -> None:
        self._q, self._ok, self._tot = rotq, ok, tot
        self._li, self._nl = li, nl
        self._state = None

    def update(
        self,
        rotq: int,
        ok: int,
        tot: int,
        *,
        level_index: int | None = None,
        num_levels: int | None = None,
        state=None,
    ) -> None:
        self._q, self._ok, self._tot = rotq, ok, tot
        if level_index is not None:
            self._li = level_index
        if num_levels is not None:
            self._nl = num_levels
        if state is not None:
            self._state = state

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        _r_dots(frame, h, w, self._li, self._nl, 0)
        frame[1, 1] = 10 + (self._q % 4)
        for i in range(min(self._tot, 14)):
            frame[2, 1 + i] = 14 if i < self._ok else 8
        go = self._state == GameState.GAME_OVER
        win = self._state == GameState.WIN
        _r_bar(frame, h, w, go, win)
        return frame


W = Sprite(
    pixels=[[WALL_C]],
    name="w",
    visible=True,
    collidable=True,
    tags=["wall"],
)
H = Sprite(
    pixels=[[HINT_C]],
    name="h",
    visible=True,
    collidable=False,
    tags=["hint"],
)
P = Sprite(
    pixels=[[PNT_C]],
    name="p",
    visible=True,
    collidable=False,
    tags=["paint"],
)


def mk(
    hints: list[tuple[int, int]],
    walls: list[tuple[int, int]],
    max_steps: int,
    d: int,
) -> Level:
    sl = [W.clone().set_position(x, y) for x, y in walls]
    sl += [H.clone().set_position(x, y) for x, y in hints]
    return Level(
        sprites=sl,
        grid_size=(GW, GH),
        data={
            "goal": [list(p) for p in hints],
            "max_steps": max_steps,
            "difficulty": d,
        },
    )


levels = [
    mk([(5, 5), (6, 5), (5, 6)], [], 40, 1),
    mk([(4, 4), (5, 4), (4, 5), (7, 7)], [(6, 6)], 50, 2),
    mk([(3, 3), (4, 3), (3, 4), (8, 8), (9, 8), (8, 9)], [(5, 5), (5, 6)], 60, 3),
    mk([(2, 2), (3, 2), (2, 3), (10, 10), (11, 10), (10, 11)], [(6, 6), (7, 6)], 70, 4),
    mk([(4, 7), (5, 7), (4, 8), (9, 4), (10, 4), (9, 5)], [], 80, 5),
    mk([(6, 6), (7, 6), (6, 7), (6, 9), (7, 9), (6, 10)], [(8, 8)], 90, 6),
    mk([(2, 8), (3, 8), (2, 9), (12, 3), (13, 3), (12, 4), (7, 7)], [(5, 5)], 100, 7),
]


class Sf04(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Sf04UI(0, 0, 0, 0, len(levels))
        super().__init__(
            "sf04",
            levels,
            Camera(0, 0, CAM, CAM, BG, PAD, [self._ui]),
            False,
            1,
            [5, 6],
        )

    def on_set_level(self, level: Level) -> None:
        self._goal = {tuple(p) for p in level.get_data("goal")}
        self._max_steps = int(level.get_data("max_steps") or 50)
        self._steps = 0
        self._rotq = 0
        self._sync()

    def _cells(self, ax: int, ay: int) -> list[tuple[int, int]]:
        return [
            (ax + rot(dx, dy, self._rotq)[0], ay + rot(dx, dy, self._rotq)[1])
            for dx, dy in BASE_STENCIL
        ]

    def _painted(self) -> set[tuple[int, int]]:
        return {(s.x, s.y) for s in self.current_level.get_sprites_by_tag("paint")}

    def _sync(self) -> None:
        painted = self._painted()
        ok = len(painted & self._goal)
        self._ui.update(
            self._rotq,
            ok,
            len(self._goal),
            level_index=self.level_index,
            num_levels=len(levels),
            state=self._state,
        )

    def step(self) -> None:
        if self.action.id == GameAction.ACTION5:
            self._rotq = (self._rotq + 1) % 4
            self._steps += 1
            self._sync()
            if self._steps >= self._max_steps:
                self.lose()
            self.complete_action()
            return

        if self.action.id == GameAction.ACTION6:
            hit = self.camera.display_to_grid(
                self.action.data.get("x", 0), self.action.data.get("y", 0)
            )
            if hit:
                ax, ay = int(hit[0]), int(hit[1])
                for cx, cy in self._cells(ax, ay):
                    if not (0 <= cx < GW and 0 <= cy < GH):
                        self._steps += 1
                        self._sync()
                        self.complete_action()
                        return
                    sp = self.current_level.get_sprite_at(cx, cy, ignore_collidable=True)
                    if sp and "wall" in sp.tags:
                        self._steps += 1
                        self._sync()
                        self.complete_action()
                        return
                for cx, cy in self._cells(ax, ay):
                    ex = self.current_level.get_sprite_at(cx, cy, ignore_collidable=True)
                    if ex and "paint" in ex.tags:
                        continue
                    self.current_level.add_sprite(P.clone().set_position(cx, cy))
            self._steps += 1
            self._sync()
            if self._goal <= self._painted():
                self.next_level()
            elif self._steps >= self._max_steps:
                self.lose()
            self.complete_action()
            return

        self.complete_action()
