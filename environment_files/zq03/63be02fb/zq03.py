"""Synced dual hazards: `mask_b` length is a multiple of `mask_a` rhythm; exactly one tick per cycle has both sets safe (beat window)."""

from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Zq03UI(RenderableUserDisplay):
    def __init__(self, a: bool, b: bool) -> None:
        self._a = a
        self._b = b

    def update(self, a: bool, b: bool) -> None:
        self._a = a
        self._b = b

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
        tags=["zq3_hazard_a"],
    ),
    "hazard_b": Sprite(
        pixels=[[12]],
        name="hazard_b",
        visible=True,
        collidable=True,
        tags=["zq3_hazard_b"],
    ),
    "wall": Sprite(
        pixels=[[3]],
        name="wall",
        visible=True,
        collidable=True,
        tags=["wall"],
    ),
}


def mk(sl, grid_size, difficulty, cells_a, cells_b, mask_a: list[int], mask_b: list[int]):
    assert len(mask_a) == len(mask_b)
    return Level(
        sprites=sl,
        grid_size=grid_size,
        data={
            "difficulty": difficulty,
            "hazard_cells_a": cells_a,
            "hazard_cells_b": cells_b,
            "mask_a": mask_a,
            "mask_b": mask_b,
            "cycle_len": len(mask_a),
        },
    )


# 1 = dangerous/on, 0 = safe/off; only index 0 has both 0
M1A = [0, 1, 1, 1, 1, 1, 1, 1]
M1B = [0, 0, 1, 1, 1, 1, 1, 1]
M2A = [0, 1, 0, 1, 1, 1, 1, 1]
M2B = [0, 1, 1, 0, 1, 1, 1, 1]
M3A = [0, 1, 1, 1, 0, 1, 1, 1]
M3B = [0, 1, 1, 1, 1, 0, 1, 1]
M4A = [0, 1, 1, 1, 1, 1, 1, 1]
M4B = [0, 1, 0, 1, 0, 1, 0, 1]
M5A = [0, 1, 1, 1, 1, 1, 1, 1]
M5B = [0, 0, 1, 1, 1, 1, 1, 1]


def _solo_beat(ma: list[int], mb: list[int]) -> bool:
    hits = [i for i in range(len(ma)) if ma[i] == 0 and mb[i] == 0]
    return len(hits) == 1


assert _solo_beat(M1A, M1B)
assert _solo_beat(M2A, M2B)
assert _solo_beat(M3A, M3B)
assert _solo_beat(M4A, M4B)
assert _solo_beat(M5A, M5B)


levels = [
    mk(
        [
            sprites["player"].clone().set_position(0, 3),
            sprites["target"].clone().set_position(7, 3),
        ],
        (8, 8),
        1,
        [(3, 3), (4, 3)],
        [(5, 2), (5, 4)],
        M1A,
        M1B,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["target"].clone().set_position(6, 6),
        ],
        (8, 8),
        2,
        [(2, y) for y in range(6, 8)],
        [(x, 2) for x in range(2, 6)],
        M2A,
        M2B,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["target"].clone().set_position(7, 7),
        ],
        (8, 8),
        3,
        [(x, 4) for x in range(8) if x % 2 == 0],
        [(4, y) for y in range(8) if y % 2 == 1],
        M3A,
        M3B,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 4),
            sprites["target"].clone().set_position(9, 4),
        ],
        (10, 8),
        4,
        [(3, y) for y in range(8)],
        [(6, y) for y in range(8) if y != 4],
        M4A,
        M4B,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 7),
            sprites["target"].clone().set_position(7, 0),
        ],
        (8, 8),
        5,
        [(2, 2), (5, 5)],
        [(5, 2), (2, 5)],
        M5A,
        M5B,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Zq03(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Zq03UI(False, False)
        super().__init__(
            "zq03",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        for tag in ("zq3_hazard_a", "zq3_hazard_b"):
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
        L = int(self.current_level.get_data("cycle_len") or 8)
        ma = list(self.current_level.get_data("mask_a") or [])
        mb = list(self.current_level.get_data("mask_b") or [])
        if len(ma) != L or len(mb) != L:
            L = max(len(ma), len(mb), 1)
        m = (self._ticks - 1) % L
        self._on_a = bool(ma[m]) if m < len(ma) else False
        self._on_b = bool(mb[m]) if m < len(mb) else False
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
            "zq3_hazard_a" in sprite.tags or "zq3_hazard_b" in sprite.tags
        ):
            self.complete_action()
            return

        if not sprite or not sprite.is_collidable:
            self._player.set_position(nx, ny)

        for t in self._targets:
            if self._player.x == t.x and self._player.y == t.y:
                self.next_level()
                break

        self.complete_action()
