"""lw04: connect A–B with path length ≤ L and at most K direction changes (corners)."""

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
P = Sprite(pixels=[[9]], name="p", visible=True, collidable=True, tags=["player"])
A = Sprite(pixels=[[6]], name="a", visible=True, collidable=False, tags=["a"])
B = Sprite(pixels=[[7]], name="b", visible=True, collidable=False, tags=["b"])
PATH = Sprite(pixels=[[10]], name="t", visible=True, collidable=False, tags=["path_px"])
W = Sprite(pixels=[[3]], name="w", visible=True, collidable=True, tags=["wall"])


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


class Lw04UI(RenderableUserDisplay):
    def __init__(self, ln: int, crn: int, kcap: int, num_levels: int) -> None:
        self._ln, self._crn, self._kcap = ln, crn, kcap
        self._num_levels = num_levels
        self._level_index = 0
        self._gs: GameState | None = None

    def update(
        self,
        ln: int,
        crn: int,
        kcap: int,
        *,
        level_index: int | None = None,
        gs: GameState | None = None,
    ) -> None:
        self._ln, self._crn, self._kcap = ln, crn, kcap
        if level_index is not None:
            self._level_index = level_index
        if gs is not None:
            self._gs = gs

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        _r_dots(frame, h, w, self._level_index, self._num_levels, 0)
        for i in range(min(self._ln, 12)):
            frame[h - 2, 1 + i] = 10
        for i in range(min(self._crn, 6)):
            frame[h - 2, 20 + i] = 12
        for i in range(min(self._kcap, 6)):
            frame[h - 1, 20 + i] = 4
        go = self._gs == GameState.GAME_OVER
        win = self._gs == GameState.WIN
        _r_bar(frame, h, w, go, win)
        return frame


def corners(path: list[tuple[int, int]]) -> int:
    if len(path) < 3:
        return 0
    c = 0
    for i in range(2, len(path)):
        d1 = (path[i - 1][0] - path[i - 2][0], path[i - 1][1] - path[i - 2][1])
        d2 = (path[i][0] - path[i - 1][0], path[i][1] - path[i - 1][1])
        if d1 != d2:
            c += 1
    return c


def mk(sl: list, max_len: int, kcorn: int, d: int) -> Level:
    exit_coords: list[tuple[int, int]] = []
    for s in sl:
        if "b" in s.tags:
            exit_coords.append((s.x, s.y))
            break
    return Level(
        sprites=sl,
        grid_size=(12, 12),
        data={
            "difficulty": d,
            "max_len": max_len,
            "corner_cap": kcorn,
            "exit_coords": exit_coords,
        },
    )


levels = [
    mk(
        [
            P.clone().set_position(1, 1),
            A.clone().set_position(1, 1),
            B.clone().set_position(4, 1),
        ],
        8,
        2,
        1,
    ),
    mk(
        [
            P.clone().set_position(2, 2),
            A.clone().set_position(2, 2),
            B.clone().set_position(5, 5),
        ],
        14,
        3,
        2,
    ),
    mk(
        [
            P.clone().set_position(0, 0),
            A.clone().set_position(0, 0),
            B.clone().set_position(3, 3),
        ]
        + [W.clone().set_position(1, 1), W.clone().set_position(2, 2)],
        12,
        4,
        3,
    ),
    mk(
        [P.clone().set_position(6, 1), A.clone().set_position(6, 1), B.clone().set_position(6, 8)],
        16,
        2,
        4,
    ),
    mk(
        [P.clone().set_position(1, 5), A.clone().set_position(1, 5), B.clone().set_position(9, 5)],
        18,
        3,
        5,
    ),
    mk(
        [P.clone().set_position(2, 2), A.clone().set_position(2, 2), B.clone().set_position(8, 7)],
        20,
        5,
        6,
    ),
    mk(
        [P.clone().set_position(0, 0), A.clone().set_position(0, 0), B.clone().set_position(10, 10)],
        24,
        6,
        7,
    ),
]

_NUM_LEVELS = len(levels)


class Lw04(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Lw04UI(0, 0, 1, _NUM_LEVELS)
        super().__init__(
            "lw04",
            levels,
            Camera(0, 0, 16, 16, BG, PAD, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 6],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._max_len = int(level.get_data("max_len") or 12)
        self._kcap = int(level.get_data("corner_cap") or 3)
        self._path: list[tuple[int, int]] = []
        for s in list(self.current_level.get_sprites_by_tag("path_px")):
            self.current_level.remove_sprite(s)
        self._ui.update(
            0,
            0,
            self._kcap,
            level_index=self.level_index,
            gs=self._state,
        )

    def _eps(self):
        a = self.current_level.get_sprites_by_tag("a")[0]
        b = self.current_level.get_sprites_by_tag("b")[0]
        return (a.x, a.y), (b.x, b.y)

    def _redraw(self) -> None:
        for s in list(self.current_level.get_sprites_by_tag("path_px")):
            self.current_level.remove_sprite(s)
        ea, eb = self._eps()
        for x, y in self._path:
            if (x, y) in (ea, eb):
                continue
            self.current_level.add_sprite(PATH.clone().set_position(x, y))
        self._ui.update(
            len(self._path),
            corners(self._path),
            self._kcap,
            level_index=self.level_index,
            gs=self._state,
        )

    def step(self) -> None:
        if self.action.id == GameAction.ACTION6:
            hit = self.camera.display_to_grid(
                self.action.data.get("x", 0), self.action.data.get("y", 0)
            )
            if not hit:
                self.complete_action()
                return
            gx, gy = int(hit[0]), int(hit[1])
            gw, gh = self.current_level.grid_size
            if not (0 <= gx < gw and 0 <= gy < gh):
                self.complete_action()
                return
            ea, eb = self._eps()
            if not self._path:
                if (gx, gy) in (ea, eb):
                    self._path.append((gx, gy))
                    self._redraw()
            else:
                lx, ly = self._path[-1]
                if abs(gx - lx) + abs(gy - ly) != 1:
                    self.complete_action()
                    return
                if (gx, gy) in self._path:
                    self.complete_action()
                    return
                sp = self.current_level.get_sprite_at(gx, gy, ignore_collidable=True)
                if sp and "wall" in sp.tags:
                    self.complete_action()
                    return
                trial = self._path + [(gx, gy)]
                if len(trial) > self._max_len or corners(trial) > self._kcap:
                    self.complete_action()
                    return
                self._path = trial
                self._redraw()
                ps = set(self._path)
                if ea in ps and eb in ps:
                    self.next_level()
                    self._ui.update(
                        len(self._path),
                        corners(self._path),
                        self._kcap,
                        level_index=self.level_index,
                        gs=self._state,
                    )
            self.complete_action()
            return

        dx = dy = 0
        if self.action.id.value == 1:
            dy = -1
        elif self.action.id.value == 2:
            dy = 1
        elif self.action.id.value == 3:
            dx = -1
        elif self.action.id.value == 4:
            dx = 1
        else:
            self.complete_action()
            return
        nx, ny = self._player.x + dx, self._player.y + dy
        gw, gh = self.current_level.grid_size
        if 0 <= nx < gw and 0 <= ny < gh:
            sp = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
            if not sp or not sp.is_collidable:
                self._player.set_position(nx, ny)
        self.complete_action()
