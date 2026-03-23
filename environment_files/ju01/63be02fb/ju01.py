"""Jump tile: stepping onto a jump floor continues one extra cell in the same direction when the skip cell is clear."""

from arcengine import (
    ARCBaseGame,
    Camera,
    GameAction,
    GameState,
    Level,
    RenderableUserDisplay,
    Sprite,
)


def _rp(frame, h, w, x, y, c):
    if 0 <= x < w and 0 <= y < h:
        frame[y, x] = c


def _r_dots(frame, h, w, li, n, y0=0):
    for i in range(min(n, 14)):
        cx = 1 + i * 2
        if cx >= w:
            break
        c = 14 if i < li else (11 if i == li else 3)
        _rp(frame, h, w, cx, y0, c)


def _r_bar(frame, h, w, game_over, win):
    if not (game_over or win):
        return
    r = h - 3
    if r < 0:
        return
    c = 14 if win else 8
    for x in range(min(w, 16)):
        _rp(frame, h, w, x, r, c)


class Ju01UI(RenderableUserDisplay):
    def __init__(self, d: int, num_levels: int) -> None:
        self._d = d
        self._num_levels = num_levels
        self._level_index = 0
        self._gs: GameState | None = None
        self._skid_gx = -1
        self._skid_gy = -1
        self._skid_frames = 0

    def update(
        self,
        d: int,
        *,
        level_index: int | None = None,
        gs: GameState | None = None,
    ) -> None:
        self._d = d
        if level_index is not None:
            self._level_index = level_index
        if gs is not None:
            self._gs = gs

    def mark_skid_cell(self, gx: int, gy: int, frames: int = 8) -> None:
        self._skid_gx = gx
        self._skid_gy = gy
        self._skid_frames = frames

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        _r_dots(frame, h, w, self._level_index, self._num_levels, 0)
        for i in range(min(self._d, 12)):
            frame[h - 2, 1 + i] = 12
        go = self._gs == GameState.GAME_OVER
        win = self._gs == GameState.WIN
        _r_bar(frame, h, w, go, win)
        if self._skid_frames > 0 and self._skid_gx >= 0:
            scale = 4
            cx = self._skid_gx * scale + scale // 2
            cy = self._skid_gy * scale + scale // 2
            c = 0 if self._skid_frames % 2 == 0 else 12
            for dx, dy in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
                _rp(frame, h, w, cx + dx, cy + dy, c)
            self._skid_frames -= 1
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
    "jump": Sprite(
        pixels=[[12]],
        name="jump",
        visible=True,
        collidable=False,
        tags=["jump"],
    ),
}


def mk(sl, d: int):
    return Level(sprites=sl, grid_size=(10, 10), data={"difficulty": d})


levels = [
    mk(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["goal"].clone().set_position(8, 8),
            sprites["jump"].clone().set_position(4, 4),
        ],
        1,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 5),
            sprites["goal"].clone().set_position(9, 5),
            sprites["jump"].clone().set_position(3, 5),
            sprites["jump"].clone().set_position(6, 5),
        ],
        2,
    ),
    mk(
        [
            sprites["player"].clone().set_position(2, 2),
            sprites["goal"].clone().set_position(7, 7),
            sprites["wall"].clone().set_position(5, 4),
            sprites["wall"].clone().set_position(5, 5),
            sprites["jump"].clone().set_position(5, 3),
        ],
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 8),
            sprites["goal"].clone().set_position(8, 1),
            sprites["jump"].clone().set_position(4, 5),
        ]
        + [sprites["wall"].clone().set_position(x, 5) for x in (2, 3, 6, 7)],
        4,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["goal"].clone().set_position(9, 9),
            sprites["jump"].clone().set_position(2, 2),
            sprites["jump"].clone().set_position(5, 5),
            sprites["jump"].clone().set_position(7, 7),
        ],
        5,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4

_NUM_LEVELS = len(levels)


class Ju01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Ju01UI(1, _NUM_LEVELS)
        super().__init__(
            "ju01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._goal = self.current_level.get_sprites_by_tag("goal")[0]
        self._ui.update(
            int(level.get_data("difficulty") or 1),
            level_index=self.level_index,
            gs=self._state,
        )

    def _blocked(self, x: int, y: int) -> bool:
        gw, gh = self.current_level.grid_size
        if not (0 <= x < gw and 0 <= y < gh):
            return True
        sp = self.current_level.get_sprite_at(x, y, ignore_collidable=True)
        return bool(sp and "wall" in sp.tags)

    def _has_jump(self, x: int, y: int) -> bool:
        sp = self.current_level.get_sprite_at(x, y, ignore_collidable=True)
        return bool(sp and "jump" in sp.tags)

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

        if dx == 0 and dy == 0:
            self.complete_action()
            return

        x, y = self._player.x, self._player.y
        n1x, n1y = x + dx, y + dy
        if self._blocked(n1x, n1y):
            self.complete_action()
            return

        n2x, n2y = x + 2 * dx, y + 2 * dy
        if self._has_jump(n1x, n1y) and not self._blocked(n2x, n2y):
            self._player.set_position(n2x, n2y)
            self._ui.mark_skid_cell(n1x, n1y)
        else:
            self._player.set_position(n1x, n1y)

        if self._player.x == self._goal.x and self._player.y == self._goal.y:
            self.next_level()
            self._ui.update(
                int(self.current_level.get_data("difficulty") or 1),
                level_index=self.level_index,
                gs=self._state,
            )

        self.complete_action()
