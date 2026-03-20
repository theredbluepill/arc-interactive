"""rs04: XOR phase — only targets whose color matches the XOR-safe palette may be cleared."""

from __future__ import annotations

from arcengine import ARCBaseGame, Camera, GameAction, Level, RenderableUserDisplay, Sprite

BG, PAD = 5, 4
G = 10
CAM = 16
SAFE = (8, 9)


class Rs04UI(RenderableUserDisplay):
    def __init__(self, a: int, b: int) -> None:
        self._a, self._b = a, b

    def update(self, a: int, b: int) -> None:
        self._a, self._b = a, b

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        frame[h - 2, 2] = SAFE[0] if self._a else SAFE[1]
        frame[h - 2, 4] = SAFE[1] if self._b else SAFE[0]
        return frame


def tgt(x, y, c):
    return Sprite(
        pixels=[[c]],
        name="t",
        visible=True,
        collidable=False,
        tags=["target", f"c{c}"],
    ).clone().set_position(x, y)


def mk(items: list[tuple[int, int, int]], d: int) -> Level:
    sl = [tgt(x, y, c) for x, y, c in items]
    return Level(
        sprites=sl,
        grid_size=(G, G),
        data={"items": [[x, y, c] for x, y, c in items], "difficulty": d},
    )


levels = [
    mk([(2, 5, 8), (7, 5, 9)], 1),
    mk([(3, 3, 8), (6, 6, 9), (3, 6, 8)], 2),
    mk([(x, 5, 8 if x % 2 == 0 else 9) for x in range(2, 8)], 3),
    mk([(2, 2, 9), (8, 8, 8), (2, 8, 9)], 4),
    mk([(4, 4, 8), (5, 5, 9), (6, 4, 8)], 5),
    mk([(1, 1, 8), (8, 1, 9), (1, 8, 9), (8, 8, 8)], 6),
    mk([(x, y, 8 if (x + y) % 2 == 0 else 9) for x in range(3, 7) for y in range(3, 7)], 7),
]


class Rs04(ARCBaseGame):
    def __init__(self) -> None:
        self._hud = Rs04UI(0, 0)
        super().__init__(
            "rs04",
            levels,
            Camera(0, 0, CAM, CAM, BG, PAD, [self._hud]),
            False,
            1,
            [5, 6],
        )

    def on_set_level(self, level: Level) -> None:
        self._a = self._b = 0
        self._steps = 0
        self._hud.update(self._a, self._b)

    def _safe(self) -> int:
        return SAFE[(int(self._a) ^ int(self._b)) & 1]

    def step(self) -> None:
        if self.action.id == GameAction.ACTION5:
            self._a = 1 - self._a
            self._steps += 1
            if self._steps % 3 == 0:
                self._b = 1 - self._b
            self._hud.update(self._a, self._b)
            self.complete_action()
            return
        if self.action.id == GameAction.ACTION6:
            c = self.camera.display_to_grid(
                self.action.data.get("x", 0), self.action.data.get("y", 0)
            )
            if c:
                gx, gy = int(c[0]), int(c[1])
                sp = self.current_level.get_sprite_at(gx, gy, ignore_collidable=True)
                if sp and "target" in sp.tags:
                    col = sp.pixels[0][0]
                    if int(col) == self._safe():
                        self.current_level.remove_sprite(sp)
            left = list(self.current_level.get_sprites_by_tag("target"))
            if not left:
                self.next_level()
            self.complete_action()
            return
        self.complete_action()
