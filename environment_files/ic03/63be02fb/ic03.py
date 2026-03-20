from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Ic03UI(RenderableUserDisplay):
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
    "hazard": Sprite(
        pixels=[[8]],
        name="hazard",
        visible=True,
        collidable=True,
        tags=["hazard"],
    ),
}


def make_level(sl, grid_size, difficulty, slide_cap):
    return Level(
        sprites=sl,
        grid_size=grid_size,
        data={"difficulty": difficulty, "slide_cap": slide_cap},
    )


levels = [
    make_level(
        [
            sprites["player"].clone().set_position(1, 6),
            sprites["target"].clone().set_position(1, 1),
            sprites["wall"].clone().set_position(1, 0),
        ],
        (8, 8),
        1,
        3,
    ),
    make_level(
        [
            sprites["player"].clone().set_position(1, 6),
            sprites["target"].clone().set_position(6, 1),
            sprites["wall"].clone().set_position(1, 3),
            sprites["wall"].clone().set_position(2, 3),
            sprites["wall"].clone().set_position(3, 3),
            sprites["wall"].clone().set_position(4, 3),
            sprites["wall"].clone().set_position(5, 3),
            sprites["wall"].clone().set_position(6, 3),
        ],
        (8, 8),
        2,
        2,
    ),
    make_level(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["target"].clone().set_position(7, 7),
        ]
        + [sprites["wall"].clone().set_position(x, 4) for x in range(8) if x != 3],
        (8, 8),
        3,
        4,
    ),
    make_level(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["target"].clone().set_position(8, 6),
            sprites["hazard"].clone().set_position(5, 4),
        ]
        + [sprites["wall"].clone().set_position(x, y) for x, y in [(3, 2), (4, 2)]],
        (10, 8),
        4,
        3,
    ),
    make_level(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["target"].clone().set_position(7, 7),
        ],
        (8, 8),
        5,
        1,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Ic03(ARCBaseGame):
    """Each move slides at most K cells in that direction (K per level), unless blocked sooner."""

    def __init__(self) -> None:
        self._ui = Ic03UI(0)
        super().__init__(
            "ic03",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._targets = self.current_level.get_sprites_by_tag("target")
        self._cap = int(level.get_data("slide_cap") or 3)

    def _blocked(self, x: int, y: int) -> bool:
        sprite = self.current_level.get_sprite_at(x, y, ignore_collidable=True)
        if not sprite:
            return False
        return "wall" in sprite.tags or "hazard" in sprite.tags

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

        grid_w, grid_h = self.current_level.grid_size
        px, py = self._player.x, self._player.y
        steps = 0
        while steps < self._cap:
            nx, ny = px + dx, py + dy
            if not (0 <= nx < grid_w and 0 <= ny < grid_h):
                break
            if self._blocked(nx, ny):
                break
            px, py = nx, ny
            steps += 1

        self._player.set_position(px, py)

        for t in self._targets:
            if self._player.x == t.x and self._player.y == t.y:
                self.next_level()
                break

        self.complete_action()
