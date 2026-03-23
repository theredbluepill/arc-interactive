"""Dual phase hazards: two independent blinking hazard sets with different period/offset."""

from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Zq02UI(RenderableUserDisplay):
    def __init__(self, a: bool, b: bool) -> None:
        self._a = a
        self._b = b
        self._hazard_flash = 0

    def update(self, a: bool, b: bool) -> None:
        self._a = a
        self._b = b

    def flash_hazard_block(self, frames: int = 6) -> None:
        self._hazard_flash = frames

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        c0 = 8 if self._a else 10
        c1 = 8 if self._b else 13
        for dy in range(2):
            for dx in range(2):
                frame[h - 3 + dy, w - 5 + dx] = c0
                frame[h - 3 + dy, w - 3 + dx] = c1
        if self._hazard_flash > 0:
            for dy in range(2):
                for dx in range(2):
                    frame[h - 5 + dy, 1 + dx] = 8
            self._hazard_flash -= 1
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
    "hazard_a": Sprite(
        pixels=[[8]],
        name="hazard_a",
        visible=True,
        collidable=True,
        tags=["zq2_hazard_a"],
    ),
    "hazard_b": Sprite(
        pixels=[[12]],
        name="hazard_b",
        visible=True,
        collidable=True,
        tags=["zq2_hazard_b"],
    ),
    "wall": Sprite(
        pixels=[[3]],
        name="wall",
        visible=True,
        collidable=True,
        tags=["wall"],
    ),
}


def mk(sl, grid_size, difficulty, pa, pb, off_a, off_b, cells_a, cells_b):
    return Level(
        sprites=sl,
        grid_size=grid_size,
        data={
            "difficulty": difficulty,
            "period_a": pa,
            "period_b": pb,
            "offset_a": off_a,
            "offset_b": off_b,
            "hazard_cells_a": cells_a,
            "hazard_cells_b": cells_b,
        },
    )


levels = [
    mk(
        [
            sprites["player"].clone().set_position(0, 3),
            sprites["target"].clone().set_position(7, 3),
        ],
        (8, 8),
        1,
        4,
        6,
        0,
        2,
        [(3, 3), (4, 3)],
        [(5, 2), (5, 4)],
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["target"].clone().set_position(6, 6),
        ],
        (8, 8),
        2,
        3,
        5,
        0,
        1,
        [(2, y) for y in range(6, 8)],
        [(x, 2) for x in range(2, 6)],
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["target"].clone().set_position(7, 7),
        ],
        (8, 8),
        3,
        5,
        7,
        1,
        3,
        [(x, 4) for x in range(8) if x % 2 == 0],
        [(4, y) for y in range(8) if y % 2 == 1],
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 4),
            sprites["target"].clone().set_position(9, 4),
        ],
        (10, 8),
        4,
        4,
        5,
        0,
        2,
        [(3, y) for y in range(8)],
        [(6, y) for y in range(8) if y != 4],
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 7),
            sprites["target"].clone().set_position(7, 0),
        ],
        (8, 8),
        5,
        2,
        3,
        0,
        1,
        [(2, 2), (5, 5)],
        [(5, 2), (2, 5)],
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Zq02(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Zq02UI(False, False)
        super().__init__(
            "zq02",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        for tag in ("zq2_hazard_a", "zq2_hazard_b"):
            for s in list(self.current_level.get_sprites_by_tag(tag)):
                self.current_level.remove_sprite(s)
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._targets = self.current_level.get_sprites_by_tag("target")
        self._ticks = 0
        self._on_a = False
        self._on_b = False
        self._sprites_a: list[Sprite] = []
        self._sprites_b: list[Sprite] = []
        for hx, hy in list(self.current_level.get_data("hazard_cells_a") or []):
            s = sprites["hazard_a"].clone().set_position(hx, hy)
            self._sprites_a.append(s)
            self.current_level.add_sprite(s)
        for hx, hy in list(self.current_level.get_data("hazard_cells_b") or []):
            s = sprites["hazard_b"].clone().set_position(hx, hy)
            self._sprites_b.append(s)
            self.current_level.add_sprite(s)
        self._sync()

    def _sync(self) -> None:
        for s in self._sprites_a:
            s.set_visible(self._on_a)
            s.set_collidable(self._on_a)
        for s in self._sprites_b:
            s.set_visible(self._on_b)
            s.set_collidable(self._on_b)
        self._ui.update(self._on_a, self._on_b)

    def step(self) -> None:
        self._ticks += 1
        pa = int(self.current_level.get_data("period_a") or 4)
        pb = int(self.current_level.get_data("period_b") or 5)
        oa = int(self.current_level.get_data("offset_a") or 0)
        ob = int(self.current_level.get_data("offset_b") or 0)
        if (self._ticks + oa) % pa == 0:
            self._on_a = not self._on_a
        if (self._ticks + ob) % pb == 0:
            self._on_b = not self._on_b
        self._sync()

        dx = dy = 0
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
        if sprite and sprite.is_collidable and (
            "zq2_hazard_a" in sprite.tags or "zq2_hazard_b" in sprite.tags
        ):
            self._ui.flash_hazard_block()
            self.complete_action()
            return

        if not sprite or not sprite.is_collidable:
            self._player.set_position(nx, ny)

        for t in self._targets:
            if self._player.x == t.x and self._player.y == t.y:
                self.next_level()
                break

        self.complete_action()
