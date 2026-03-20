from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Tp02UI(RenderableUserDisplay):
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
    "portal": Sprite(
        pixels=[[7]],
        name="portal",
        visible=True,
        collidable=False,
        tags=["portal"],
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


def lvl(sl, grid_size, difficulty, directed_pairs):
    return Level(
        sprites=sl,
        grid_size=grid_size,
        data={"difficulty": difficulty, "directed_pairs": directed_pairs},
    )


levels = [
    lvl(
        [
            sprites["player"].clone().set_position(0, 3),
            sprites["portal"].clone().set_position(2, 3),
            sprites["portal"].clone().set_position(6, 3),
            sprites["target"].clone().set_position(7, 3),
        ],
        (8, 8),
        1,
        [[(2, 3), (6, 3)]],
    ),
    lvl(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["portal"].clone().set_position(1, 5),
            sprites["portal"].clone().set_position(5, 5),
            sprites["target"].clone().set_position(6, 1),
        ]
        + [sprites["wall"].clone().set_position(3, y) for y in range(6)],
        (8, 8),
        2,
        [[(1, 5), (5, 5)]],
    ),
    lvl(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["portal"].clone().set_position(2, 0),
            sprites["portal"].clone().set_position(6, 4),
            sprites["portal"].clone().set_position(2, 6),
            sprites["portal"].clone().set_position(6, 6),
            sprites["target"].clone().set_position(7, 7),
        ]
        + [sprites["wall"].clone().set_position(4, y) for y in range(8) if y != 3],
        (8, 8),
        3,
        [[(2, 0), (6, 4)], [(2, 6), (6, 6)]],
    ),
    lvl(
        [
            sprites["player"].clone().set_position(0, 4),
            sprites["portal"].clone().set_position(2, 4),
            sprites["portal"].clone().set_position(8, 4),
            sprites["target"].clone().set_position(9, 0),
        ]
        + [sprites["wall"].clone().set_position(5, y) for y in range(8) if y != 4],
        (10, 8),
        4,
        [[(2, 4), (8, 4)]],
    ),
    lvl(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["portal"].clone().set_position(3, 1),
            sprites["portal"].clone().set_position(5, 5),
            sprites["portal"].clone().set_position(1, 5),
            sprites["portal"].clone().set_position(5, 1),
            sprites["target"].clone().set_position(6, 6),
        ]
        + [
            sprites["wall"].clone().set_position(x, y)
            for x, y in [(2, 2), (4, 2), (2, 4), (4, 4)]
        ],
        (8, 8),
        5,
        [[(3, 1), (5, 5)], [(1, 5), (5, 1)]],
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Tp02(ARCBaseGame):
    """Directed portals: only from-cell warps to to-cell; stepping the exit tile does not warp back."""

    def __init__(self) -> None:
        self._ui = Tp02UI(0)
        super().__init__(
            "tp02",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._targets = self.current_level.get_sprites_by_tag("target")
        pairs = level.get_data("directed_pairs") or []
        self._warp_from: dict[tuple[int, int], tuple[int, int]] = {}
        for a, b in pairs:
            self._warp_from[tuple(a)] = tuple(b)

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

        pos = (self._player.x, self._player.y)
        if pos in self._warp_from:
            dest = self._warp_from[pos]
            self._player.set_position(dest[0], dest[1])

        for t in self._targets:
            if self._player.x == t.x and self._player.y == t.y:
                self.next_level()
                break

        self.complete_action()
