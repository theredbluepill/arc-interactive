"""Moving exit pad: like exit hold with sliding decay, but the green pad shifts one cell every `pad_period` steps (`pad_delta` in data)."""

from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Ex03UI(RenderableUserDisplay):
    def __init__(self, progress: int, need: int) -> None:
        self._progress = progress
        self._need = need

    def update(self, progress: int, need: int) -> None:
        self._progress = progress
        self._need = need

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        color = 14 if self._progress >= self._need else 11
        for dy in range(4):
            for dx in range(4):
                frame[h - 4 + dy, w - 4 + dx] = color
        return frame


sprites = {
    "player": Sprite(
        pixels=[[9]],
        name="player",
        visible=True,
        collidable=True,
        tags=["player"],
    ),
    "exit_pad": Sprite(
        pixels=[[14]],
        name="exit_pad",
        visible=True,
        collidable=False,
        tags=["exit_pad"],
    ),
    "wall": Sprite(
        pixels=[[3]],
        name="wall",
        visible=True,
        collidable=True,
        tags=["wall"],
    ),
}


def mk(sl, grid_size, difficulty, hold: int, period: int = 4, pad_delta=None):
    if pad_delta is None:
        pad_delta = [1, 0]
    return Level(
        sprites=sl,
        grid_size=grid_size,
        data={
            "difficulty": difficulty,
            "hold_frames": hold,
            "pad_period": period,
            "pad_delta": pad_delta,
        },
    )


levels = [
    mk(
        [
            sprites["player"].clone().set_position(3, 3),
            sprites["exit_pad"].clone().set_position(3, 3),
        ],
        (8, 8),
        1,
        5,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["exit_pad"].clone().set_position(6, 6),
        ],
        (8, 8),
        2,
        6,
    ),
    mk(
        [
            sprites["player"].clone().set_position(2, 2),
            sprites["exit_pad"].clone().set_position(5, 5),
        ]
        + [sprites["wall"].clone().set_position(4, y) for y in range(8) if y != 3],
        (8, 8),
        3,
        4,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["exit_pad"].clone().set_position(4, 4),
        ],
        (8, 8),
        4,
        7,
    ),
    mk(
        [
            sprites["player"].clone().set_position(7, 7),
            sprites["exit_pad"].clone().set_position(0, 0),
        ],
        (8, 8),
        5,
        6,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Ex03(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Ex03UI(0, 1)
        self._pads: list = []
        self._pad_tick = 0
        super().__init__(
            "ex03",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 5],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._pads = self.current_level.get_sprites_by_tag("exit_pad")
        self._hold = 0
        self._pad_tick = 0
        need = int(self.current_level.get_data("hold_frames") or 4)
        self._ui.update(0, need)

    def _slide_pads(self) -> None:
        period = int(self.current_level.get_data("pad_period") or 4)
        pd = self.current_level.get_data("pad_delta") or [1, 0]
        dx, dy = int(pd[0]), int(pd[1])
        self._pad_tick += 1
        if self._pad_tick % period != 0:
            return
        gw, gh = self.current_level.grid_size
        for p in self._pads:
            nx, ny = p.x + dx, p.y + dy
            if not (0 <= nx < gw and 0 <= ny < gh):
                continue
            sp = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
            if sp and "wall" in sp.tags:
                continue
            ride = self._player.x == p.x and self._player.y == p.y
            p.set_position(nx, ny)
            if ride:
                self._player.set_position(nx, ny)

    def _on_exit_pad(self) -> bool:
        for p in self._pads:
            if self._player.x == p.x and self._player.y == p.y:
                return True
        return False

    def step(self) -> None:
        need = int(self.current_level.get_data("hold_frames") or 4)
        self._slide_pads()

        if self.action.id.value == 5:
            if self._on_exit_pad():
                self._hold += 1
                self._ui.update(self._hold, need)
                if self._hold >= need:
                    self.next_level()
            else:
                self._hold = 0
                self._ui.update(0, need)
            self.complete_action()
            return

        dx = dy = 0
        if self.action.id.value == 1:
            dy = -1
        elif self.action.id.value == 2:
            dy = 1
        elif self.action.id.value == 3:
            dx = -1
        elif self.action.id.value == 4:
            dx = 1

        if dx != 0 or dy != 0:
            if self._hold > 0:
                self._hold -= 1
                self._ui.update(self._hold, need)

        nx = self._player.x + dx
        ny = self._player.y + dy
        grid_w, grid_h = self.current_level.grid_size
        if dx == 0 and dy == 0:
            self.complete_action()
            return
        if not (0 <= nx < grid_w and 0 <= ny < grid_h):
            self.complete_action()
            return

        sprite = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
        if sprite and "wall" in sprite.tags:
            self.complete_action()
            return

        if not sprite or not sprite.is_collidable:
            self._player.set_position(nx, ny)

        self.complete_action()
