"""Hamiltonian tour: visit every walkable cell exactly once (revisit = lose); no separate goal tile."""

from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Hm01UI(RenderableUserDisplay):
    def __init__(self, remaining: int) -> None:
        self._remaining = remaining

    def update(self, remaining: int) -> None:
        self._remaining = remaining

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        color = 14 if self._remaining == 0 else 11
        for dy in range(4):
            for dx in range(4):
                frame[h - 4 + dy, w - 4 + dx] = color
        return frame


sprites = {
    "player": Sprite(
        pixels=[[9]],
        name="player",
        visible=True,
        collidable=True,
        tags=["player"],
    ),
    "wall": Sprite(
        pixels=[[3]],
        name="wall",
        visible=True,
        collidable=True,
        tags=["wall"],
    ),
}


def mk(sl, grid_size, difficulty):
    return Level(sprites=sl, grid_size=grid_size, data={"difficulty": difficulty})


levels = [
    mk([sprites["player"].clone().set_position(0, 0)], (3, 3), 1),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["wall"].clone().set_position(1, 1),
        ],
        (3, 3),
        2,
    ),
    mk(
        [sprites["player"].clone().set_position(0, 0)]
        + [sprites["wall"].clone().set_position(2, y) for y in range(4) if y != 1],
        (4, 4),
        3,
    ),
    mk(
        [sprites["player"].clone().set_position(0, 0)]
        + [sprites["wall"].clone().set_position(x, 2) for x in range(5) if x != 2],
        (5, 5),
        4,
    ),
    mk(
        [sprites["player"].clone().set_position(0, 0)]
        + [sprites["wall"].clone().set_position(1, y) for y in range(6) if y not in (2, 3)]
        + [sprites["wall"].clone().set_position(4, y) for y in range(6) if y not in (2, 3)],
        (6, 6),
        5,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Hm01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Hm01UI(0)
        super().__init__(
            "hm01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def _open_total(self) -> int:
        gw, gh = self.current_level.grid_size
        n = 0
        for y in range(gh):
            for x in range(gw):
                sp = self.current_level.get_sprite_at(x, y, ignore_collidable=True)
                if sp and "wall" in sp.tags:
                    continue
                n += 1
        return n

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._visited: set[tuple[int, int]] = set()
        self._visited.add((self._player.x, self._player.y))
        self._need = self._open_total()
        self._ui.update(self._need - len(self._visited))

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

        nx = self._player.x + dx
        ny = self._player.y + dy
        grid_w, grid_h = self.current_level.grid_size
        if not (0 <= nx < grid_w and 0 <= ny < grid_h):
            self.complete_action()
            return

        sprite = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
        if sprite and "wall" in sprite.tags:
            self.complete_action()
            return

        if (nx, ny) in self._visited:
            self.lose()
            self.complete_action()
            return

        if not sprite or not sprite.is_collidable:
            self._player.set_position(nx, ny)
            self._visited.add((nx, ny))
            self._ui.update(self._need - len(self._visited))

        if len(self._visited) >= self._need:
            self.next_level()

        self.complete_action()
