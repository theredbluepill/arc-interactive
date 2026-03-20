from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Fs01UI(RenderableUserDisplay):
    def __init__(self, activated: int, total: int) -> None:
        self._activated = activated
        self._total = total

    def update(self, activated: int, total: int) -> None:
        self._activated = activated
        self._total = total

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        done = self._activated >= self._total and self._total > 0
        color = 14 if done else 11
        n = min(self._activated, 4)
        for i in range(4):
            c = color if i < n else 5
            for dy in range(2):
                for dx in range(2):
                    frame[h - 4 + dy, w - 8 + i * 2 + dx] = c
        return frame


sprites = {
    "player": Sprite(
        pixels=[[9]],
        name="player",
        visible=True,
        collidable=True,
        tags=["player"],
    ),
    "switch": Sprite(
        pixels=[[11]],
        name="switch",
        visible=True,
        collidable=False,
        tags=["switch"],
    ),
    "door": Sprite(
        pixels=[[3]],
        name="door",
        visible=True,
        collidable=True,
        tags=["door"],
    ),
    "target": Sprite(
        pixels=[[14]],
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


def make_level(sprites_list, grid_size, difficulty):
    return Level(
        sprites=sprites_list,
        grid_size=grid_size,
        data={"difficulty": difficulty},
    )


levels = [
    make_level(
        [
            sprites["player"].clone().set_position(0, 3),
            sprites["switch"].clone().set_position(2, 3),
            sprites["switch"].clone().set_position(6, 3),
            sprites["door"].clone().set_position(4, 3),
            sprites["target"].clone().set_position(7, 3),
        ],
        (8, 8),
        1,
    ),
    make_level(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["switch"].clone().set_position(1, 5),
            sprites["switch"].clone().set_position(5, 1),
            sprites["door"].clone().set_position(3, 3),
            sprites["target"].clone().set_position(6, 6),
        ]
        + [sprites["wall"].clone().set_position(x, 2) for x in range(8) if x != 3],
        (8, 8),
        2,
    ),
    make_level(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["switch"].clone().set_position(2, 0),
            sprites["switch"].clone().set_position(0, 2),
            sprites["switch"].clone().set_position(2, 2),
            sprites["door"].clone().set_position(4, 1),
            sprites["target"].clone().set_position(7, 1),
        ]
        + [sprites["wall"].clone().set_position(3, y) for y in range(8) if y != 1],
        (8, 8),
        3,
    ),
    make_level(
        [
            sprites["player"].clone().set_position(1, 4),
            sprites["switch"].clone().set_position(2, 2),
            sprites["switch"].clone().set_position(2, 6),
            sprites["door"].clone().set_position(5, 4),
            sprites["target"].clone().set_position(8, 4),
        ]
        + [sprites["wall"].clone().set_position(4, y) for y in range(8) if y != 4],
        (10, 8),
        4,
    ),
    make_level(
        [
            sprites["player"].clone().set_position(0, 7),
            sprites["switch"].clone().set_position(1, 1),
            sprites["switch"].clone().set_position(6, 1),
            sprites["switch"].clone().set_position(1, 6),
            sprites["switch"].clone().set_position(6, 6),
            sprites["door"].clone().set_position(3, 4),
            sprites["target"].clone().set_position(7, 4),
        ]
        + [sprites["wall"].clone().set_position(x, 4) for x in range(8) if x != 3 and x != 4],
        (8, 8),
        5,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Fs01(ARCBaseGame):
    """Step on every yellow pressure plate (order-free) to open the door, then reach the green goal."""

    def __init__(self) -> None:
        self._ui = Fs01UI(0, 0)
        super().__init__(
            "fs01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._switches = self.current_level.get_sprites_by_tag("switch")
        self._switch_positions = frozenset((s.x, s.y) for s in self._switches)
        self._activated: set[tuple[int, int]] = set()
        self._door = self.current_level.get_sprites_by_tag("door")
        self._targets = self.current_level.get_sprites_by_tag("target")
        self._open_door_if_ready()

    def _open_door_if_ready(self) -> None:
        if len(self._activated) >= len(self._switch_positions) and self._door:
            for d in list(self._door):
                self.current_level.remove_sprite(d)
            self._door = []
        self._ui.update(len(self._activated), len(self._switch_positions))

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

        if sprite and "door" in sprite.tags:
            self.complete_action()
            return

        if not sprite or not sprite.is_collidable:
            self._player.set_position(new_x, new_y)

        pos = (self._player.x, self._player.y)
        if pos in self._switch_positions:
            self._activated.add(pos)
            self._open_door_if_ready()

        for t in self._targets:
            if self._player.x == t.x and self._player.y == t.y:
                if len(self._door) == 0:
                    self.next_level()
                break

        self.complete_action()
