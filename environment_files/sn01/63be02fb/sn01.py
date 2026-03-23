"""Snake: eat all yellow food; grow; avoid walls and biting yourself."""

from collections import deque

from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Sn01UI(RenderableUserDisplay):
    def __init__(self, left: int) -> None:
        self._left = left

    def update(self, left: int) -> None:
        self._left = left

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, _w = frame.shape
        for i in range(min(self._left, 12)):
            frame[h - 2, 1 + i] = 11
        return frame


sprites = {
    "player": Sprite(
        pixels=[[9]],
        name="player",
        visible=True,
        collidable=True,
        tags=["player"],
    ),
    "food": Sprite(
        pixels=[[11]],
        name="food",
        visible=True,
        collidable=False,
        tags=["food"],
    ),
    "wall": Sprite(
        pixels=[[3]],
        name="wall",
        visible=True,
        collidable=True,
        tags=["wall"],
    ),
    "snake_body": Sprite(
        pixels=[[10]],
        name="snake_body",
        visible=True,
        collidable=False,
        tags=["snake_body"],
    ),
}


def mk(sl: list, d: int) -> Level:
    return Level(sprites=sl, grid_size=(12, 12), data={"difficulty": d})


levels = [
    mk(
        [
            sprites["player"].clone().set_position(5, 5),
            sprites["food"].clone().set_position(8, 5),
            sprites["food"].clone().set_position(3, 5),
        ],
        1,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["food"].clone().set_position(10, 1),
            sprites["food"].clone().set_position(10, 10),
            sprites["food"].clone().set_position(1, 10),
        ],
        2,
    ),
    mk(
        [
            sprites["player"].clone().set_position(5, 6),
            sprites["food"].clone().set_position(2, 6),
            sprites["food"].clone().set_position(9, 6),
        ]
        + [sprites["wall"].clone().set_position(5, y) for y in (3, 4, 8, 9)],
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(6, 6),
            sprites["food"].clone().set_position(3, 3),
            sprites["food"].clone().set_position(8, 3),
            sprites["food"].clone().set_position(3, 8),
            sprites["food"].clone().set_position(8, 8),
        ],
        4,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 6),
            sprites["food"].clone().set_position(3, 6),
            sprites["food"].clone().set_position(5, 6),
            sprites["food"].clone().set_position(7, 6),
            sprites["food"].clone().set_position(9, 6),
        ],
        5,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Sn01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Sn01UI(0)
        super().__init__(
            "sn01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._foods = list(self.current_level.get_sprites_by_tag("food"))
        x, y = self._player.x, self._player.y
        self._body: deque[tuple[int, int]] = deque([(x, y)])
        self._sync_body_sprites()
        self._sync_ui()

    def _sync_ui(self) -> None:
        self._ui.update(len(self._foods))

    def _clear_body_sprites(self) -> None:
        for s in list(self.current_level.get_sprites_by_tag("snake_body")):
            self.current_level.remove_sprite(s)

    def _sync_body_sprites(self) -> None:
        self._clear_body_sprites()
        for bx, by in list(self._body)[:-1]:
            self.current_level.add_sprite(
                sprites["snake_body"].clone().set_position(bx, by),
            )

    def _wall_at(self, x: int, y: int) -> bool:
        sp = self.current_level.get_sprite_at(x, y, ignore_collidable=True)
        return bool(sp and "wall" in sp.tags)

    def step(self) -> None:
        dx = dy = 0
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

        hx, hy = self._body[-1]
        nx, ny = hx + dx, hy + dy
        gw, gh = self.current_level.grid_size
        if not (0 <= nx < gw and 0 <= ny < gh) or self._wall_at(nx, ny):
            self.complete_action()
            return

        tail = self._body[0]
        ate = False
        food_here = None
        for f in self._foods:
            if f.x == nx and f.y == ny:
                food_here = f
                ate = True
                break

        if (nx, ny) in self._body and (nx, ny) != tail:
            self.lose()
            self.complete_action()
            return

        self._body.append((nx, ny))
        if not ate:
            self._body.popleft()
        else:
            assert food_here is not None
            self.current_level.remove_sprite(food_here)
            self._foods.remove(food_here)

        tx, ty = self._body[-1]
        self._player.set_position(tx, ty)
        self._sync_body_sprites()
        self._sync_ui()

        if not self._foods:
            self.next_level()
            self.complete_action()
            return

        self.complete_action()
