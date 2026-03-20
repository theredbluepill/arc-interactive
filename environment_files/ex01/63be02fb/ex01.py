"""Exit pad: stand on the green pad and use ACTION5 (hold) N times in a row to clear the level.

HUD: orange 2×2 (top-left) = use ACTION5 on the pad; bottom row = one segment per ``hold_frames``
(required charges); segments fill yellow as you hold, green when complete.
"""

from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Ex01UI(RenderableUserDisplay):
    """Shows ``hold_frames`` as a row of segments; fill progress after each ACTION5 on the pad."""

    MAX_SEGMENTS = 12
    SLOT_W = 3
    SLOT_GAP = 1

    def __init__(self, progress: int, need: int) -> None:
        self._progress = progress
        self._need = need

    def update(self, progress: int, need: int) -> None:
        self._progress = progress
        self._need = need

    @staticmethod
    def _rect(
        frame,
        y0: int,
        x0: int,
        hh: int,
        ww: int,
        color: int,
        h: int,
        w: int,
    ) -> None:
        for dy in range(hh):
            for dx in range(ww):
                py, px = y0 + dy, x0 + dx
                if 0 <= py < h and 0 <= px < w:
                    frame[py, px] = color

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape

        # Legend: ACTION5 = hold / charge on green pad (orange, top-left).
        self._rect(frame, 1, 1, 2, 2, 12, h, w)

        raw_need = max(1, self._need)
        done = self._progress >= raw_need
        n_slot = min(raw_need, self.MAX_SEGMENTS)
        if raw_need > self.MAX_SEGMENTS:
            prog_fill = min(
                n_slot,
                (self._progress * n_slot + raw_need - 1) // raw_need,
            )
        else:
            prog_fill = max(0, min(self._progress, n_slot))

        y_bar = h - 5
        x_start = 2
        seg_w = 2
        seg_h = 3
        pitch = self.SLOT_W + self.SLOT_GAP

        for i in range(n_slot):
            x0 = x_start + i * pitch
            if x0 + seg_w > w - 1:
                break
            if done or i < prog_fill:
                seg_color = 14 if done else 11
            else:
                seg_color = 3
            self._rect(frame, y_bar, x0, seg_h, seg_w, seg_color, h, w)

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


def mk(sl, grid_size, difficulty, hold: int):
    return Level(
        sprites=sl,
        grid_size=grid_size,
        data={"difficulty": difficulty, "hold_frames": hold},
    )


levels = [
    mk(
        [
            sprites["player"].clone().set_position(3, 3),
            sprites["exit_pad"].clone().set_position(3, 3),
        ],
        (8, 8),
        1,
        4,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["exit_pad"].clone().set_position(6, 6),
        ],
        (8, 8),
        2,
        5,
    ),
    mk(
        [
            sprites["player"].clone().set_position(2, 2),
            sprites["exit_pad"].clone().set_position(5, 5),
        ]
        + [sprites["wall"].clone().set_position(4, y) for y in range(8) if y != 3],
        (8, 8),
        3,
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["exit_pad"].clone().set_position(4, 4),
        ],
        (8, 8),
        4,
        6,
    ),
    mk(
        [
            sprites["player"].clone().set_position(7, 7),
            sprites["exit_pad"].clone().set_position(0, 0),
        ],
        (8, 8),
        5,
        5,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Ex01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Ex01UI(0, 1)
        super().__init__(
            "ex01",
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
        need = int(self.current_level.get_data("hold_frames") or 4)
        self._ui.update(0, need)

    def _on_exit_pad(self) -> bool:
        for p in self._pads:
            if self._player.x == p.x and self._player.y == p.y:
                return True
        return False

    def step(self) -> None:
        need = int(self.current_level.get_data("hold_frames") or 4)

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

        self._hold = 0
        need = int(self.current_level.get_data("hold_frames") or 4)
        self._ui.update(0, need)

        dx = 0
        dy = 0
        if self.action.id.value == 1:
            dy = -1
        elif self.action.id.value == 2:
            dy = 1
        elif self.action.id.value == 3:
            dx = -1
        elif self.action.id.value == 4:
            dx = 1

        if dx == 0 and dy == 0:
            self.complete_action()
            return

        nx = self._player.x + dx
        ny = self._player.y + dy
        grid_w, grid_h = self.current_level.grid_size
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
