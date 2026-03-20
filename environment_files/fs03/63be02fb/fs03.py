from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Fs03UI(RenderableUserDisplay):
    def __init__(self, idx: int, total: int) -> None:
        self._idx = idx
        self._total = total

    def update(self, idx: int, total: int) -> None:
        self._idx = idx
        self._total = total

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for i in range(min(self._total, 4)):
            c = 14 if i < self._idx else 11
            for dy in range(2):
                for dx in range(2):
                    frame[h - 4 + dy, w - 8 + i * 2 + dx] = c
        return frame


sprites = {
    "player": Sprite(
        pixels=[[9]],
        name="player",
        visible=True,
        collidable=True,
        tags=["player"],
    ),
    "switch": Sprite(
        pixels=[[11]],
        name="switch",
        visible=True,
        collidable=False,
        tags=["switch"],
    ),
    "door": Sprite(
        pixels=[[3]],
        name="door",
        visible=True,
        collidable=True,
        tags=["door"],
    ),
    "target": Sprite(
        pixels=[[14]],
        name="target",
        visible=True,
        collidable=False,
        tags=["target"],
    ),
    "wall": Sprite(
        pixels=[[3]],
        name="wall",
        visible=True,
        collidable=True,
        tags=["wall"],
    ),
}


def mk(sl, grid_size, difficulty, order_len):
    return Level(
        sprites=sl,
        grid_size=grid_size,
        data={"difficulty": difficulty, "order_len": order_len},
    )


levels = [
    mk(
        [
            sprites["player"].clone().set_position(0, 3),
            sprites["switch"].clone().set_position(2, 3),
            sprites["switch"].clone().set_position(6, 3),
            sprites["door"].clone().set_position(4, 3),
            sprites["target"].clone().set_position(7, 3),
        ],
        (8, 8),
        1,
        2,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["switch"].clone().set_position(1, 5),
            sprites["switch"].clone().set_position(5, 1),
            sprites["door"].clone().set_position(3, 3),
            sprites["target"].clone().set_position(6, 6),
        ]
        + [sprites["wall"].clone().set_position(x, 2) for x in range(8) if x != 3],
        (8, 8),
        2,
        2,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["switch"].clone().set_position(2, 0),
            sprites["switch"].clone().set_position(0, 2),
            sprites["switch"].clone().set_position(2, 2),
            sprites["door"].clone().set_position(4, 1),
            sprites["target"].clone().set_position(7, 1),
        ]
        + [sprites["wall"].clone().set_position(3, y) for y in range(8) if y != 1],
        (8, 8),
        3,
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 4),
            sprites["switch"].clone().set_position(2, 2),
            sprites["switch"].clone().set_position(2, 6),
            sprites["door"].clone().set_position(5, 4),
            sprites["target"].clone().set_position(8, 4),
        ]
        + [sprites["wall"].clone().set_position(4, y) for y in range(8) if y != 4],
        (10, 8),
        4,
        2,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 7),
            sprites["switch"].clone().set_position(1, 1),
            sprites["switch"].clone().set_position(6, 1),
            sprites["switch"].clone().set_position(1, 6),
            sprites["switch"].clone().set_position(6, 6),
            sprites["door"].clone().set_position(3, 4),
            sprites["target"].clone().set_position(7, 4),
        ]
        + [sprites["wall"].clone().set_position(x, 4) for x in range(8) if x not in (3, 4)],
        (8, 8),
        5,
        4,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Fs03(ARCBaseGame):
    """Activate switches in row order (first plate in level list, then second, ...); then door opens."""

    def __init__(self) -> None:
        self._ui = Fs03UI(0, 2)
        super().__init__(
            "fs03",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._switches = self.current_level.get_sprites_by_tag("switch")
        self._order = [(s.x, s.y) for s in self._switches]
        self._next_i = 0
        self._door = self.current_level.get_sprites_by_tag("door")
        self._targets = self.current_level.get_sprites_by_tag("target")
        self._ui.update(0, len(self._order))

    def _open_door(self) -> None:
        if self._door:
            for d in list(self._door):
                self.current_level.remove_sprite(d)
            self._door = []
        self._ui.update(len(self._order), len(self._order))

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

        if sprite and "door" in sprite.tags:
            self.complete_action()
            return

        if not sprite or not sprite.is_collidable:
            self._player.set_position(new_x, new_y)

        pos = (self._player.x, self._player.y)
        if self._next_i < len(self._order) and pos == self._order[self._next_i]:
            self._next_i += 1
            self._ui.update(self._next_i, len(self._order))
            if self._next_i >= len(self._order):
                self._open_door()

        for t in self._targets:
            if self._player.x == t.x and self._player.y == t.y:
                if len(self._door) == 0:
                    self.next_level()
                break

        self.complete_action()
