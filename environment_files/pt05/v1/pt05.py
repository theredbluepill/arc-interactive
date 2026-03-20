"""pt05: click row header (x=0) to cycle that row’s colors left; match key."""

from __future__ import annotations

from arcengine import ARCBaseGame, Camera, GameAction, Level, RenderableUserDisplay, Sprite

BG, PAD = 5, 4
W, H = 8, 8
CAM = 16
HEADER_X = 0


def pix(c: int) -> Sprite:
    return Sprite(
        pixels=[[c]],
        name="px",
        visible=True,
        collidable=False,
        tags=["rowcell"],
    )


class Pt05UI(RenderableUserDisplay):
    def render_interface(self, frame):
        return frame


def mk_row(rows: list[list[int]], targ: list[list[int]], diff: int) -> Level:
    sl: list[Sprite] = []
    for y in range(1, H):
        sl.append(
            Sprite(
                pixels=[[11]],
                name="hdr",
                visible=True,
                collidable=False,
                tags=["header"],
            ).clone().set_position(HEADER_X, y)
        )
        for x in range(1, W):
            sl.append(pix(rows[y - 1][x - 1]).clone().set_position(x, y))
    return Level(
        sprites=sl,
        grid_size=(W, H),
        data={
            "difficulty": diff,
            "target": [list(r) for r in targ],
        },
    )


def row(vals: list[int]) -> list[int]:
    return vals + [3] * (7 - len(vals))


levels = [
    mk_row(
        [row([9, 11, 14]), row([3, 3, 3]), row([3, 3, 3]), row([3, 3, 3]), row([3, 3, 3]), row([3, 3, 3]), row([3, 3, 3])],
        [row([11, 9, 14]), row([3, 3, 3]), row([3, 3, 3]), row([3, 3, 3]), row([3, 3, 3]), row([3, 3, 3]), row([3, 3, 3])],
        1,
    ),
    mk_row(
        [
            row([10, 10, 10]),
            row([8, 8, 8]),
            row([3, 3, 3]),
            row([3, 3, 3]),
            row([3, 3, 3]),
            row([3, 3, 3]),
            row([3, 3, 3]),
        ],
        [
            row([10, 10, 10]),
            row([8, 8, 8]),
            row([3, 3, 3]),
            row([3, 3, 3]),
            row([3, 3, 3]),
            row([3, 3, 3]),
            row([3, 3, 3]),
        ],
        2,
    ),
    mk_row(
        [
            row([9, 11, 14, 10]),
            row([11, 14, 10, 9]),
            row([3, 3, 3, 3]),
            row([3, 3, 3, 3]),
            row([3, 3, 3, 3]),
            row([3, 3, 3, 3]),
            row([3, 3, 3, 3]),
        ],
        [
            row([14, 10, 9, 11]),
            row([10, 9, 11, 14]),
            row([3, 3, 3, 3]),
            row([3, 3, 3, 3]),
            row([3, 3, 3, 3]),
            row([3, 3, 3, 3]),
            row([3, 3, 3, 3]),
        ],
        3,
    ),
    mk_row(
        [
            row([12, 3, 3, 3]),
            row([3, 12, 3, 3]),
            row([3, 3, 12, 3]),
            row([3, 3, 3, 3]),
            row([3, 3, 3, 3]),
            row([3, 3, 3, 3]),
            row([3, 3, 3, 3]),
        ],
        [
            row([3, 3, 12, 3]),
            row([3, 12, 3, 3]),
            row([12, 3, 3, 3]),
            row([3, 3, 3, 3]),
            row([3, 3, 3, 3]),
            row([3, 3, 3, 3]),
            row([3, 3, 3, 3]),
        ],
        4,
    ),
    mk_row(
        [
            row([9, 9, 11, 11]),
            row([11, 11, 9, 9]),
            row([3, 3, 3, 3]),
            row([3, 3, 3, 3]),
            row([3, 3, 3, 3]),
            row([3, 3, 3, 3]),
            row([3, 3, 3, 3]),
        ],
        [
            row([11, 11, 9, 9]),
            row([9, 9, 11, 11]),
            row([3, 3, 3, 3]),
            row([3, 3, 3, 3]),
            row([3, 3, 3, 3]),
            row([3, 3, 3, 3]),
            row([3, 3, 3, 3]),
        ],
        5,
    ),
    mk_row(
        [
            row([10, 8, 14]),
            row([8, 14, 10]),
            row([14, 10, 8]),
            row([3, 3, 3]),
            row([3, 3, 3]),
            row([3, 3, 3]),
            row([3, 3, 3]),
        ],
        [
            row([14, 10, 8]),
            row([10, 8, 14]),
            row([8, 14, 10]),
            row([3, 3, 3]),
            row([3, 3, 3]),
            row([3, 3, 3]),
            row([3, 3, 3]),
        ],
        6,
    ),
    mk_row(
        [
            row([9, 11, 14, 10, 8]),
            row([3, 3, 3, 3, 3]),
            row([3, 3, 3, 3, 3]),
            row([3, 3, 3, 3, 3]),
            row([3, 3, 3, 3, 3]),
            row([3, 3, 3, 3, 3]),
            row([3, 3, 3, 3, 3]),
        ],
        [
            row([8, 10, 14, 11, 9]),
            row([3, 3, 3, 3, 3]),
            row([3, 3, 3, 3, 3]),
            row([3, 3, 3, 3, 3]),
            row([3, 3, 3, 3, 3]),
            row([3, 3, 3, 3, 3]),
            row([3, 3, 3, 3, 3]),
        ],
        7,
    ),
]


class Pt05(ARCBaseGame):
    def __init__(self) -> None:
        super().__init__(
            "pt05",
            levels,
            Camera(0, 0, CAM, CAM, BG, PAD, [Pt05UI()]),
            False,
            1,
            [1, 2, 3, 4, 6],
        )

    def on_set_level(self, level: Level) -> None:
        self._target = level.get_data("target")
        self._by_pos: dict[tuple[int, int], Sprite] = {}
        for sp in self.current_level.get_sprites_by_tag("rowcell"):
            self._by_pos[(sp.x, sp.y)] = sp
        self._headers: dict[int, Sprite] = {}
        for sp in self.current_level.get_sprites_by_tag("header"):
            self._headers[sp.y] = sp

    def _row_vals(self, y: int) -> list[int]:
        return [self._by_pos[(x, y)].pixels[0][0] for x in range(1, W)]

    def _cycle_row(self, y: int) -> None:
        vals = self._row_vals(y)
        if not vals:
            return
        nv = vals[1:] + [vals[0]]
        for x in range(1, W):
            self._by_pos[(x, y)].pixels = [[nv[x - 1]]]

    def _win(self) -> bool:
        for yi, row in enumerate(self._target, start=1):
            for xi in range(1, W):
                if self._by_pos[(xi, yi)].pixels[0][0] != row[xi - 1]:
                    return False
        return True

    def step(self) -> None:
        if self.action.id == GameAction.ACTION6:
            c = self.camera.display_to_grid(
                self.action.data.get("x", 0), self.action.data.get("y", 0)
            )
            if c:
                gx, gy = c
                if gx == HEADER_X and gy in self._headers:
                    self._cycle_row(gy)
                    if self._win():
                        self.next_level()
            self.complete_action()
            return
        self.complete_action()
