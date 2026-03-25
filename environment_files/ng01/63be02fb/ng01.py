"""Nonogram lite: 8×8 playfield with visible row/column run clues on a 1-cell border. ACTION1–4 move cursor; ACTION6 cycles empty / filled / mark. Win when filled cells match the solution.

Level 1 is a teaching layout: one full row gives a single row run clue matching all eight cells, and each column shows a single 1-run, so the nonogram convention (counts of consecutive filled cells) is inferable without prior puzzle exposure.
"""

from __future__ import annotations

from arcengine import (
    ARCBaseGame,
    Camera,
    GameAction,
    Level,
    RenderableUserDisplay,
    Sprite,
)

BACKGROUND_COLOR = 5
PADDING_COLOR = 4
GW = GH = 8
# 10×10: 2×2 corner + row hints on x=0–1, col hints on y=0–1, playfield (2..9,2..9).
OUT = 10
OFF = 2
EMPTY_C = 2
FILL_C = 9
MARK_C = 8
HINT_BG = 5
# Clue digits 1..8 map to distinct palette indices (avoid clash with play colors).
_CLUE_BASE = 12


class Ng01UI(RenderableUserDisplay):
    def __init__(self, cx: int, cy: int) -> None:
        self._cx = cx
        self._cy = cy

    def update(self, cx: int, cy: int) -> None:
        self._cx = cx
        self._cy = cy

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        scale = max(1, min(64 // OUT, 64 // OUT))
        pad = (64 - OUT * scale) // 2
        px = (OFF + self._cx) * scale + pad
        py = (OFF + self._cy) * scale + pad
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            x, y = px + dx, py + dy
            if 0 <= x < w and 0 <= y < h:
                frame[y, x] = 11
        return frame


def _cell_sprite(color: int) -> Sprite:
    return Sprite(
        pixels=[[color]],
        name="ng_cell",
        visible=True,
        collidable=False,
        tags=["ng_cell"],
    )


def _parse_sol(rows: list[str]) -> list[list[int]]:
    return [[1 if c == "#" else 0 for c in row] for row in rows]


def _runs(line: list[int]) -> list[int]:
    out: list[int] = []
    c = 0
    for v in line:
        if v == 1:
            c += 1
        elif c:
            out.append(c)
            c = 0
    if c:
        out.append(c)
    return out if out else [0]


def _clue_color(n: int) -> int:
    n = int(n)
    if n <= 0:
        return HINT_BG
    return min(_CLUE_BASE + n - 1, 15)


def mk(sol_rows: list[str], diff: int) -> Level:
    sol = _parse_sol(sol_rows)
    assert len(sol) == GW and all(len(r) == GW for r in sol)
    row_clues = [_runs(sol[y]) for y in range(GH)]
    col_clues: list[list[int]] = []
    for x in range(GW):
        col = [sol[y][x] for y in range(GH)]
        col_clues.append(_runs(col))
    return Level(
        sprites=[],
        grid_size=(OUT, OUT),
        data={
            "difficulty": diff,
            "solution": sol,
            "row_clues": row_clues,
            "col_clues": col_clues,
        },
    )


levels = [
    mk(
        [
            "........",
            "........",
            "........",
            "########",
            "........",
            "........",
            "........",
            "........",
        ],
        1,
    ),
    mk(
        [
            "####....",
            "#..#....",
            "#..#....",
            "####....",
            "........",
            "....####",
            "....#..#",
            "....####",
        ],
        2,
    ),
    mk(
        [
            ".#.#.#.#",
            "#.#.#.#.",
            ".#.#.#.#",
            "#.#.#.#.",
            ".#.#.#.#",
            "#.#.#.#.",
            "........",
            "########",
        ],
        3,
    ),
    mk(
        [
            "........",
            ".####...",
            ".#..#...",
            ".#..#...",
            ".####...",
            "........",
            "...###..",
            "...###..",
        ],
        4,
    ),
    mk(
        [
            "##......",
            "##......",
            "....##..",
            "....##..",
            "..##....",
            "..##....",
            "......##",
            "......##",
        ],
        5,
    ),
]


class Ng01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Ng01UI(0, 0)
        super().__init__(
            "ng01",
            levels,
            Camera(0, 0, OUT, OUT, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 6],
        )

    def on_set_level(self, level: Level) -> None:
        self._sol = self.current_level.get_data("solution")
        self._row_clues = self.current_level.get_data("row_clues") or []
        self._col_clues = self.current_level.get_data("col_clues") or []
        self._st = [[0 for _ in range(GW)] for _ in range(GH)]
        self._cx = self._cy = 0
        for s in list(self.current_level.get_sprites_by_tag("ng_cell")):
            self.current_level.remove_sprite(s)
        self._refresh_cells()
        self._ui.update(self._cx, self._cy)

    def _refresh_cells(self) -> None:
        for s in list(self.current_level.get_sprites_by_tag("ng_cell")):
            self.current_level.remove_sprite(s)
        for y in range(OUT):
            for x in range(OUT):
                if y < OFF and x < OFF:
                    self.current_level.add_sprite(_cell_sprite(HINT_BG).set_position(x, y))
                    continue
                if y < OFF and x >= OFF:
                    if x < OFF + GW:
                        cc = self._col_clues[x - OFF]
                        if y == 0:
                            c = _clue_color(cc[0]) if len(cc) > 0 else HINT_BG
                        else:
                            c = _clue_color(cc[1]) if len(cc) > 1 else HINT_BG
                        self.current_level.add_sprite(_cell_sprite(c).set_position(x, y))
                    else:
                        self.current_level.add_sprite(_cell_sprite(HINT_BG).set_position(x, y))
                    continue
                if x < OFF and y >= OFF:
                    if y < OFF + GH:
                        rc = self._row_clues[y - OFF]
                        if x == 0:
                            c = _clue_color(rc[0]) if len(rc) > 0 else HINT_BG
                        else:
                            c = _clue_color(rc[1]) if len(rc) > 1 else HINT_BG
                        self.current_level.add_sprite(_cell_sprite(c).set_position(x, y))
                    else:
                        self.current_level.add_sprite(_cell_sprite(HINT_BG).set_position(x, y))
                    continue
                if x >= OFF and y >= OFF and x < OFF + GW and y < OFF + GH:
                    lx, ly = x - OFF, y - OFF
                    t = self._st[ly][lx]
                    want = self._sol[ly][lx]
                    if t == 0:
                        c = EMPTY_C
                    elif t == 1:
                        c = FILL_C if want == 1 else 8
                    else:
                        c = MARK_C
                    self.current_level.add_sprite(_cell_sprite(c).set_position(x, y))
                    continue
                self.current_level.add_sprite(_cell_sprite(HINT_BG).set_position(x, y))

    def _win(self) -> bool:
        for y in range(GH):
            for x in range(GW):
                want = self._sol[y][x]
                got = 1 if self._st[y][x] == 1 else 0
                if want != got:
                    return False
        return True

    def step(self) -> None:
        aid = self.action.id

        if aid == GameAction.ACTION1 and self._cy > 0:
            self._cy -= 1
        elif aid == GameAction.ACTION2 and self._cy < GH - 1:
            self._cy += 1
        elif aid == GameAction.ACTION3 and self._cx > 0:
            self._cx -= 1
        elif aid == GameAction.ACTION4 and self._cx < GW - 1:
            self._cx += 1
        elif aid == GameAction.ACTION6:
            px = int(self.action.data.get("x", 0))
            py = int(self.action.data.get("y", 0))
            hit = self.camera.display_to_grid(px, py)
            if hit is not None:
                gx, gy = int(hit[0]), int(hit[1])
                if OFF <= gx < OFF + GW and OFF <= gy < OFF + GH:
                    lx, ly = gx - OFF, gy - OFF
                    self._cx, self._cy = lx, ly
                    t = self._st[ly][lx]
                    self._st[ly][lx] = (t + 1) % 3
                    self._refresh_cells()
                    if self._win():
                        self.next_level()

        self._ui.update(self._cx, self._cy)
        self.complete_action()
