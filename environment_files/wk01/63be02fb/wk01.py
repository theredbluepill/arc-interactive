"""Weak floor: leaving a brown tile makes it collapse into a hole; stepping into a hole loses."""

from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Wk01UI(RenderableUserDisplay):
    """Bottom-right: **red** = stepped in a **hole**; **maroon** in play. Bottom-left **13** = weak-floor cue."""

    def __init__(self) -> None:
        self._fail = False

    def update(self, *, fail: bool | None = None) -> None:
        if fail is not None:
            self._fail = fail

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        br = 8 if self._fail else 13
        bl = 8 if self._fail else 13
        for dy in range(4):
            for dx in range(4):
                frame[h - 4 + dy, w - 4 + dx] = br
        for dy in range(3):
            for dx in range(3):
                frame[h - 4 + dy, dx] = bl
        return frame


sprites = {
    "player": Sprite(
        pixels=[[9]],
        name="player",
        visible=True,
        collidable=True,
        tags=["player"],
    ),
    "target": Sprite(
        pixels=[[11]],
        name="target",
        visible=True,
        collidable=False,
        tags=["target"],
    ),
    "weak": Sprite(
        pixels=[[13]],
        name="weak",
        visible=True,
        collidable=False,
        tags=["weak"],
    ),
    "hole": Sprite(
        pixels=[[5]],
        name="hole",
        visible=True,
        collidable=True,
        tags=["hole"],
    ),
    "wall": Sprite(
        pixels=[[3]],
        name="wall",
        visible=True,
        collidable=True,
        tags=["wall"],
    ),
}


def mk(sl, grid_size, difficulty):
    return Level(sprites=sl, grid_size=grid_size, data={"difficulty": difficulty})


levels = [
    mk(
        [
            sprites["player"].clone().set_position(0, 3),
            sprites["weak"].clone().set_position(3, 3),
            sprites["target"].clone().set_position(6, 3),
        ],
        (8, 8),
        1,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["weak"].clone().set_position(2, 2),
            sprites["weak"].clone().set_position(4, 4),
            sprites["target"].clone().set_position(6, 6),
        ],
        (8, 8),
        2,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["weak"].clone().set_position(1, 0),
            sprites["target"].clone().set_position(7, 7),
        ],
        (8, 8),
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(2, 2),
            sprites["weak"].clone().set_position(3, 2),
            sprites["weak"].clone().set_position(4, 2),
            sprites["target"].clone().set_position(5, 6),
        ],
        (8, 8),
        4,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 7),
            sprites["weak"].clone().set_position(4, 4),
            sprites["target"].clone().set_position(7, 0),
        ],
        (8, 8),
        5,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Wk01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Wk01UI()
        super().__init__(
            "wk01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._targets = self.current_level.get_sprites_by_tag("target")
        self._prev_pos = (self._player.x, self._player.y)
        self._ui.update(fail=False)

    def _collapse_weak(self, left_pos: tuple[int, int]) -> None:
        wx, wy = left_pos
        sp = self.current_level.get_sprite_at(wx, wy, ignore_collidable=True)
        if sp and "weak" in sp.tags:
            self.current_level.remove_sprite(sp)
            hole = sprites["hole"].clone().set_position(wx, wy)
            self.current_level.add_sprite(hole)

    def step(self) -> None:
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

        prev = (self._player.x, self._player.y)
        new_x = self._player.x + dx
        new_y = self._player.y + dy
        grid_w, grid_h = self.current_level.grid_size
        if not (0 <= new_x < grid_w and 0 <= new_y < grid_h):
            self.complete_action()
            return

        sprite = self.current_level.get_sprite_at(new_x, new_y, ignore_collidable=True)

        if sprite and "wall" in sprite.tags:
            self.complete_action()
            return

        if sprite and "hole" in sprite.tags:
            self._ui.update(fail=True)
            self.lose()
            self.complete_action()
            return

        if not sprite or not sprite.is_collidable:
            self._collapse_weak(prev)
            self._player.set_position(new_x, new_y)

        for t in self._targets:
            if self._player.x == t.x and self._player.y == t.y:
                self.next_level()
                break

        self.complete_action()
