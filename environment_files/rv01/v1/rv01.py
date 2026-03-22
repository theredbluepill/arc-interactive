"""Rotating vector sparks: red hazards all shift one cell in a shared direction that cycles N→E→S→W each step.

Spec:
- Tags: ``player``, ``target`` (collectible), ``wall``, ``hazard`` + ``spark``.
- ``level.data``: ``difficulty`` only (movement is global).
- Actions: 1–4 move; after each action, every spark moves in the current wind direction, then wind rotates.
- Win: all targets collected. Lose: spark shares a cell with the player after any sub-update.
- Camera: 16×16; grids 8×8, 12×12, 16×16.
"""

from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Rv01UI(RenderableUserDisplay):
    def __init__(self, n_levels: int) -> None:
        self._remaining = 0
        self._wind = 0
        self._n_levels = n_levels
        self._li = 0

    def update(
        self,
        remaining: int,
        wind: int,
        level_index: int | None = None,
    ) -> None:
        self._remaining = remaining
        self._wind = wind
        if level_index is not None:
            self._li = level_index

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for i in range(min(self._n_levels, 14)):
            cx = 1 + i * 2
            if cx >= w:
                break
            c = 14 if i < self._li else (11 if i == self._li else 3)
            frame[0, cx] = c
        for i in range(4):
            frame[h - 2, 2 + i] = 11 if (self._wind % 4) == i else 2
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
    "wall": Sprite(
        pixels=[[3]],
        name="wall",
        visible=True,
        collidable=True,
        tags=["wall"],
    ),
    "spark": Sprite(
        pixels=[[8]],
        name="spark",
        visible=True,
        collidable=True,
        tags=["hazard", "spark"],
    ),
}


def mk(
    grid: tuple[int, int],
    parts: list[Sprite],
    diff: int,
) -> Level:
    return Level(sprites=parts, grid_size=grid, data={"difficulty": diff})


levels = [
    mk(
        (8, 8),
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["target"].clone().set_position(6, 6),
            sprites["target"].clone().set_position(2, 6),
            sprites["spark"].clone().set_position(4, 3),
            sprites["wall"].clone().set_position(4, 4),
        ],
        1,
    ),
    mk(
        (12, 12),
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["target"].clone().set_position(9, 9),
            sprites["target"].clone().set_position(5, 10),
            sprites["spark"].clone().set_position(6, 5),
            sprites["spark"].clone().set_position(8, 5),
        ]
        + [sprites["wall"].clone().set_position(6, y) for y in range(12) if y not in (4, 5, 6, 7)],
        2,
    ),
    mk(
        (16, 16),
        [
            sprites["player"].clone().set_position(2, 2),
            sprites["target"].clone().set_position(13, 13),
            sprites["target"].clone().set_position(8, 8),
            sprites["target"].clone().set_position(3, 12),
            sprites["spark"].clone().set_position(10, 6),
            sprites["spark"].clone().set_position(6, 10),
            sprites["spark"].clone().set_position(12, 12),
        ],
        3,
    ),
    mk(
        (12, 12),
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["target"].clone().set_position(10, 10),
            sprites["target"].clone().set_position(10, 1),
            sprites["spark"].clone().set_position(5, 5),
            sprites["wall"].clone().set_position(5, 4),
            sprites["wall"].clone().set_position(5, 6),
        ],
        4,
    ),
    mk(
        (16, 16),
        [
            sprites["player"].clone().set_position(1, 14),
            sprites["target"].clone().set_position(14, 1),
            sprites["target"].clone().set_position(14, 2),
            sprites["target"].clone().set_position(1, 1),
            sprites["spark"].clone().set_position(8, 8),
            sprites["spark"].clone().set_position(9, 8),
            sprites["spark"].clone().set_position(8, 9),
        ]
        + [sprites["wall"].clone().set_position(8, y) for y in range(4)]
        + [sprites["wall"].clone().set_position(8, y) for y in range(12, 16)],
        5,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Rv01(ARCBaseGame):
    _DIRS = ((0, -1), (1, 0), (0, 1), (-1, 0))

    def __init__(self) -> None:
        self._ui = Rv01UI(len(levels))
        super().__init__(
            "rv01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._targets = self.current_level.get_sprites_by_tag("target")
        self._sparks = [s for s in self.current_level.get_sprites_by_tag("spark")]
        self._wind = 0
        self._ui.update(len(self._targets), self._wind, self.level_index)

    def _advance_sparks(self) -> None:
        grid_w, grid_h = self.current_level.grid_size
        dx, dy = self._DIRS[self._wind % 4]
        for sp in self._sparks:
            nx, ny = sp.x + dx, sp.y + dy
            if not (0 <= nx < grid_w and 0 <= ny < grid_h):
                continue
            cell = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
            if cell and "wall" in cell.tags:
                continue
            if cell and "spark" in cell.tags:
                continue
            sp.set_position(nx, ny)
        self._wind += 1

    def _player_on_spark(self) -> bool:
        px, py = self._player.x, self._player.y
        hit = self.current_level.get_sprite_at(px, py, ignore_collidable=True)
        return hit is not None and "spark" in hit.tags

    def step(self) -> None:
        dx = dy = 0
        moved = False
        if self.action.id.value == 1:
            dy, moved = -1, True
        elif self.action.id.value == 2:
            dy, moved = 1, True
        elif self.action.id.value == 3:
            dx, moved = -1, True
        elif self.action.id.value == 4:
            dx, moved = 1, True

        if not moved:
            self.complete_action()
            return

        new_x = self._player.x + dx
        new_y = self._player.y + dy
        grid_w, grid_h = self.current_level.grid_size
        if 0 <= new_x < grid_w and 0 <= new_y < grid_h:
            sprite = self.current_level.get_sprite_at(new_x, new_y, ignore_collidable=True)
            if sprite and "target" in sprite.tags:
                self.current_level.remove_sprite(sprite)
                self._targets.remove(sprite)
                self._player.set_position(new_x, new_y)
            elif not sprite or not sprite.is_collidable:
                self._player.set_position(new_x, new_y)
            elif sprite and "spark" in sprite.tags:
                self.complete_action()
                return

        self._advance_sparks()
        self._ui.update(len(self._targets), self._wind, self.level_index)

        if self._player_on_spark():
            self.lose()
            self.complete_action()
            return

        if len(self._targets) == 0:
            self.next_level()

        self.complete_action()
