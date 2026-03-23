"""Key leash: a key sprite must stay within Manhattan distance R of the player or you lose."""

from arcengine import (
    ARCBaseGame,
    Camera,
    GameState,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Kb01UI(RenderableUserDisplay):
    def __init__(self, r: int, num_levels: int) -> None:
        self._r = r
        self._dist = 0
        self._li = 0
        self._nl = num_levels
        self._state: GameState | None = None

    def update(
        self,
        r: int,
        *,
        dist: int | None = None,
        level_index: int | None = None,
        num_levels: int | None = None,
        state: GameState | None = None,
    ) -> None:
        self._r = r
        if dist is not None:
            self._dist = dist
        if level_index is not None:
            self._li = level_index
        if num_levels is not None:
            self._nl = num_levels
        if state is not None:
            self._state = state

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for i in range(min(self._nl, 14)):
            cx = 1 + i * 2
            if cx >= w:
                break
            c = 14 if i < self._li else (11 if i == self._li else 3)
            frame[0, cx] = c
        if self._state in (GameState.GAME_OVER, GameState.WIN):
            rrow = h - 3
            if rrow >= 0:
                cc = 14 if self._state == GameState.WIN else 8
                for x in range(min(w, 16)):
                    frame[rrow, x] = cc
        # Bottom row: Manhattan slack (R − d). Green = headroom, yellow = caution, red at i=0 when slack=0 (at leash limit).
        slack = max(0, self._r - self._dist)
        for i in range(min(self._r + 1, 8)):
            x = 1 + i
            if x >= w:
                break
            if slack == 0:
                c = 8 if i == 0 else 3
            elif i < slack:
                c = 14
            elif i == slack:
                c = 11
            else:
                c = 3
            frame[h - 2, x] = c
        return frame


sprites = {
    "player": Sprite(
        pixels=[[9]],
        name="player",
        visible=True,
        collidable=True,
        tags=["player"],
    ),
    "key": Sprite(
        pixels=[[11]],
        name="key",
        visible=True,
        collidable=False,
        tags=["key"],
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


def mk(sl: list, d: int, r: int) -> Level:
    return Level(sprites=sl, grid_size=(10, 10), data={"difficulty": d, "leash": r})


levels = [
    mk(
        [
            sprites["player"].clone().set_position(1, 5),
            sprites["key"].clone().set_position(3, 5),
            sprites["goal"].clone().set_position(7, 5),
        ],
        1,
        4,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 5),
            sprites["key"].clone().set_position(2, 5),
            sprites["goal"].clone().set_position(5, 5),
        ],
        2,
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 5),
            sprites["key"].clone().set_position(4, 5),
            sprites["goal"].clone().set_position(8, 5),
        ]
        + [sprites["wall"].clone().set_position(6, y) for y in range(10) if y != 5],
        3,
        5,
    ),
    mk(
        [
            sprites["player"].clone().set_position(2, 5),
            sprites["key"].clone().set_position(4, 5),
            sprites["goal"].clone().set_position(7, 5),
        ],
        4,
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["key"].clone().set_position(1, 0),
            sprites["goal"].clone().set_position(4, 0),
        ],
        5,
        4,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Kb01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Kb01UI(4, len(levels))
        super().__init__(
            "kb01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._key = self.current_level.get_sprites_by_tag("key")[0]
        self._goal = self.current_level.get_sprites_by_tag("goal")[0]
        self._r = int(level.get_data("leash") or 4)
        self._sync_ui()

    def _sync_ui(self) -> None:
        d = abs(self._player.x - self._key.x) + abs(self._player.y - self._key.y)
        self._ui.update(
            self._r,
            dist=d,
            level_index=self.level_index,
            num_levels=len(levels),
            state=self._state,
        )

    def _leash_ok(self) -> bool:
        d = abs(self._player.x - self._key.x) + abs(self._player.y - self._key.y)
        return d <= self._r

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

        if dx == 0 and dy == 0:
            self._sync_ui()
            self.complete_action()
            return

        nx = self._player.x + dx
        ny = self._player.y + dy
        gw, gh = self.current_level.grid_size
        if not (0 <= nx < gw and 0 <= ny < gh):
            self._sync_ui()
            self.complete_action()
            return

        sp = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
        if sp and "wall" in sp.tags:
            self._sync_ui()
            self.complete_action()
            return

        self._player.set_position(nx, ny)

        if not self._leash_ok():
            self.lose()
            self._sync_ui()
            self.complete_action()
            return

        if self._player.x == self._goal.x and self._player.y == self._goal.y:
            self.next_level()

        self._sync_ui()
        self.complete_action()
