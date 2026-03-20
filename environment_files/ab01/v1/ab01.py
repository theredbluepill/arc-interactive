"""ab01: sandpile win when stable and total grains mod P equals R."""

from __future__ import annotations

from arcengine import ARCBaseGame, Camera, GameAction, Level, RenderableUserDisplay, Sprite

BG, PAD = 5, 4
GW = GH = 10
CAM = 16
WC = 3


class Ab01UI(RenderableUserDisplay):
    def __init__(self, s: int, p: int, r: int) -> None:
        self._s, self._p, self._r = s, p, r

    def update(self, s: int, p: int, r: int) -> None:
        self._s, self._p, self._r = s, p, r

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for i in range(min(self._s, 18)):
            frame[h - 2, 1 + i] = 11
        frame[h - 1, 2] = (self._p % 10) + 5
        frame[h - 1, 4] = (self._r % 10) + 5
        return frame


def px(n: int) -> Sprite:
    c = min(15, 5 + n)
    return Sprite(
        pixels=[[c]], name="s", visible=True, collidable=False, tags=["sand"]
    )


def mk(walls: list[tuple[int, int]], P: int, R: int, max_s: int, d: int) -> Level:
    sl = [
        Sprite(
            pixels=[[WC]],
            name="w",
            visible=True,
            collidable=True,
            tags=["wall"],
        ).clone().set_position(x, y)
        for x, y in walls
    ]
    return Level(
        sprites=sl,
        grid_size=(GW, GH),
        data={"difficulty": d, "mod_p": P, "mod_r": R, "max_steps": max_s},
    )


levels = [
    mk([], 5, 0, 180, 1),
    mk([(5, y) for y in range(10) if y != 4], 7, 3, 200, 2),
    mk([], 4, 2, 220, 3),
    mk([(0, y) for y in range(10)], 6, 1, 240, 4),
    mk([(3, 3), (6, 6)], 5, 4, 260, 5),
    mk([], 3, 0, 200, 6),
    mk([(x, 5) for x in range(10) if x != 5], 8, 5, 280, 7),
]


class Ab01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Ab01UI(0, 5, 0)
        super().__init__(
            "ab01",
            levels,
            Camera(0, 0, CAM, CAM, BG, PAD, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 6],
        )

    def on_set_level(self, level: Level) -> None:
        self._P = int(level.get_data("mod_p") or 5)
        self._R = int(level.get_data("mod_r") or 0)
        self._g = [[0 for _ in range(GW)] for _ in range(GH)]
        self._left = int(level.get_data("max_steps") or 200)
        self._ui.update(self._left, self._P, self._R)
        self._ref()

    def _wall(self, x: int, y: int) -> bool:
        sp = self.current_level.get_sprite_at(x, y, ignore_collidable=True)
        return sp is not None and "wall" in sp.tags

    def _ref(self) -> None:
        for s in list(self.current_level.get_sprites_by_tag("sand")):
            self.current_level.remove_sprite(s)
        for y in range(GH):
            for x in range(GW):
                if self._wall(x, y):
                    continue
                n = self._g[y][x]
                if n > 0:
                    self.current_level.add_sprite(px(n).clone().set_position(x, y))

    def _top(self) -> None:
        ch = True
        while ch:
            ch = False
            nxt = [r[:] for r in self._g]
            for y in range(GH):
                for x in range(GW):
                    if self._wall(x, y) or self._g[y][x] < 4:
                        continue
                    nxt[y][x] -= 4
                    for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                        nx, ny = x + dx, y + dy
                        if (
                            0 <= nx < GW
                            and 0 <= ny < GH
                            and not self._wall(nx, ny)
                        ):
                            nxt[ny][nx] += 1
                    ch = True
            self._g = nxt

    def _sum(self) -> int:
        return sum(
            self._g[y][x]
            for y in range(GH)
            for x in range(GW)
            if not self._wall(x, y)
        )

    def _win(self) -> bool:
        if any(
            self._g[y][x] >= 4
            for y in range(GH)
            for x in range(GW)
            if not self._wall(x, y)
        ):
            return False
        return (self._sum() % self._P) == (self._R % self._P)

    def step(self) -> None:
        if self.action.id.value in (1, 2, 3, 4):
            self.complete_action()
            return
        if self.action.id != GameAction.ACTION6:
            self.complete_action()
            return
        if self._left <= 0:
            self.lose()
            self.complete_action()
            return
        c = self.camera.display_to_grid(
            self.action.data.get("x", 0), self.action.data.get("y", 0)
        )
        if not c:
            self.complete_action()
            return
        gx, gy = int(c[0]), int(c[1])
        if not (0 <= gx < GW and 0 <= gy < GH) or self._wall(gx, gy):
            self.complete_action()
            return
        self._g[gy][gx] += 1
        self._top()
        self._ref()
        self._left -= 1
        self._ui.update(self._left, self._P, self._R)
        if self._win():
            self.next_level()
        elif self._left <= 0:
            self.lose()
        self.complete_action()
