"""Nonogram lite: 8×8 grid. ACTION1–4 move cursor; ACTION6 (click) cycles cell under cursor in display space via display_to_grid. Match the hidden solution in level data."""

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
CAM = 16
EMPTY_C = 2
FILL_C = 9
MARK_C = 8
CURSOR_C = 0
WALL_C = 3


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
        scale = min(64 // CAM, 64 // CAM)
        pad = (64 - CAM * scale) // 2
        px = self._cx * scale + pad
        py = self._cy * scale + pad
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


def mk(sol_rows: list[str], diff: int) -> Level:
    sol = _parse_sol(sol_rows)
    assert len(sol) == GW and all(len(r) == GW for r in sol)
    return Level(
        sprites=[],
        grid_size=(GW, GH),
        data={"difficulty": diff, "solution": sol},
    )


levels = [
    mk(
        [
            "........",
            "..##....",
            "..##....",
            "........",
            "....##..",
            "....##..",
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
            Camera(0, 0, CAM, CAM, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 6],
        )

    def on_set_level(self, level: Level) -> None:
        self._sol = self.current_level.get_data("solution")
        self._st = [[0 for _ in range(GW)] for _ in range(GH)]
        self._cx = self._cy = 0
        for s in list(self.current_level.get_sprites_by_tag("ng_cell")):
            self.current_level.remove_sprite(s)
        self._refresh_cells()
        self._ui.update(self._cx, self._cy)

    def _refresh_cells(self) -> None:
        for s in list(self.current_level.get_sprites_by_tag("ng_cell")):
            self.current_level.remove_sprite(s)
        for y in range(GH):
            for x in range(GW):
                t = self._st[y][x]
                c = EMPTY_C if t == 0 else (FILL_C if t == 1 else MARK_C)
                self.current_level.add_sprite(_cell_sprite(c).set_position(x, y))

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
                if 0 <= gx < GW and 0 <= gy < GH:
                    self._cx, self._cy = gx, gy
                    t = self._st[gy][gx]
                    self._st[gy][gx] = (t + 1) % 3
                    self._refresh_cells()
                    if self._win():
                        self.next_level()

        self._ui.update(self._cx, self._cy)
        self.complete_action()
