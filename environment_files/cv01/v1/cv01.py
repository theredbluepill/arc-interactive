"""cv01: list coloring — each cell may use only its palette; **ACTION6** cycles choice; neighbors must differ."""

from __future__ import annotations

import numpy as np

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

G = 8
CAM = 16
PAL = (8, 9, 11, 12)


class Cv01UI(RenderableUserDisplay):
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


def mk(grid_choices: list[list[list[int]]], d: int) -> Level:
    sl: list[Sprite] = []
    for y in range(G):
        for x in range(G):
            opts = grid_choices[y][x]
            c = PAL[opts[0] % len(PAL)]
            sl.append(
                Sprite(
                    pixels=[[c]],
                    name="cell",
                    visible=True,
                    collidable=False,
                    tags=["cell", f"{x},{y}"],
                )
                .clone()
                .set_position(x, y)
            )
    return Level(
        sprites=sl,
        grid_size=(G, G),
        data={"choices": grid_choices, "difficulty": d},
    )


levels = [
    mk([[ [0, 1] for _ in range(G)] for _ in range(G)], 1),
    mk([[ [0, 1, 2] if (i + j) % 2 == 0 else [0, 1] for j in range(G)] for i in range(G)], 2),
    mk([[ [(i + j) % 3, (i + j + 1) % 3] for j in range(G)] for i in range(G)], 3),
    mk([[ [0, 2] if i % 2 == 0 else [1, 2] for j in range(G)] for i in range(G)], 4),
    mk([[ [0, 1] if j < 4 else [1, 2] for j in range(G)] for i in range(G)], 5),
    mk([[ [0, 1, 2, 3] for _ in range(G)] for _ in range(G)], 6),
    mk([[ [0, 1] if (i // 2 + j // 2) % 2 == 0 else [2, 3] for j in range(G)] for i in range(G)], 7),
]


class Cv01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Cv01UI(0, len(levels), 1)
        super().__init__(
            "cv01",
            levels,
            Camera(0, 0, CAM, CAM, BG, PAD, [self._ui]),
            False,
            1,
            [6],
        )


    def _sync_ui(self) -> None:
        self._ui.update(
            level_index=self.level_index,
            num_levels=len(levels),
            ticks=1,
            state=self._state,
        )

    def on_set_level(self, level: Level) -> None:
        self._choices = level.get_data("choices")
        self._idx = [[0 for _ in range(G)] for _ in range(G)]

    def _color_at(self, x: int, y: int) -> int:
        opts = self._choices[y][x]
        pi = self._idx[y][x] % len(opts)
        return PAL[int(opts[pi]) % len(PAL)]

    def _ok(self) -> bool:
        for y in range(G):
            for x in range(G):
                c = self._color_at(x, y)
                for dx, dy in ((0, 1), (1, 0)):
                    nx, ny = x + dx, y + dy
                    if nx < G and ny < G and self._color_at(nx, ny) == c:
                        return False
        return True

    def step(self) -> None:
        if self.action.id != GameAction.ACTION6:
            self._sync_ui()
            self.complete_action()
            return
        c = self.camera.display_to_grid(
            self.action.data.get("x", 0), self.action.data.get("y", 0)
        )
        if c:
            gx, gy = int(c[0]), int(c[1])
            n = len(self._choices[gy][gx])
            self._idx[gy][gx] = (self._idx[gy][gx] + 1) % n
            sp = self.current_level.get_sprite_at(gx, gy, ignore_collidable=True)
            if sp and "cell" in sp.tags:
                sp.pixels = np.array([[self._color_at(gx, gy)]], dtype=np.int8)
        if self._ok():
            self.next_level()
        self._sync_ui()
        self.complete_action()
