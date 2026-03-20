"""cv01: list coloring — each cell may use only its palette; **ACTION6** cycles choice; neighbors must differ."""

from __future__ import annotations

from arcengine import ARCBaseGame, Camera, GameAction, Level, RenderableUserDisplay, Sprite

BG, PAD = 5, 4
G = 8
CAM = 16
PAL = (8, 9, 11, 12)


class Cv01UI(RenderableUserDisplay):
    def render_interface(self, frame):
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
        super().__init__(
            "cv01",
            levels,
            Camera(0, 0, CAM, CAM, BG, PAD, [Cv01UI()]),
            False,
            1,
            [6],
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
                sp.pixels = [[self._color_at(gx, gy)]]
        if self._ok():
            self.next_level()
        self.complete_action()
