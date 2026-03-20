from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Va02UI(RenderableUserDisplay):
    def __init__(self, remaining: int, strikes_left: int) -> None:
        self._remaining = remaining
        self._strikes_left = strikes_left

    def update(self, remaining: int, strikes_left: int) -> None:
        self._remaining = remaining
        self._strikes_left = strikes_left

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        color = 14 if self._remaining == 0 else 11
        for dy in range(4):
            for dx in range(4):
                frame[h - 4 + dy, w - 4 + dx] = color
        for i in range(3):
            c = 14 if i < self._strikes_left else 8
            for dy in range(2):
                for dx in range(2):
                    frame[h - 4 + dy, 2 + i * 3 + dx] = c
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
    "trail": Sprite(
        pixels=[[14]],
        name="trail",
        visible=True,
        collidable=False,
        tags=["trail"],
        layer=0,
    ),
    "wall": Sprite(
        pixels=[[3]],
        name="wall",
        visible=True,
        collidable=True,
        tags=["wall"],
        layer=1,
    ),
    "hazard": Sprite(
        pixels=[[8]],
        name="hazard",
        visible=True,
        collidable=True,
        tags=["hazard"],
        layer=1,
    ),
}


def mk(sl, grid_size, difficulty):
    return Level(sprites=sl, grid_size=grid_size, data={"difficulty": difficulty})


levels = [
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["hazard"].clone().set_position(2, 2),
        ],
        (4, 4),
        1,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["hazard"].clone().set_position(1, 1),
            sprites["hazard"].clone().set_position(3, 3),
        ],
        (5, 5),
        2,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
        ]
        + [sprites["hazard"].clone().set_position(x, 2) for x in range(8) if x != 4],
        (8, 8),
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["hazard"].clone().set_position(3, 3),
            sprites["hazard"].clone().set_position(4, 4),
        ]
        + [sprites["wall"].clone().set_position(2, y) for y in range(6) if y != 2],
        (6, 6),
        4,
    ),
    mk(
        [
            sprites["player"].clone().set_position(3, 3),
            sprites["hazard"].clone().set_position(0, 0),
            sprites["hazard"].clone().set_position(1, 0),
            sprites["hazard"].clone().set_position(0, 1),
        ],
        (8, 8),
        5,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Va02(ARCBaseGame):
    """Visit every safe floor cell; red hazard cells are not part of coverage and block entry.
    Three blocked move attempts (OOB, wall, hazard) in one level = lose."""

    MAX_STRIKES = 3

    def _add_trail(self, x: int, y: int) -> None:
        t = sprites["trail"].clone().set_position(x, y)
        self.current_level.add_sprite(t)

    def _sync_ui(self) -> None:
        rem = len(self._open_cells) - len(self._visited)
        left = self.MAX_STRIKES - self._strikes
        self._ui.update(rem, left)

    def __init__(self) -> None:
        self._ui = Va02UI(0, self.MAX_STRIKES)
        super().__init__(
            "va02",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def _compute_open_cells(self) -> set[tuple[int, int]]:
        gw, gh = self.current_level.grid_size
        o: set[tuple[int, int]] = set()
        for x in range(gw):
            for y in range(gh):
                sp = self.current_level.get_sprite_at(x, y, ignore_collidable=True)
                if sp and "wall" in sp.tags:
                    continue
                if sp and "hazard" in sp.tags:
                    continue
                o.add((x, y))
        return o

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._open_cells = self._compute_open_cells()
        self._visited: set[tuple[int, int]] = {(self._player.x, self._player.y)}
        self._strikes = 0
        self._add_trail(self._player.x, self._player.y)
        self._sync_ui()

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
            self._strikes += 1
            self._sync_ui()
            if self._strikes >= self.MAX_STRIKES:
                self.lose()
            self.complete_action()
            return

        sprite = self.current_level.get_sprite_at(new_x, new_y, ignore_collidable=True)

        if sprite and "wall" in sprite.tags:
            self._strikes += 1
            self._sync_ui()
            if self._strikes >= self.MAX_STRIKES:
                self.lose()
            self.complete_action()
            return

        if sprite and "hazard" in sprite.tags:
            self._strikes += 1
            self._sync_ui()
            if self._strikes >= self.MAX_STRIKES:
                self.lose()
            self.complete_action()
            return

        if not sprite or not sprite.is_collidable:
            self._player.set_position(new_x, new_y)

        pos = (self._player.x, self._player.y)
        if pos not in self._visited:
            self._add_trail(*pos)
        self._visited.add(pos)
        self._sync_ui()

        if self._visited == self._open_cells:
            self.next_level()

        self.complete_action()
