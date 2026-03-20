"""Cyan waypoint must be entered from the correct side before the yellow goal counts."""

from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


# ``waypoint_enter_from``: which neighbor you step *from* onto the waypoint (compass on grid).
# Move onto tile uses (dx, dy): n=(0,+1) down, s=(0,-1) up, e=(-1,0) left, w=(+1,0) right.
_ENTRY_DELTA: dict[str, tuple[int, int]] = {
    "n": (0, 1),
    "s": (0, -1),
    "e": (-1, 0),
    "w": (1, 0),
}


class Dt01UI(RenderableUserDisplay):
    def __init__(self, ok: bool) -> None:
        self._ok = ok

    def update(self, ok: bool) -> None:
        self._ok = ok

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        color = 10 if self._ok else 5
        for dy in range(3):
            for dx in range(3):
                frame[h - 3 + dy, w - 4 + dx] = color
        return frame


sprites = {
    "player": Sprite(
        pixels=[[9]],
        name="player",
        visible=True,
        collidable=True,
        tags=["player"],
        layer=2,
    ),
    "waypoint": Sprite(
        pixels=[[10]],
        name="waypoint",
        visible=True,
        collidable=False,
        tags=["waypoint"],
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


def mk(sl, grid_size, difficulty, waypoint_enter_from: str = "w"):
    return Level(
        sprites=sl,
        grid_size=grid_size,
        data={
            "difficulty": difficulty,
            "waypoint_enter_from": waypoint_enter_from,
        },
    )


levels = [
    # Shortest path to goal crosses waypoint from the west; required entry is from the south
    # (step up). Agents can stand on goal without a valid detour latch.
    mk(
        [
            sprites["player"].clone().set_position(0, 3),
            sprites["waypoint"].clone().set_position(3, 3),
            sprites["target"].clone().set_position(7, 3),
        ],
        (8, 8),
        1,
        "s",
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["waypoint"].clone().set_position(2, 3),
            sprites["target"].clone().set_position(6, 1),
        ]
        + [sprites["wall"].clone().set_position(3, y) for y in range(8) if y != 4],
        (8, 8),
        2,
        "n",
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["waypoint"].clone().set_position(2, 2),
            sprites["target"].clone().set_position(7, 7),
        ],
        (8, 8),
        3,
        "w",
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 4),
            sprites["waypoint"].clone().set_position(3, 4),
            sprites["target"].clone().set_position(8, 4),
        ]
        + [sprites["wall"].clone().set_position(5, y) for y in range(8) if y != 4],
        (10, 8),
        4,
        "w",
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 7),
            sprites["waypoint"].clone().set_position(3, 3),
            sprites["target"].clone().set_position(7, 0),
        ],
        (8, 8),
        5,
        "n",
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Dt01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Dt01UI(False)
        super().__init__(
            "dt01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._waypoints = self.current_level.get_sprites_by_tag("waypoint")
        self._targets = self.current_level.get_sprites_by_tag("target")
        self._hit_waypoint = False
        raw = level.get_data("waypoint_enter_from") or "w"
        key = str(raw).lower().strip()[:1]
        self._entry_delta = _ENTRY_DELTA.get(key, (1, 0))
        self._ui.update(False)

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

        for w in self._waypoints:
            if self._player.x == w.x and self._player.y == w.y:
                if (dx, dy) == self._entry_delta:
                    self._hit_waypoint = True
                    self._ui.update(True)
                break

        for t in self._targets:
            if self._player.x == t.x and self._player.y == t.y:
                if self._hit_waypoint:
                    self.next_level()
                break

        self.complete_action()
