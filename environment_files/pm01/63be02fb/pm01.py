"""Prime steps: movement actions only take effect on prime global step counts (2,3,5,…); others no-op."""

from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Pm01UI(RenderableUserDisplay):
    def __init__(self, n_levels: int) -> None:
        self._s = 0
        self._prime_step = False
        self._move_noop = False
        self._n_levels = n_levels
        self._li = 0

    def update(
        self,
        s: int,
        level_index: int | None = None,
        *,
        prime_step: bool = False,
        move_noop: bool = False,
    ) -> None:
        self._s = s
        self._prime_step = prime_step
        self._move_noop = move_noop
        if level_index is not None:
            self._li = level_index

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for i in range(min(self._n_levels, 14)):
            cx = 1 + i * 2
            if cx >= w:
                break
            c = 14 if i < self._li else (11 if i == self._li else 3)
            frame[0, cx] = c
        for i in range(min(self._s % 20, 18)):
            frame[2, 2 + i] = 11
        frame[3, 2] = 14 if self._prime_step else 3
        if self._move_noop:
            frame[h - 1, min(w - 1, 15)] = 12
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


def mk(sl: list, d: int) -> Level:
    return Level(sprites=sl, grid_size=(10, 10), data={"difficulty": d})


def _h_corridor_walls() -> list:
    """y=5 lane with solid walls on y=4 and y=6 (full width)."""
    return [
        *[sprites["wall"].clone().set_position(x, 4) for x in range(10)],
        *[sprites["wall"].clone().set_position(x, 6) for x in range(10)],
    ]


# Layouts tuned for **prime-index moves only** (distinct geometry from in01 ink mazes).
levels = [
    mk(
        [
            sprites["player"].clone().set_position(0, 5),
            sprites["goal"].clone().set_position(4, 5),
            *_h_corridor_walls(),
        ],
        1,
    ),
    mk(
        [
            sprites["player"].clone().set_position(5, 0),
            sprites["goal"].clone().set_position(5, 5),
            *[sprites["wall"].clone().set_position(4, y) for y in range(10)],
            *[sprites["wall"].clone().set_position(6, y) for y in range(10)],
        ],
        2,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 5),
            sprites["goal"].clone().set_position(9, 5),
            *_h_corridor_walls(),
        ],
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 1),
            sprites["goal"].clone().set_position(3, 1),
            *[sprites["wall"].clone().set_position(x, 0) for x in range(10)],
            *[sprites["wall"].clone().set_position(x, 2) for x in range(10)],
        ],
        4,
    ),
    mk(
        [
            sprites["player"].clone().set_position(8, 8),
            sprites["goal"].clone().set_position(1, 1),
            *[sprites["wall"].clone().set_position(x, 0) for x in range(10)],
            *[sprites["wall"].clone().set_position(x, 9) for x in range(10)],
            *[sprites["wall"].clone().set_position(0, y) for y in range(10)],
            *[sprites["wall"].clone().set_position(9, y) for y in range(10)],
            sprites["wall"].clone().set_position(5, 5),
        ],
        5,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


def _is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True


class Pm01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Pm01UI(len(levels))
        super().__init__(
            "pm01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._goal = self.current_level.get_sprites_by_tag("goal")[0]
        self._si = 0
        self._ui.update(0, self.level_index, prime_step=False, move_noop=False)

    def step(self) -> None:
        self._si += 1
        prime = _is_prime(self._si)

        dx = dy = 0
        if self.action.id.value == 1:
            dy = -1
        elif self.action.id.value == 2:
            dy = 1
        elif self.action.id.value == 3:
            dx = -1
        elif self.action.id.value == 4:
            dx = 1

        move_intent = dx != 0 or dy != 0
        move_noop = move_intent and not prime
        self._ui.update(self._si, self.level_index, prime_step=prime, move_noop=move_noop)

        if prime and move_intent:
            nx = self._player.x + dx
            ny = self._player.y + dy
            gw, gh = self.current_level.grid_size
            if (0 <= nx < gw and 0 <= ny < gh):
                sp = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
                if not (sp and "wall" in sp.tags):
                    self._player.set_position(nx, ny)

        if self._player.x == self._goal.x and self._player.y == self._goal.y:
            self.next_level()

        self.complete_action()
