"""After each move, gravity pulls one step down (if not blocked)."""

from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Gr01UI(RenderableUserDisplay):
    def __init__(self, _: int) -> None:
        pass

    def update(self, _: int) -> None:
        pass

    def render_interface(self, frame):
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
}


def mk(sl, grid_size, difficulty):
    return Level(sprites=sl, grid_size=grid_size, data={"difficulty": difficulty})


levels = [
    mk(
        [
            sprites["player"].clone().set_position(2, 0),
            sprites["target"].clone().set_position(2, 6),
        ],
        (8, 8),
        1,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["target"].clone().set_position(6, 6),
            sprites["wall"].clone().set_position(3, 3),
        ],
        (8, 8),
        2,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["target"].clone().set_position(7, 7),
        ]
        + [sprites["wall"].clone().set_position(4, y) for y in range(8) if y != 5],
        (8, 8),
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(3, 0),
            sprites["target"].clone().set_position(3, 7),
        ],
        (8, 8),
        4,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 2),
            sprites["target"].clone().set_position(7, 5),
        ],
        (8, 8),
        5,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Gr01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Gr01UI(0)
        super().__init__(
            "gr01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._targets = self.current_level.get_sprites_by_tag("target")

    def _blocked(self, x: int, y: int) -> bool:
        sp = self.current_level.get_sprite_at(x, y, ignore_collidable=True)
        return sp is not None and "wall" in sp.tags

    def _gravity(self) -> None:
        grid_w, grid_h = self.current_level.grid_size
        nx, ny = self._player.x, self._player.y + 1
        if 0 <= nx < grid_w and 0 <= ny < grid_h and not self._blocked(nx, ny):
            self._player.set_position(nx, ny)

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

        if not sprite or not sprite.is_collidable:
            self._player.set_position(new_x, new_y)

        self._gravity()

        for t in self._targets:
            if self._player.x == t.x and self._player.y == t.y:
                self.next_level()
                break

        self.complete_action()
