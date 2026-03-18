from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Ez01UI(RenderableUserDisplay):
    def __init__(self, targets_remaining: int) -> None:
        self._targets = targets_remaining

    def update(self, targets_remaining: int) -> None:
        self._targets = targets_remaining

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
        pixels=[[4]],
        name="target",
        visible=True,
        collidable=False,
        tags=["target"],
    ),
}

levels = [
    Level(
        sprites=[
            sprites["player"].clone().set_position(3, 6),
            sprites["target"].clone().set_position(3, 4),
        ],
        grid_size=(8, 8),
        data={"difficulty": 1},
    ),
    Level(
        sprites=[
            sprites["player"].clone().set_position(4, 6),
            sprites["target"].clone().set_position(4, 2),
        ],
        grid_size=(8, 8),
        data={"difficulty": 2},
    ),
    Level(
        sprites=[
            sprites["player"].clone().set_position(3, 7),
            sprites["target"].clone().set_position(3, 1),
        ],
        grid_size=(8, 8),
        data={"difficulty": 3},
    ),
    Level(
        sprites=[
            sprites["player"].clone().set_position(5, 7),
            sprites["target"].clone().set_position(5, 1),
        ],
        grid_size=(8, 8),
        data={"difficulty": 4},
    ),
    Level(
        sprites=[
            sprites["player"].clone().set_position(3, 7),
            sprites["target"].clone().set_position(3, 0),
        ],
        grid_size=(8, 8),
        data={"difficulty": 5},
    ),
]

BACKGROUND_COLOR = 0
PADDING_COLOR = 4


class Ez01(ARCBaseGame):
    """Go UP to win."""

    def __init__(self) -> None:
        self._ui = Ez01UI(0)
        super().__init__(
            "ez01",
            levels,
            Camera(0, 0, 8, 8, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._targets = self.current_level.get_sprites_by_tag("target")
        self._ui.update(len(self._targets))

    def step(self) -> None:
        dx = 0
        dy = 0
        moved = False

        if self.action.id.value == 1:
            dy = -1
            moved = True
        elif self.action.id.value == 2:
            dy = 1
            moved = True
        elif self.action.id.value == 3:
            dx = -1
            moved = True
        elif self.action.id.value == 4:
            dx = 1
            moved = True

        if not moved:
            self.complete_action()
            return

        new_x = self._player.x + dx
        new_y = self._player.y + dy

        grid_w, grid_h = self.current_level.grid_size
        if 0 <= new_x < grid_w and 0 <= new_y < grid_h:
            sprite = self.current_level.get_sprite_at(
                new_x, new_y, ignore_collidable=True
            )

            if sprite and "target" in sprite.tags:
                self.current_level.remove_sprite(sprite)
                self._targets.remove(sprite)
                self._player.set_position(new_x, new_y)
                self._ui.update(len(self._targets))
            elif not sprite or not sprite.is_collidable:
                self._player.set_position(new_x, new_y)

        if len(self._targets) == 0:
            self.next_level()

        self.complete_action()
