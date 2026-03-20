from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Ul01UI(RenderableUserDisplay):
    def __init__(self, has_key: bool) -> None:
        self._has_key = has_key

    def update(self, has_key: bool) -> None:
        self._has_key = has_key

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        key_color = 11 if self._has_key else 5
        # Larger 4x4 indicator in bottom-right
        for dy in range(4):
            for dx in range(4):
                frame[h - 4 + dy, w - 4 + dx] = key_color
        return frame


sprites = {
    "player": Sprite(
        pixels=[[9]],
        name="player",
        visible=True,
        collidable=True,
        tags=["player"],
    ),
    "key": Sprite(
        pixels=[[11]],
        name="key",
        visible=True,
        collidable=False,
        tags=["key"],
    ),
    "door": Sprite(
        pixels=[[3]],
        name="door",
        visible=True,
        collidable=True,
        tags=["door"],
    ),
}

levels = [
    Level(
        sprites=[
            sprites["player"].clone().set_position(1, 1),
            sprites["key"].clone().set_position(3, 3),
            sprites["door"].clone().set_position(6, 1),
        ],
        grid_size=(8, 8),
        data={"difficulty": 1},
    ),
    Level(
        sprites=[
            sprites["player"].clone().set_position(1, 1),
            sprites["key"].clone().set_position(5, 5),
            sprites["door"].clone().set_position(7, 3),
        ],
        grid_size=(8, 8),
        data={"difficulty": 2},
    ),
    Level(
        sprites=[
            sprites["player"].clone().set_position(1, 1),
            sprites["key"].clone().set_position(4, 4),
            sprites["door"].clone().set_position(7, 7),
        ],
        grid_size=(8, 8),
        data={"difficulty": 3},
    ),
    Level(
        sprites=[
            sprites["player"].clone().set_position(0, 0),
            sprites["key"].clone().set_position(3, 3),
            sprites["door"].clone().set_position(7, 0),
        ],
        grid_size=(8, 8),
        data={"difficulty": 4},
    ),
    Level(
        sprites=[
            sprites["player"].clone().set_position(0, 7),
            sprites["key"].clone().set_position(7, 0),
            sprites["door"].clone().set_position(7, 7),
        ],
        grid_size=(8, 8),
        data={"difficulty": 5},
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Ul01(ARCBaseGame):
    """Pick up key to unlock door and advance to next level."""

    def __init__(self) -> None:
        self._ui = Ul01UI(False)
        super().__init__(
            "ul01",
            levels,
            Camera(0, 0, 8, 8, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._key = self.current_level.get_sprites_by_tag("key")
        self._door = self.current_level.get_sprites_by_tag("door")
        self._has_key = False
        self._ui.update(self._has_key)

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

            if sprite and "key" in sprite.tags:
                self.current_level.remove_sprite(sprite)
                self._key.remove(sprite)
                self._has_key = True
                self._player.set_position(new_x, new_y)
                self._ui.update(self._has_key)
            elif sprite and "door" in sprite.tags:
                if self._has_key:
                    self.current_level.remove_sprite(sprite)
                    self._door.remove(sprite)
                    self._player.set_position(new_x, new_y)
                # else: door blocks player
            elif not sprite or not sprite.is_collidable:
                self._player.set_position(new_x, new_y)

        if len(self._door) == 0 and len(self._key) == 0:
            self.next_level()

        self.complete_action()
