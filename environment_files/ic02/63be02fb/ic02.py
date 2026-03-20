from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Ic02UI(RenderableUserDisplay):
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


def make_level(sl, grid_size, difficulty):
    return Level(sprites=sl, grid_size=grid_size, data={"difficulty": difficulty})


levels = [
    make_level(
        [
            sprites["player"].clone().set_position(1, 6),
            sprites["target"].clone().set_position(1, 1),
            sprites["wall"].clone().set_position(1, 0),
        ],
        (8, 8),
        1,
    ),
    # Wall one cell past the goal on the slide axis stops the torus orbit on that line.
    make_level(
        [
            sprites["player"].clone().set_position(2, 6),
            sprites["target"].clone().set_position(2, 2),
            sprites["wall"].clone().set_position(2, 1),
        ],
        (8, 8),
        2,
    ),
    make_level(
        [
            sprites["player"].clone().set_position(6, 2),
            sprites["target"].clone().set_position(6, 6),
            sprites["wall"].clone().set_position(6, 7),
        ],
        (8, 8),
        3,
    ),
    make_level(
        [
            sprites["player"].clone().set_position(1, 3),
            sprites["target"].clone().set_position(5, 3),
            sprites["wall"].clone().set_position(6, 3),
        ],
        (8, 8),
        4,
    ),
    make_level(
        [
            sprites["player"].clone().set_position(6, 4),
            sprites["target"].clone().set_position(2, 4),
            sprites["wall"].clone().set_position(1, 4),
        ],
        (8, 8),
        5,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Ic02(ARCBaseGame):
    """Ice slide on a torus: leaving an edge wraps to the opposite side."""

    def __init__(self) -> None:
        self._ui = Ic02UI(0)
        super().__init__(
            "ic02",
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
        sprite = self.current_level.get_sprite_at(x, y, ignore_collidable=True)
        if not sprite:
            return False
        return "wall" in sprite.tags or "hazard" in sprite.tags

    def _wrap_step(self, x: int, y: int, dx: int, dy: int, gw: int, gh: int) -> tuple[int, int]:
        nx = x + dx
        ny = y + dy
        if nx < 0:
            nx = gw - 1
        elif nx >= gw:
            nx = 0
        if ny < 0:
            ny = gh - 1
        elif ny >= gh:
            ny = 0
        return nx, ny

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
        for _ in range(grid_w * grid_h):
            nx, ny = self._wrap_step(px, py, dx, dy, grid_w, grid_h)
            if self._blocked(nx, ny):
                break
            px, py = nx, ny

        self._player.set_position(px, py)

        for t in self._targets:
            if self._player.x == t.x and self._player.y == t.y:
                self.next_level()
                break

        self.complete_action()
