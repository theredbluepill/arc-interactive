"""Arrow floor: after you land on an arrow cell, your next move uses that facing (overrides input)."""

from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Nw01UI(RenderableUserDisplay):
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
    "arrow": Sprite(
        pixels=[[6]],
        name="arrow",
        visible=True,
        collidable=False,
        tags=["arrow"],
    ),
}


def mk(sl, grid_size, difficulty, arrows):
    return Level(
        sprites=sl,
        grid_size=grid_size,
        data={"difficulty": difficulty, "arrows": arrows},
    )


levels = [
    mk(
        [
            sprites["player"].clone().set_position(0, 3),
            sprites["arrow"].clone().set_position(2, 3),
            sprites["target"].clone().set_position(5, 1),
        ],
        (8, 8),
        1,
        [[(2, 3), [0, -1]]],
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["arrow"].clone().set_position(3, 1),
            sprites["target"].clone().set_position(6, 6),
        ],
        (8, 8),
        2,
        [[(3, 1), [1, 0]]],
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["arrow"].clone().set_position(2, 2),
            sprites["arrow"].clone().set_position(5, 7),
            sprites["target"].clone().set_position(7, 0),
        ],
        (8, 8),
        3,
        [[(2, 2), [0, 1]], [(5, 7), [-1, 0]]],
    ),
    mk(
        [
            sprites["player"].clone().set_position(2, 2),
            sprites["arrow"].clone().set_position(4, 2),
            sprites["target"].clone().set_position(1, 6),
        ],
        (8, 8),
        4,
        [[(4, 2), [0, 1]]],
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["arrow"].clone().set_position(1, 0),
            sprites["target"].clone().set_position(7, 7),
        ],
        (8, 8),
        5,
        [[(1, 0), [1, 0]]],
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Nw01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Nw01UI(0)
        super().__init__(
            "nw01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._targets = self.current_level.get_sprites_by_tag("target")
        self._arrow_map: dict[tuple[int, int], tuple[int, int]] = {}
        for entry in level.get_data("arrows") or []:
            pos, vec = entry
            self._arrow_map[tuple(pos)] = tuple(vec)
        self._forced: tuple[int, int] | None = None

    def step(self) -> None:
        dx = 0
        dy = 0
        if self._forced is not None:
            dx, dy = self._forced
            self._forced = None
        else:
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

        pos = (self._player.x, self._player.y)
        if pos in self._arrow_map:
            self._forced = self._arrow_map[pos]

        for t in self._targets:
            if self._player.x == t.x and self._player.y == t.y:
                self.next_level()
                break

        self.complete_action()
