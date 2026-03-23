"""Knight courier: ACTION1–4 are four L-moves from bank A; ACTION5 toggles to bank B (the other four knight offsets). Reach the yellow goal."""

from __future__ import annotations

from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)

BACKGROUND_COLOR = 5
PADDING_COLOR = 4
CAM = 16

BANK_A = ((-2, -1), (-2, 1), (2, -1), (2, 1))
BANK_B = ((-1, -2), (-1, 2), (1, -2), (1, 2))


class Kn01UI(RenderableUserDisplay):
    def __init__(self, bank: int) -> None:
        self._bank = bank

    def update(self, bank: int) -> None:
        self._bank = bank

    @staticmethod
    def _rp(frame, hh: int, ww: int, x: int, y: int, c: int) -> None:
        if 0 <= x < ww and 0 <= y < hh:
            frame[y, x] = c

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        frame[h - 2, 2] = 10 if self._bank == 0 else 6
        bank = BANK_A if self._bank == 0 else BANK_B
        for i in range(4):
            dx, dy = bank[i]
            ox = 4 + i * 7
            oy = h - 6
            for yy in range(5):
                for xx in range(5):
                    self._rp(frame, h, w, ox + xx, oy + yy, 5)
            self._rp(frame, h, w, ox + 2 + dx, oy + 2 + dy, 10)
        return frame


sprites = {
    "player": Sprite(
        pixels=[[9]],
        name="player",
        visible=True,
        collidable=True,
        tags=["player"],
    ),
    "goal": Sprite(
        pixels=[[11]],
        name="goal",
        visible=True,
        collidable=False,
        tags=["goal"],
    ),
    "wall": Sprite(
        pixels=[[3]],
        name="wall",
        visible=True,
        collidable=True,
        tags=["wall"],
    ),
}


def mk(
    p: tuple[int, int],
    g: tuple[int, int],
    walls: list[tuple[int, int]],
    diff: int,
) -> Level:
    sl = [
        sprites["player"].clone().set_position(*p),
        sprites["goal"].clone().set_position(*g),
    ]
    for wx, wy in walls:
        sl.append(sprites["wall"].clone().set_position(wx, wy))
    return Level(sprites=sl, grid_size=(CAM, CAM), data={"difficulty": diff})


levels = [
    mk((2, 8), (12, 8), [(x, 7) for x in range(16) if 4 < x < 12], 1),
    mk((1, 1), (14, 14), [(8, y) for y in range(16) if y != 7 and y != 8], 2),
    mk((0, 0), (15, 15), [(x, x) for x in range(16) if 4 < x < 12], 3),
    mk((8, 1), (8, 14), [(5, y) for y in range(16)] + [(11, y) for y in range(16)], 4),
    mk((2, 2), (13, 13), [(7, y) for y in range(16) if y % 3 != 1], 5),
]


class Kn01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Kn01UI(0)
        super().__init__(
            "kn01",
            levels,
            Camera(0, 0, CAM, CAM, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 5],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._bank = 0
        self._ui.update(self._bank)

    def step(self) -> None:
        aid = self.action.id.value

        if aid == 5:
            self._bank = 1 - self._bank
            self._ui.update(self._bank)
            self.complete_action()
            return

        if aid not in (1, 2, 3, 4):
            self.complete_action()
            return

        bank = BANK_A if self._bank == 0 else BANK_B
        dx, dy = bank[aid - 1]
        nx, ny = self._player.x + dx, self._player.y + dy
        gw, gh = self.current_level.grid_size
        if not (0 <= nx < gw and 0 <= ny < gh):
            self.complete_action()
            return
        sp = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
        if sp and "wall" in sp.tags:
            self.complete_action()
            return
        self._player.set_position(nx, ny)
        go = self.current_level.get_sprites_by_tag("goal")[0]
        if self._player.x == go.x and self._player.y == go.y:
            self.next_level()
        self.complete_action()
