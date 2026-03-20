"""sp04: sandpile with sink cells — grains toppling into a sink vanish."""

from __future__ import annotations

from arcengine import ARCBaseGame, Camera, GameAction, Level, RenderableUserDisplay, Sprite

BG, PAD = 5, 4
GW = GH = 12
CAM = 16
WALL_C = 3
SINK_C = 10


class Sp04UI(RenderableUserDisplay):
    def __init__(self, s: int) -> None:
        self._s = s

    def update(self, s: int) -> None:
        self._s = s

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for i in range(min(self._s, 20)):
            frame[h - 2, 1 + i] = 11
        return frame


def _px(n: int) -> Sprite:
    c = min(15, 5 + n)
    return Sprite(
        pixels=[[c]], name="sand", visible=True, collidable=False, tags=["sand"]
    )


def mk(
    walls: list[tuple[int, int]],
    sinks: list[tuple[int, int]],
    target_sum: int,
    max_steps: int,
    d: int,
) -> Level:
    sl: list[Sprite] = []
    for wx, wy in walls:
        sl.append(
            Sprite(
                pixels=[[WALL_C]],
                name="wall",
                visible=True,
                collidable=True,
                tags=["wall"],
            ).clone().set_position(wx, wy),
        )
    for sx, sy in sinks:
        sl.append(
            Sprite(
                pixels=[[SINK_C]],
                name="sink",
                visible=True,
                collidable=True,
                tags=["sink"],
            ).clone().set_position(sx, sy),
        )
    return Level(
        sprites=sl,
        grid_size=(GW, GH),
        data={
            "difficulty": d,
            "target_sum": target_sum,
            "max_steps": max_steps,
            "sinks": [list(p) for p in sinks],
        },
    )


levels = [
    mk([], [(6, 6)], 20, 220, 1),
    mk([(6, y) for y in range(12) if y != 5], [(5, 5), (7, 5)], 30, 260, 2),
    mk([], [(0, 0), (11, 11)], 40, 300, 3),
    mk([(0, y) for y in range(12)], [], 28, 320, 4),
    mk([(3, 3), (8, 8)], [(5, 5)], 24, 280, 5),
    mk([], [(2, 2), (9, 9), (5, 8)], 36, 340, 6),
    mk([(x, 6) for x in range(12) if x not in (5, 6)], [(6, 6)], 32, 360, 7),
]


class Sp04(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Sp04UI(0)
        super().__init__(
            "sp04",
            levels,
            Camera(0, 0, CAM, CAM, BG, PAD, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 6],
        )

    def on_set_level(self, level: Level) -> None:
        self._target_sum = int(level.get_data("target_sum") or 0)
        raw = level.get_data("sinks") or []
        self._sinks = {(int(a), int(b)) for a, b in raw}
        self._g = [[0 for _ in range(GW)] for _ in range(GH)]
        self._steps_left = int(level.get_data("max_steps") or 200)
        self._refresh()

    def _wall(self, x: int, y: int) -> bool:
        sp = self.current_level.get_sprite_at(x, y, ignore_collidable=True)
        return sp is not None and "wall" in sp.tags

    def _sink(self, x: int, y: int) -> bool:
        return (x, y) in self._sinks

    def _refresh(self) -> None:
        for s in list(self.current_level.get_sprites_by_tag("sand")):
            self.current_level.remove_sprite(s)
        for y in range(GH):
            for x in range(GW):
                if self._wall(x, y) or self._sink(x, y):
                    continue
                n = self._g[y][x]
                if n > 0:
                    self.current_level.add_sprite(_px(n).clone().set_position(x, y))

    def _topple(self) -> None:
        changed = True
        while changed:
            changed = False
            nxt = [row[:] for row in self._g]
            for y in range(GH):
                for x in range(GW):
                    if self._wall(x, y) or self._sink(x, y):
                        continue
                    if self._g[y][x] < 4:
                        continue
                    nxt[y][x] -= 4
                    for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                        nx, ny = x + dx, y + dy
                        if not (0 <= nx < GW and 0 <= ny < GH):
                            continue
                        if self._wall(nx, ny):
                            continue
                        if self._sink(nx, ny):
                            continue
                        nxt[ny][nx] += 1
                    changed = True
            self._g = nxt

    def _win(self) -> bool:
        if any(
            self._g[y][x] >= 4
            for y in range(GH)
            for x in range(GW)
            if not self._wall(x, y) and not self._sink(x, y)
        ):
            return False
        s = sum(
            self._g[y][x]
            for y in range(GH)
            for x in range(GW)
            if not self._wall(x, y) and not self._sink(x, y)
        )
        return s == self._target_sum

    def step(self) -> None:
        if self.action.id.value in (1, 2, 3, 4):
            self.complete_action()
            return
        if self.action.id != GameAction.ACTION6:
            self.complete_action()
            return
        if self._steps_left <= 0:
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
        if (
            not (0 <= gx < GW and 0 <= gy < GH)
            or self._wall(gx, gy)
            or self._sink(gx, gy)
        ):
            self.complete_action()
            return
        self._g[gy][gx] += 1
        self._topple()
        self._refresh()
        self._steps_left -= 1
        self._ui.update(self._steps_left)
        if self._win():
            self.next_level()
        elif self._steps_left <= 0:
            self.lose()
        self.complete_action()
