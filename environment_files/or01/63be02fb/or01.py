"""Orbit keys: gold keys sit on a ring around a central pillar; each step they rotate clockwise; grab a key from an orth-adjacent cell."""

from arcengine import (
    ARCBaseGame,
    Camera,
    GameAction,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Or01UI(RenderableUserDisplay):
    def __init__(self, held: int, need: int) -> None:
        self._held = held
        self._need = need
        self._pickup_flash = 0

    def update(self, held: int, need: int) -> None:
        self._held = held
        self._need = need

    def flash_pickup(self, frames: int = 6) -> None:
        self._pickup_flash = frames

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for i in range(min(self._need, 4)):
            frame[h - 2, 2 + i] = 11 if i < self._held else 5
        if self._pickup_flash > 0:
            c = 0 if self._pickup_flash % 2 == 0 else 11
            for dy in range(2):
                for dx in range(3):
                    px, py = w - 5 + dx, h - 4 + dy
                    if 0 <= px < w and 0 <= py < h:
                        frame[py, px] = c
            self._pickup_flash -= 1
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
    "pillar": Sprite(
        pixels=[[2]],
        name="pillar",
        visible=True,
        collidable=True,
        tags=["pillar"],
    ),
    "key": Sprite(
        pixels=[[11]],
        name="key",
        visible=True,
        collidable=False,
        tags=["key"],
    ),
}


def mk(sl, d: int, cx: int, cy: int):
    return Level(
        sprites=sl,
        grid_size=(10, 10),
        data={"difficulty": d, "pillar": [cx, cy]},
    )


# Ring positions clockwise from east around (cx,cy)
def ring_offsets():
    return [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]


levels = [
    mk(
        [
            sprites["player"].clone().set_position(1, 5),
            sprites["pillar"].clone().set_position(5, 5),
            sprites["key"].clone().set_position(6, 5),
            sprites["key"].clone().set_position(5, 6),
            sprites["goal"].clone().set_position(8, 5),
        ],
        1,
        5,
        5,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 5),
            sprites["pillar"].clone().set_position(4, 5),
            sprites["key"].clone().set_position(5, 5),
            sprites["goal"].clone().set_position(9, 5),
        ],
        2,
        4,
        5,
    ),
    mk(
        [
            sprites["player"].clone().set_position(2, 2),
            sprites["pillar"].clone().set_position(5, 5),
            sprites["key"].clone().set_position(6, 5),
            sprites["key"].clone().set_position(4, 5),
            sprites["key"].clone().set_position(5, 4),
            sprites["goal"].clone().set_position(8, 8),
        ],
        3,
        5,
        5,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["pillar"].clone().set_position(5, 4),
            sprites["key"].clone().set_position(6, 4),
            sprites["goal"].clone().set_position(8, 7),
        ]
        + [sprites["wall"].clone().set_position(3, y) for y in range(6, 9)],
        4,
        5,
        4,
    ),
    mk(
        [
            sprites["player"].clone().set_position(5, 9),
            sprites["pillar"].clone().set_position(5, 5),
            sprites["key"].clone().set_position(6, 5),
            sprites["key"].clone().set_position(5, 6),
            sprites["key"].clone().set_position(4, 5),
            sprites["goal"].clone().set_position(5, 0),
        ],
        5,
        5,
        5,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Or01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Or01UI(0, 2)
        self._keys: list[Sprite] = []
        self._ring_index: list[int] = []
        super().__init__(
            "or01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._goal = self.current_level.get_sprites_by_tag("goal")[0]
        self._keys = list(self.current_level.get_sprites_by_tag("key"))
        pc = level.get_data("pillar") or [5, 5]
        self._cx, self._cy = int(pc[0]), int(pc[1])
        ring = ring_offsets()
        self._ring_index = []
        for k in self._keys:
            best = 0
            bestd = 999
            for i, (ox, oy) in enumerate(ring):
                if k.x == self._cx + ox and k.y == self._cy + oy:
                    best = i
                    bestd = 0
                    break
                d = abs(k.x - (self._cx + ox)) + abs(k.y - (self._cy + oy))
                if d < bestd:
                    bestd = d
                    best = i
            self._ring_index.append(best)
        self._held = 0
        self._need_keys = len(self._keys)
        self._ui.update(0, self._need_keys)

    def _rotate_keys(self) -> None:
        ring = ring_offsets()
        n = len(ring)
        for ki, k in enumerate(self._keys):
            self._ring_index[ki] = (self._ring_index[ki] + 1) % n
            ox, oy = ring[self._ring_index[ki]]
            k.set_position(self._cx + ox, self._cy + oy)

    def _try_pickup(self) -> None:
        px, py = self._player.x, self._player.y
        for i, k in enumerate(list(self._keys)):
            if abs(k.x - px) + abs(k.y - py) == 1:
                self.current_level.remove_sprite(k)
                self._keys.pop(i)
                self._ring_index.pop(i)
                self._held += 1
                self._ui.flash_pickup()
                break
        self._ui.update(self._held, self._need_keys)

    def step(self) -> None:
        dx = dy = 0
        if self.action.id == GameAction.ACTION1:
            dy = -1
        elif self.action.id == GameAction.ACTION2:
            dy = 1
        elif self.action.id == GameAction.ACTION3:
            dx = -1
        elif self.action.id == GameAction.ACTION4:
            dx = 1

        self._rotate_keys()

        if dx == 0 and dy == 0:
            self.complete_action()
            return

        nx = self._player.x + dx
        ny = self._player.y + dy
        gw, gh = self.current_level.grid_size
        if not (0 <= nx < gw and 0 <= ny < gh):
            self.complete_action()
            return

        sp = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
        if sp and "wall" in sp.tags:
            self.complete_action()
            return
        if sp and "pillar" in sp.tags:
            self.complete_action()
            return

        if not sp or not sp.is_collidable:
            self._player.set_position(nx, ny)

        self._try_pickup()

        if self._held >= self._need_keys and self._player.x == self._goal.x and self._player.y == self._goal.y:
            self.next_level()

        self.complete_action()
