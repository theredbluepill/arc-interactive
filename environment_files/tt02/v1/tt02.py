from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Tt02UI(RenderableUserDisplay):
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
    "wall": Sprite(
        pixels=[[5]],
        name="wall",
        visible=True,
        collidable=True,
        tags=["wall"],
    ),
    "hazard": Sprite(
        pixels=[[2]],
        name="hazard",
        visible=True,
        collidable=True,
        tags=["hazard"],
    ),
    "coin": Sprite(
        pixels=[[7]],
        name="coin",
        visible=True,
        collidable=False,
        tags=["coin"],
    ),
}

levels = [
    Level(
        sprites=[
            sprites["player"].clone().set_position(1, 1),
            sprites["target"].clone().set_position(3, 3),
            sprites["target"].clone().set_position(5, 2),
            sprites["target"].clone().set_position(2, 5),
            sprites["coin"].clone().set_position(4, 1),
            sprites["coin"].clone().set_position(1, 4),
            sprites["wall"].clone().set_position(2, 2),
            sprites["wall"].clone().set_position(4, 4),
            sprites["wall"].clone().set_position(6, 1),
            sprites["hazard"].clone().set_position(5, 5),
        ],
        grid_size=(8, 8),
        data={"difficulty": 1},
    ),
    Level(
        sprites=[
            sprites["player"].clone().set_position(2, 2),
            sprites["target"].clone().set_position(6, 6),
            sprites["target"].clone().set_position(8, 3),
            sprites["target"].clone().set_position(4, 10),
            sprites["target"].clone().set_position(12, 8),
            sprites["coin"].clone().set_position(3, 5),
            sprites["coin"].clone().set_position(7, 2),
            sprites["coin"].clone().set_position(10, 5),
            sprites["wall"].clone().set_position(3, 3),
            sprites["wall"].clone().set_position(5, 5),
            sprites["wall"].clone().set_position(7, 7),
            sprites["wall"].clone().set_position(10, 4),
            sprites["wall"].clone().set_position(8, 12),
            sprites["hazard"].clone().set_position(6, 4),
            sprites["hazard"].clone().set_position(10, 10),
        ],
        grid_size=(16, 16),
        data={"difficulty": 2},
    ),
    Level(
        sprites=[
            sprites["player"].clone().set_position(5, 5),
            sprites["target"].clone().set_position(10, 10),
            sprites["target"].clone().set_position(15, 5),
            sprites["target"].clone().set_position(8, 18),
            sprites["target"].clone().set_position(20, 12),
            sprites["target"].clone().set_position(3, 20),
            sprites["coin"].clone().set_position(6, 3),
            sprites["coin"].clone().set_position(12, 15),
            sprites["coin"].clone().set_position(18, 8),
            sprites["coin"].clone().set_position(5, 20),
            sprites["wall"].clone().set_position(6, 6),
            sprites["wall"].clone().set_position(12, 8),
            sprites["wall"].clone().set_position(18, 15),
            sprites["wall"].clone().set_position(10, 20),
            sprites["wall"].clone().set_position(5, 12),
            sprites["wall"].clone().set_position(15, 3),
            sprites["wall"].clone().set_position(20, 20),
            sprites["hazard"].clone().set_position(8, 8),
            sprites["hazard"].clone().set_position(14, 14),
            sprites["hazard"].clone().set_position(18, 6),
        ],
        grid_size=(24, 24),
        data={"difficulty": 3},
    ),
]

BACKGROUND_COLOR = 0
PADDING_COLOR = 4


class Tt02(ARCBaseGame):
    """Collection game with targets and coins. Player collects targets."""

    def __init__(self) -> None:
        self._ui = Tt02UI(0)
        super().__init__(
            "tt02",
            levels,
            Camera(0, 0, 24, 24, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._targets = self.current_level.get_sprites_by_tag("target")
        self._ui.update(len(self._targets))

    def step(self) -> None:
        lgr = 0
        kyr = 0
        moved = False

        if self.action.id.value == 1:
            kyr = -1
            moved = True
        elif self.action.id.value == 2:
            kyr = 1
            moved = True
        elif self.action.id.value == 3:
            lgr = -1
            moved = True
        elif self.action.id.value == 4:
            lgr = 1
            moved = True

        if not moved:
            self.complete_action()
            return

        new_x = self._player.x + lgr
        new_y = self._player.y + kyr

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
