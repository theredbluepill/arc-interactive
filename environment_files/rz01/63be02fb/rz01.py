"""Rush grid: 1×2 vertical cars (two linked blocks) slide when pushed if both destination cells are free."""

from __future__ import annotations

from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Rz01UI(RenderableUserDisplay):
    def __init__(self, n: int) -> None:
        self._n = n

    def update(self, n: int) -> None:
        self._n = n

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        exit_open = self._n == 0
        c = 14 if exit_open else 11
        for dy in range(3):
            for dx in range(3):
                frame[h - 3 + dy, w - 3 + dx] = c
        return frame


sprites = {
    "player": Sprite(
        pixels=[[9]],
        name="player",
        visible=True,
        collidable=True,
        tags=["player"],
    ),
    "block": Sprite(
        pixels=[[15]],
        name="block",
        visible=True,
        collidable=True,
        tags=["block", "car"],
    ),
    "exit": Sprite(
        pixels=[[14]],
        name="exit",
        visible=True,
        collidable=False,
        tags=["exit_lane"],
    ),
    "wall": Sprite(
        pixels=[[3]],
        name="wall",
        visible=True,
        collidable=True,
        tags=["wall"],
    ),
}


def mk(sl, cars: list[list[list[int]]], d: int):
    return Level(
        sprites=sl,
        grid_size=(12, 12),
        data={"difficulty": d, "cars": cars},
    )


def _car_blocks(level: Level) -> list[Sprite]:
    return [s for s in level.get_sprites_by_tag("car")]


levels = [
    mk(
        [
            sprites["player"].clone().set_position(1, 5),
            sprites["exit"].clone().set_position(10, 5),
        ],
        [[[4, 4], [4, 5]]],
        1,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["exit"].clone().set_position(11, 0),
        ]
        + [sprites["wall"].clone().set_position(6, y) for y in range(12) if y != 5],
        [[[4, 5], [4, 6]]],
        2,
    ),
    mk(
        [
            sprites["player"].clone().set_position(2, 2),
            sprites["exit"].clone().set_position(9, 9),
        ],
        [[[5, 5], [5, 6]], [[7, 3], [7, 4]]],
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(5, 10),
            sprites["exit"].clone().set_position(5, 0),
        ],
        [[[5, 4], [5, 5]]],
        4,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 6),
            sprites["exit"].clone().set_position(11, 6),
        ],
        [[[3, 5], [3, 6]], [[8, 5], [8, 6]]],
        5,
    ),
]


BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Rz01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Rz01UI(1)
        super().__init__(
            "rz01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        for s in list(self.current_level.get_sprites_by_tag("car")):
            self.current_level.remove_sprite(s)
        cars = self.current_level.get_data("cars") or []
        for pair in cars:
            for px, py in pair:
                self.current_level.add_sprite(
                    sprites["block"].clone().set_position(int(px), int(py))
                )
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._cars_spec = [
            [(int(a[0]), int(a[1])), (int(b[0]), int(b[1]))] for a, b in cars
        ]
        self._sync_ui()

    def _positions(self) -> set[tuple[int, int]]:
        return {(s.x, s.y) for s in _car_blocks(self.current_level)}

    def _sync_ui(self) -> None:
        ex = self.current_level.get_sprites_by_tag("exit_lane")[0]
        occ = self._positions()
        clear = (ex.x, ex.y) not in occ and (ex.x, ex.y + 1) not in occ
        self._ui.update(0 if clear else 1)

    def _find_car_at(self, x: int, y: int) -> list[tuple[int, int]] | None:
        for a, b in self._cars_spec:
            if (x, y) == a or (x, y) == b:
                return [a, b]
        return None

    def step(self) -> None:
        dx = dy = 0
        if self.action.id.value == 1:
            dy = -1
        elif self.action.id.value == 2:
            dy = 1
        elif self.action.id.value == 3:
            dx = -1
        elif self.action.id.value == 4:
            dx = 1
        else:
            self.complete_action()
            return

        nx, ny = self._player.x + dx, self._player.y + dy
        gw, gh = self.current_level.grid_size
        if not (0 <= nx < gw and 0 <= ny < gh):
            self.complete_action()
            return

        sp = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
        if sp and "wall" in sp.tags:
            self.complete_action()
            return

        if sp and "car" in sp.tags:
            car = self._find_car_at(nx, ny)
            if not car:
                self.complete_action()
                return
            npos = [(cx + dx, cy + dy) for cx, cy in car]
            for cx, cy in npos:
                if not (0 <= cx < gw and 0 <= cy < gh):
                    self.complete_action()
                    return
                t = self.current_level.get_sprite_at(cx, cy, ignore_collidable=True)
                if t and "wall" in t.tags:
                    self.complete_action()
                    return
                if t and "car" in t.tags and (t.x, t.y) not in car:
                    self.complete_action()
                    return
            for s in _car_blocks(self.current_level):
                if (s.x, s.y) in car:
                    s.set_position(s.x + dx, s.y + dy)
            for i, (a, b) in enumerate(self._cars_spec):
                if (nx, ny) in (a, b):
                    self._cars_spec[i] = [
                        (a[0] + dx, a[1] + dy),
                        (b[0] + dx, b[1] + dy),
                    ]
                    break
            self._player.set_position(nx, ny)
        elif not sp or not sp.is_collidable:
            self._player.set_position(nx, ny)

        ex = self.current_level.get_sprites_by_tag("exit_lane")[0]
        occ = self._positions()
        if (ex.x, ex.y) not in occ and (ex.x, ex.y + 1) not in occ:
            self.next_level()

        self._sync_ui()
        self.complete_action()
