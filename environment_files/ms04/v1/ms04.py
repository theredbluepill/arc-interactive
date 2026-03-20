"""ms04: edge mine clues — numbers count mines sharing a unit edge; ACTION6 flags a cell."""

from __future__ import annotations

from arcengine import ARCBaseGame, Camera, GameAction, Level, RenderableUserDisplay, Sprite

BG, PAD = 5, 4
G = 8
CAM = 16


class Ms04UI(RenderableUserDisplay):
    def render_interface(self, frame):
        return frame


def mk(mines: list[tuple[int, int]], d: int) -> Level:
    sl: list[Sprite] = []
    clue = [[0 for _ in range(G)] for _ in range(G)]
    ms = set(mines)
    for y in range(G):
        for x in range(G):
            if (x, y) in ms:
                continue
            n = 0
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                if (x + dx, y + dy) in ms:
                    n += 1
            clue[y][x] = n
            c = min(15, 5 + n)
            sl.append(
                Sprite(
                    pixels=[[c]],
                    name="c",
                    visible=True,
                    collidable=False,
                    tags=["clue"],
                ).clone().set_position(x, y)
            )
    return Level(
        sprites=sl,
        grid_size=(G, G),
        data={"mines": [list(p) for p in mines], "difficulty": d},
    )


levels = [
    mk([(2, 2), (5, 5)], 1),
    mk([(1, 1), (6, 6), (3, 5)], 2),
    mk([(0, 0), (7, 7)], 3),
    mk([(2, 4), (5, 3), (4, 6)], 4),
    mk([(x, x) for x in range(0, 8, 2)], 5),
    mk([(1, 3), (5, 1), (6, 6)], 6),
    mk([(3, 3), (4, 4), (3, 4), (4, 3)], 7),
]


class Ms04(ARCBaseGame):
    def __init__(self) -> None:
        super().__init__(
            "ms04",
            levels,
            Camera(0, 0, CAM, CAM, BG, PAD, [Ms04UI()]),
            False,
            1,
            [6],
        )

    def on_set_level(self, level: Level) -> None:
        self._mines = {tuple(int(t) for t in p) for p in level.get_data("mines")}
        self._flags: set[tuple[int, int]] = set()

    def step(self) -> None:
        if self.action.id != GameAction.ACTION6:
            self.complete_action()
            return
        c = self.camera.display_to_grid(
            self.action.data.get("x", 0), self.action.data.get("y", 0)
        )
        if c:
            self._flags.add((int(c[0]), int(c[1])))
            if self._flags >= self._mines:
                self.next_level()
        self.complete_action()
