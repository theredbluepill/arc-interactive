"""Escort: NPC steps one cell toward you each turn; both you and the NPC must reach their goals."""

from arcengine import (
    ARCBaseGame,
    Camera,
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


class Es01UI(RenderableUserDisplay):
    def __init__(self, d: int, level_index: int = 0, num_levels: int = 5) -> None:
        self._d = d
        self._level_index = level_index
        self._num_levels = num_levels
        self._end: GameState | None = None

    def update(
        self,
        d: int,
        *,
        level_index: int | None = None,
        num_levels: int | None = None,
        end: GameState | None = None,
    ) -> None:
        self._d = d
        if level_index is not None:
            self._level_index = level_index
        if num_levels is not None:
            self._num_levels = num_levels
        if end is not None:
            self._end = end

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        _r_dots(frame, h, w, self._level_index, self._num_levels, 0)
        for i in range(min(self._d, 8)):
            frame[h - 2, 20 + i] = 7
        go = self._end == GameState.GAME_OVER
        win = self._end == GameState.WIN
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
    "npc": Sprite(
        pixels=[[6]],
        name="npc",
        visible=True,
        collidable=True,
        tags=["npc"],
    ),
    "goal_p": Sprite(
        pixels=[[14]],
        name="goal_p",
        visible=True,
        collidable=False,
        tags=["goal", "player_goal"],
    ),
    "goal_n": Sprite(
        pixels=[[10]],
        name="goal_n",
        visible=True,
        collidable=False,
        tags=["goal", "npc_goal"],
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


levels = [
    mk(
        [
            sprites["player"].clone().set_position(1, 5),
            sprites["npc"].clone().set_position(8, 5),
            sprites["goal_p"].clone().set_position(3, 5),
            sprites["goal_n"].clone().set_position(6, 5),
        ],
        1,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 5),
            sprites["npc"].clone().set_position(9, 5),
            sprites["goal_p"].clone().set_position(2, 5),
            sprites["goal_n"].clone().set_position(7, 5),
        ],
        2,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["npc"].clone().set_position(8, 8),
            sprites["goal_p"].clone().set_position(4, 1),
            sprites["goal_n"].clone().set_position(5, 8),
        ],
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(2, 5),
            sprites["npc"].clone().set_position(7, 5),
            sprites["goal_p"].clone().set_position(4, 5),
            sprites["goal_n"].clone().set_position(5, 5),
            sprites["wall"].clone().set_position(5, 4),
            sprites["wall"].clone().set_position(5, 6),
        ],
        4,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["npc"].clone().set_position(9, 9),
            sprites["goal_p"].clone().set_position(8, 0),
            sprites["goal_n"].clone().set_position(1, 9),
        ],
        5,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Es01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Es01UI(1, 0, len(levels))
        super().__init__(
            "es01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._npc = self.current_level.get_sprites_by_tag("npc")[0]
        self._goal_p = [s for s in self.current_level.get_sprites_by_tag("goal") if "player_goal" in s.tags][0]
        self._goal_n = [s for s in self.current_level.get_sprites_by_tag("goal") if "npc_goal" in s.tags][0]
        self._ui.update(
            int(level.get_data("difficulty") or 1),
            level_index=self.level_index,
            num_levels=len(self._levels),
            end=self._state,
        )

    def _blocked(self, x: int, y: int, ignore: Sprite | None = None) -> bool:
        gw, gh = self.current_level.grid_size
        if not (0 <= x < gw and 0 <= y < gh):
            return True
        sp = self.current_level.get_sprite_at(x, y, ignore_collidable=True)
        if sp is ignore:
            return False
        if not sp:
            return False
        if "goal" in sp.tags:
            return False
        return sp.is_collidable

    def _move_npc(self) -> None:
        px, py = self._player.x, self._player.y
        nx, ny = self._npc.x, self._npc.y
        cand: list[tuple[int, int]] = []
        if px > nx:
            cand.append((nx + 1, ny))
        elif px < nx:
            cand.append((nx - 1, ny))
        if py > ny:
            cand.append((nx, ny + 1))
        elif py < ny:
            cand.append((nx, ny - 1))
        for tx, ty in cand:
            if not self._blocked(tx, ty, ignore=self._npc):
                self._npc.set_position(tx, ty)
                return

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
        if sp and "npc" in sp.tags:
            self.complete_action()
            return

        if not sp or not sp.is_collidable:
            self._player.set_position(nx, ny)

        self._move_npc()

        if self._npc.x == self._player.x and self._npc.y == self._player.y:
            self.lose()
            self._ui.update(
                int(self.current_level.get_data("difficulty") or 1),
                end=self._state,
            )
            self.complete_action()
            return

        on_p = self._player.x == self._goal_p.x and self._player.y == self._goal_p.y
        on_n = self._npc.x == self._goal_n.x and self._npc.y == self._goal_n.y
        if on_p and on_n:
            self.next_level()

        self._ui.update(
            int(self.current_level.get_data("difficulty") or 1),
            end=self._state,
        )
        self.complete_action()
