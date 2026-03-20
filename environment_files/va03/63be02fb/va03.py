from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Va03UI(RenderableUserDisplay):
    def __init__(self, idx: int, total: int) -> None:
        self._idx = idx
        self._total = total

    def update(self, idx: int, total: int) -> None:
        self._idx = idx
        self._total = total

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for i in range(min(self._total, 5)):
            c = 14 if i < self._idx else 11
            for dy in range(2):
                for dx in range(2):
                    frame[h - 4 + dy, w - 10 + i * 2 + dx] = c
        return frame


sprites = {
    "player": Sprite(
        pixels=[[9]],
        name="player",
        visible=True,
        collidable=True,
        tags=["player"],
    ),
    "mark": Sprite(
        pixels=[[11]],
        name="mark",
        visible=True,
        collidable=False,
        tags=["mark"],
    ),
    "wall": Sprite(
        pixels=[[3]],
        name="wall",
        visible=True,
        collidable=True,
        tags=["wall"],
    ),
}


def mk(sl, grid_size, difficulty, visit_order):
    return Level(
        sprites=sl,
        grid_size=grid_size,
        data={"difficulty": difficulty, "visit_order": visit_order},
    )


def level_with_marks(vo, walls, grid_size, diff, player_pos):
    sl = [sprites["player"].clone().set_position(*player_pos)]
    for p in vo:
        sl.append(sprites["mark"].clone().set_position(*p))
    for wp in walls:
        sl.append(sprites["wall"].clone().set_position(*wp))
    return mk(sl, grid_size, diff, vo)


levels = [
    level_with_marks([(0, 0), (1, 1), (2, 2)], [], (4, 4), 1, (0, 0)),
    level_with_marks([(0, 0), (2, 0), (2, 2), (0, 2)], [], (5, 5), 2, (0, 0)),
    level_with_marks(
        [(0, 0), (1, 0), (2, 0), (3, 0)],
        [(1, 1), (2, 1)],
        (8, 8),
        3,
        (0, 1),
    ),
    level_with_marks([(1, 1), (3, 1), (3, 3), (1, 3)], [(2, 2)], (6, 6), 4, (0, 0)),
    level_with_marks([(0, 0), (7, 0), (7, 7), (0, 7)], [], (8, 8), 5, (0, 0)),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Va03(ARCBaseGame):
    """Step on yellow waypoints in numbered order (level order); then the level clears."""

    def __init__(self) -> None:
        self._ui = Va03UI(0, 1)
        super().__init__(
            "va03",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        vo = level.get_data("visit_order") or []
        self._order = [tuple(p) for p in vo]
        self._next = 0
        if (
            self._order
            and (self._player.x, self._player.y) == self._order[0]
        ):
            self._next = 1
        self._ui.update(self._next, len(self._order))

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
        if self._next < len(self._order) and pos == self._order[self._next]:
            self._next += 1
            self._ui.update(self._next, len(self._order))
            if self._next >= len(self._order):
                self.next_level()

        self.complete_action()
