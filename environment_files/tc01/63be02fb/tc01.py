"""Conveyor layer: after each move the player is pushed one more step by the arrow at the **destination** cell (`arrows` in level data)."""

from __future__ import annotations

from arcengine import (
    ARCBaseGame,
    Camera,
    GameState,
    Level,
    RenderableUserDisplay,
    Sprite,
)

BACKGROUND_COLOR = 5
PADDING_COLOR = 4
CAM = 16

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


def _r_ticks(frame, h, w, n, y=None):
    row = (h - 1) if y is None else y
    for i in range(max(0, min(n, 8))):
        _rp(frame, h, w, 1 + i, row, 11)


def _r_bar(frame, h, w, game_over, win):
    if not (game_over or win):
        return
    r = h - 3
    if r < 0:
        return
    c = 14 if win else 8
    for x in range(min(w, 16)):
        _rp(frame, h, w, x, r, c)


class Tc01UI(RenderableUserDisplay):
    def __init__(
        self,
        goal_pending: int = 1,
        level_index: int = 0,
        num_levels: int = 5,
    ) -> None:
        self._goal_pending = goal_pending
        self._level_index = level_index
        self._num_levels = num_levels
        self._state: GameState | None = None

    def update(
        self,
        goal_pending: int,
        *,
        level_index: int | None = None,
        num_levels: int | None = None,
        state: GameState | None = None,
    ) -> None:
        self._goal_pending = goal_pending
        if level_index is not None:
            self._level_index = level_index
        if num_levels is not None:
            self._num_levels = num_levels
        if state is not None:
            self._state = state

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        _r_dots(frame, h, w, self._level_index, self._num_levels, 0)
        _r_ticks(frame, h, w, self._goal_pending)
        go = self._state == GameState.GAME_OVER
        win = self._state == GameState.WIN
        _r_bar(frame, h, w, go, win)
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
    "arrow": Sprite(
        pixels=[[10]],
        name="arrow",
        visible=True,
        collidable=False,
        tags=["arrow"],
    ),
}

# Distinct hues per conveyor direction (discoverability); see level data `arrows`.
_ARROW_COLOR: dict[tuple[int, int], int] = {
    (1, 0): 10,
    (-1, 0): 7,
    (0, -1): 11,
    (0, 1): 9,
}


def mk(
    p: tuple[int, int],
    g: tuple[int, int],
    walls: list[tuple[int, int]],
    arrows: dict[str, tuple[int, int]],
    diff: int,
) -> Level:
    sl = [
        sprites["player"].clone().set_position(*p),
        sprites["goal"].clone().set_position(*g),
    ]
    for wx, wy in walls:
        sl.append(sprites["wall"].clone().set_position(wx, wy))
    for key, (dx, dy) in arrows.items():
        parts = key.split(",")
        ax, ay = int(parts[0]), int(parts[1])
        hue = _ARROW_COLOR.get((dx, dy), 10)
        sl.append(
            Sprite(
                pixels=[[hue]],
                name="arrow",
                visible=True,
                collidable=False,
                tags=["arrow"],
            ).set_position(ax, ay),
        )
    ser = {k: list(v) for k, v in arrows.items()}
    return Level(
        sprites=sl,
        grid_size=(CAM, CAM),
        data={"difficulty": diff, "arrows": ser},
    )


def _key(x: int, y: int) -> str:
    return f"{x},{y}"


levels = [
    mk((2, 8), (14, 8), [], {_key(3, 8): (1, 0), _key(5, 8): (0, -1)}, 1),
    mk((1, 1), (14, 14), [(8, y) for y in range(16) if y != 8], {_key(2, 2): (1, 0)}, 2),
    mk((0, 8), (15, 8), [], {_key(x, 8): (1, 0) for x in range(1, 15)}, 3),
    mk((4, 4), (12, 12), [], {_key(5, 4): (0, 1), _key(5, 10): (1, 0)}, 4),
    mk((2, 2), (13, 13), [(6, y) for y in range(16)], {_key(7, 8): (1, 0)}, 5),
]


class Tc01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Tc01UI(1)
        super().__init__(
            "tc01",
            levels,
            Camera(0, 0, CAM, CAM, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        raw = self.current_level.get_data("arrows") or {}
        self._arrows: dict[str, tuple[int, int]] = {
            k: tuple(int(t) for t in v) for k, v in raw.items()
        }
        self._ui.update(
            1,
            level_index=self.level_index,
            num_levels=len(levels),
            state=self._state,
        )

    def _push_conveyor(self) -> None:
        x, y = self._player.x, self._player.y
        key = _key(x, y)
        if key not in self._arrows:
            return
        dx, dy = self._arrows[key]
        nx, ny = x + dx, y + dy
        gw, gh = self.current_level.grid_size
        if not (0 <= nx < gw and 0 <= ny < gh):
            return
        sp = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
        if sp and "wall" in sp.tags:
            return
        self._player.set_position(nx, ny)

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
        if 0 <= nx < gw and 0 <= ny < gh:
            sp = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
            if not sp or "wall" not in sp.tags:
                self._player.set_position(nx, ny)

        self._push_conveyor()

        gl = self.current_level.get_sprites_by_tag("goal")[0]
        on_goal = self._player.x == gl.x and self._player.y == gl.y
        if on_goal:
            self.next_level()

        self._ui.update(
            0 if on_goal else 1,
            level_index=self.level_index,
            num_levels=len(levels),
            state=self._state,
        )
        self.complete_action()
