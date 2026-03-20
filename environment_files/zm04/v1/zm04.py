"""zm04: infection spread on ACTION6; ACTION5 switches active strain (0 vs 1); inoculate blocks one expand."""

from __future__ import annotations

from arcengine import ARCBaseGame, Camera, GameAction, Level, RenderableUserDisplay, Sprite

BG, PAD = 5, 4
G = 12
CAM = 16
Z0, Z1 = 8, 6
VAC = 14
BLK = 3


class Zm04UI(RenderableUserDisplay):
    def __init__(self, strain: int, cnt: int, need: int) -> None:
        self._s, self._c, self._n = strain, cnt, need

    def update(self, strain: int, cnt: int, need: int) -> None:
        self._s, self._c, self._n = strain, cnt, need

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        frame[1, 2] = Z0 if self._s == 0 else Z1
        for i in range(min(self._c, 15)):
            frame[h - 2, 1 + i] = 11
        return frame


def mk(
    start0: list[tuple[int, int]],
    start1: list[tuple[int, int]],
    need: int,
    max_steps: int,
    d: int,
) -> Level:
    sl: list[Sprite] = []
    for x, y in start0:
        sl.append(
            Sprite(
                pixels=[[Z0]],
                name="z0",
                visible=True,
                collidable=False,
                tags=["z0"],
            ).clone().set_position(x, y)
        )
    for x, y in start1:
        sl.append(
            Sprite(
                pixels=[[Z1]],
                name="z1",
                visible=True,
                collidable=False,
                tags=["z1"],
            ).clone().set_position(x, y)
        )
    return Level(
        sprites=sl,
        grid_size=(G, G),
        data={
            "start0": [list(p) for p in start0],
            "start1": [list(p) for p in start1],
            "need_infected": need,
            "max_steps": max_steps,
            "difficulty": d,
        },
    )


levels = [
    mk([(5, 5)], [], 8, 50, 1),
    mk([(3, 3)], [(8, 8)], 12, 60, 2),
    mk([(2, 2), (9, 9)], [], 15, 70, 3),
    mk([(6, 6)], [(2, 9)], 18, 80, 4),
    mk([(1, 1), (10, 10)], [(5, 5)], 20, 90, 5),
    mk([(4, 4)], [(7, 7)], 14, 55, 6),
    mk([(3, 6), (8, 3)], [], 22, 100, 7),
]


class Zm04(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Zm04UI(0, 0, 1)
        self._strain = 0
        self._block: set[tuple[int, int]] = set()
        super().__init__(
            "zm04",
            levels,
            Camera(0, 0, CAM, CAM, BG, PAD, [self._ui]),
            False,
            1,
            [5, 6],
        )

    def on_set_level(self, level: Level) -> None:
        self._need = int(level.get_data("need_infected") or 10)
        self._left = int(level.get_data("max_steps") or 60)
        self._strain = 0
        self._block = set()
        self._sync()

    def _cells(self, tag: str) -> set[tuple[int, int]]:
        return {(s.x, s.y) for s in self.current_level.get_sprites_by_tag(tag)}

    def _count_active(self) -> int:
        tag = "z0" if self._strain == 0 else "z1"
        return len(self._cells(tag))

    def _sync(self) -> None:
        self._ui.update(self._strain, self._count_active(), self._need)

    def _expand(self) -> None:
        tag = "z0" if self._strain == 0 else "z1"
        col = Z0 if self._strain == 0 else Z1
        cur = self._cells(tag)
        ntag = "z0" if self._strain == 0 else "z1"
        for x, y in list(cur):
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                nx, ny = x + dx, y + dy
                if not (0 <= nx < G and 0 <= ny < G):
                    continue
                if (nx, ny) in self._block:
                    continue
                if (nx, ny) in self._cells("z0") or (nx, ny) in self._cells("z1"):
                    continue
                self.current_level.add_sprite(
                    Sprite(
                        pixels=[[col]],
                        name=ntag,
                        visible=True,
                        collidable=False,
                        tags=[ntag],
                    ).clone().set_position(nx, ny)
                )

    def step(self) -> None:
        if self.action.id == GameAction.ACTION5:
            self._strain = 1 - self._strain
            self._left -= 1
            self._expand()
            self._sync()
            if self._count_active() >= self._need:
                self.next_level()
            elif self._left <= 0:
                self.lose()
            self.complete_action()
            return
        if self.action.id == GameAction.ACTION6:
            c = self.camera.display_to_grid(
                self.action.data.get("x", 0), self.action.data.get("y", 0)
            )
            if c:
                gx, gy = int(c[0]), int(c[1])
                self._block.add((gx, gy))
                self.current_level.add_sprite(
                    Sprite(
                        pixels=[[BLK]],
                        name="b",
                        visible=True,
                        collidable=True,
                        tags=["block"],
                    ).clone().set_position(gx, gy)
                )
            self._left -= 1
            self._expand()
            self._sync()
            if self._count_active() >= self._need:
                self.next_level()
            elif self._left <= 0:
                self.lose()
            self.complete_action()
            return
        self.complete_action()
