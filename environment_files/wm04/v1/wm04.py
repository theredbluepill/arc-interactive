"""wm04: whack — wrong click adds penalty steps before next mole."""

from __future__ import annotations

import random

from arcengine import ARCBaseGame, Camera, GameAction, Level, RenderableUserDisplay, Sprite

BG, PAD = 5, 4
G = 8
CAM = 16
HOLE = 3
MOLE = 14


class Wm04UI(RenderableUserDisplay):
    def __init__(self, pen: int) -> None:
        self._p = pen

    def update(self, pen: int) -> None:
        self._p = pen

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for i in range(min(self._p, 8)):
            frame[h - 2, 1 + i] = 8
        return frame


def mk(d: int) -> Level:
    return Level(sprites=[], grid_size=(G, G), data={"difficulty": d, "need": 4 + d})


levels = [mk(i) for i in range(1, 8)]


class Wm04(ARCBaseGame):
    def __init__(self) -> None:
        self._hud = Wm04UI(0)
        self._rng = random.Random(0)
        super().__init__(
            "wm04",
            levels,
            Camera(0, 0, CAM, CAM, BG, PAD, [self._hud]),
            False,
            1,
            [1, 2, 3, 4, 6],
        )

    def on_set_level(self, level: Level) -> None:
        for t in ("mole", "hole"):
            for s in list(self.current_level.get_sprites_by_tag(t)):
                self.current_level.remove_sprite(s)
        self._need = int(level.get_data("need") or 5)
        self._hit = 0
        self._pen = 0
        self._up = 0
        self._spawn()

    def _spawn(self) -> None:
        for s in list(self.current_level.get_sprites_by_tag("mole")):
            self.current_level.remove_sprite(s)
        self._up = self._rng.randint(0, G * G - 1)
        x, y = self._up % G, self._up // G
        self.current_level.add_sprite(
            Sprite(
                pixels=[[MOLE]],
                name="m",
                visible=True,
                collidable=False,
                tags=["mole"],
            ).clone().set_position(x, y)
        )

    def step(self) -> None:
        if self.action.id == GameAction.ACTION6:
            c = self.camera.display_to_grid(
                self.action.data.get("x", 0), self.action.data.get("y", 0)
            )
            if c:
                gx, gy = int(c[0]), int(c[1])
                idx = gy * G + gx
                if idx == self._up:
                    self._hit += 1
                    self._spawn()
                    if self._hit >= self._need:
                        self.next_level()
                else:
                    self._pen += 2
                    for _ in range(self._pen):
                        self._rng.random()
                    self._spawn()
            self._hud.update(self._pen)
            self.complete_action()
            return
        self.complete_action()
