"""Toxic floor: each cell expires ttl world steps after you first step on it; standing on expired floor loses."""

from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Tr01UI(RenderableUserDisplay):
    """Bottom row: steps until current tile expires; row above: level ttl cap (reference)."""

    def __init__(self, rem: int, ttl_cap: int) -> None:
        self._rem = rem
        self._ttl_cap = ttl_cap

    def update(self, rem: int, ttl_cap: int) -> None:
        self._rem = rem
        self._ttl_cap = ttl_cap

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, _w = frame.shape
        cap = max(1, self._ttl_cap)
        for i in range(min(cap, 14)):
            frame[h - 3, 1 + i] = 2
        r = max(0, min(self._rem, cap))
        for i in range(min(r, 14)):
            col = 8 if r <= 3 else 11
            frame[h - 2, 1 + i] = col
        return frame


sprites = {
    "player": Sprite(
        pixels=[[9]],
        name="player",
        visible=True,
        collidable=True,
        tags=["player"],
    ),
    "goal": Sprite(
        pixels=[[14]],
        name="goal",
        visible=True,
        collidable=False,
        tags=["goal"],
    ),
    "wall": Sprite(
        pixels=[[3]],
        name="wall",
        visible=True,
        collidable=True,
        tags=["wall"],
    ),
}


def mk(sl: list, d: int, ttl: int) -> Level:
    return Level(sprites=sl, grid_size=(10, 10), data={"difficulty": d, "ttl": ttl})


levels = [
    mk(
        [
            sprites["player"].clone().set_position(0, 5),
            sprites["goal"].clone().set_position(9, 5),
        ],
        1,
        25,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["goal"].clone().set_position(8, 8),
        ],
        2,
        20,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["goal"].clone().set_position(9, 9),
            sprites["wall"].clone().set_position(5, 4),
            sprites["wall"].clone().set_position(5, 5),
            sprites["wall"].clone().set_position(5, 6),
        ],
        3,
        18,
    ),
    mk(
        [
            sprites["player"].clone().set_position(2, 5),
            sprites["goal"].clone().set_position(7, 5),
        ],
        4,
        15,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 9),
            sprites["goal"].clone().set_position(9, 0),
        ],
        5,
        12,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Tr01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Tr01UI(20, 20)
        super().__init__(
            "tr01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._goal = self.current_level.get_sprites_by_tag("goal")[0]
        self._ttl = int(level.get_data("ttl") or 20)
        self._world_step = 0
        self._entered: dict[tuple[int, int], int] = {}
        self._sync_tr_ui()

    def _sync_tr_ui(self) -> None:
        px, py = self._player.x, self._player.y
        pos = (px, py)
        if pos in self._entered:
            rem = self._ttl - (self._world_step - self._entered[pos])
        else:
            rem = self._ttl
        self._ui.update(rem, self._ttl)

    def step(self) -> None:
        self._world_step += 1
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
            self._sync_tr_ui()
            self.complete_action()
            return

        nx = self._player.x + dx
        ny = self._player.y + dy
        gw, gh = self.current_level.grid_size
        if not (0 <= nx < gw and 0 <= ny < gh):
            self._sync_tr_ui()
            self.complete_action()
            return

        sp = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
        if sp and "wall" in sp.tags:
            self._sync_tr_ui()
            self.complete_action()
            return

        px, py = nx, ny
        if (px, py) in self._entered:
            if self._world_step - self._entered[(px, py)] >= self._ttl:
                self.lose()
                self._sync_tr_ui()
                self.complete_action()
                return

        self._player.set_position(nx, ny)
        pos = (nx, ny)
        if pos not in self._entered:
            self._entered[pos] = self._world_step

        for c, t0 in list(self._entered.items()):
            if self._world_step - t0 >= self._ttl:
                if self._player.x == c[0] and self._player.y == c[1]:
                    self.lose()
                    self._sync_tr_ui()
                    self.complete_action()
                    return

        if self._player.x == self._goal.x and self._player.y == self._goal.y:
            self.next_level()

        self._sync_tr_ui()
        self.complete_action()
