"""Numberlink-lite: draw a path between numbered endpoints using exactly L cells (including endpoints); no overlap. ACTION6 uses display click on the grid (not player position)."""

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


class Fl01UI(RenderableUserDisplay):
    def __init__(self, cur: int, need: int, num_levels: int) -> None:
        self._cur = cur
        self._need = need
        self._num_levels = num_levels
        self._level_index = 0
        self._gs: GameState | None = None

    def update(
        self,
        cur: int,
        need: int,
        *,
        level_index: int | None = None,
        gs: GameState | None = None,
    ) -> None:
        self._cur = cur
        self._need = need
        if level_index is not None:
            self._level_index = level_index
        if gs is not None:
            self._gs = gs

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        _r_dots(frame, h, w, self._level_index, self._num_levels, 0)
        # Target path length (exact cells, including endpoints): one tick per required cell.
        for i in range(min(self._need, 20)):
            frame[h - 3, 1 + i] = 13
        # Current drawn path length (same units).
        for i in range(min(self._cur, 20)):
            frame[h - 2, 1 + i] = 10
        go = self._gs == GameState.GAME_OVER
        win = self._gs == GameState.WIN
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
    "a": Sprite(
        pixels=[[11]],
        name="a",
        visible=True,
        collidable=False,
        tags=["endpoint", "a"],
    ),
    "b": Sprite(
        pixels=[[11]],
        name="b",
        visible=True,
        collidable=False,
        tags=["endpoint", "b"],
    ),
    "path": Sprite(
        pixels=[[10]],
        name="path",
        visible=True,
        collidable=False,
        tags=["path_px"],
    ),
    "wall": Sprite(
        pixels=[[3]],
        name="wall",
        visible=True,
        collidable=True,
        tags=["wall"],
    ),
}


def mk(sl, need_len: int, d: int):
    return Level(
        sprites=sl,
        grid_size=(12, 12),
        data={"difficulty": d, "path_length": need_len},
    )


levels = [
    mk(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["a"].clone().set_position(1, 1),
            sprites["b"].clone().set_position(1, 5),
        ],
        6,
        1,
    ),
    mk(
        [
            sprites["player"].clone().set_position(2, 2),
            sprites["a"].clone().set_position(2, 2),
            sprites["b"].clone().set_position(8, 2),
        ],
        9,
        2,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["a"].clone().set_position(0, 0),
            sprites["b"].clone().set_position(5, 5),
        ]
        + [sprites["wall"].clone().set_position(3, y) for y in range(6)],
        12,
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(6, 6),
            sprites["a"].clone().set_position(6, 6),
            sprites["b"].clone().set_position(6, 0),
        ],
        8,
        4,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 5),
            sprites["a"].clone().set_position(1, 5),
            sprites["b"].clone().set_position(10, 5),
        ],
        14,
        5,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4

_NUM_LEVELS = len(levels)


class Fl01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Fl01UI(0, 1, _NUM_LEVELS)
        super().__init__(
            "fl01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 6],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._need = int(self.current_level.get_data("path_length") or 6)
        self._path: list[tuple[int, int]] = []
        self._clear_path_sprites()
        self._ui.update(0, self._need, level_index=self.level_index, gs=self._state)

    def _clear_path_sprites(self) -> None:
        for s in list(self.current_level.get_sprites_by_tag("path_px")):
            self.current_level.remove_sprite(s)

    def _endpoints(self) -> tuple[tuple[int, int], tuple[int, int]]:
        aa = self.current_level.get_sprites_by_tag("a")[0]
        bb = self.current_level.get_sprites_by_tag("b")[0]
        return (aa.x, aa.y), (bb.x, bb.y)

    def _redraw_path(self) -> None:
        self._clear_path_sprites()
        for x, y in self._path:
            if (x, y) in (self._endpoints()):
                continue
            self.current_level.add_sprite(sprites["path"].clone().set_position(x, y))
        self._ui.update(
            len(self._path),
            self._need,
            level_index=self.level_index,
            gs=self._state,
        )

    def step(self) -> None:
        if self.action.id == GameAction.ACTION6:
            px = int(self.action.data.get("x", 0))
            py = int(self.action.data.get("y", 0))
            coords = self.camera.display_to_grid(px, py)
            if coords is None:
                self.complete_action()
                return
            gx, gy = int(coords[0]), int(coords[1])
            gw, gh = self.current_level.grid_size
            if not (0 <= gx < gw and 0 <= gy < gh):
                self.complete_action()
                return
            epa, epb = self._endpoints()
            if not self._path:
                if (gx, gy) == epa or (gx, gy) == epb:
                    self._path.append((gx, gy))
                    self._redraw_path()
            else:
                last = self._path[-1]
                if abs(gx - last[0]) + abs(gy - last[1]) != 1:
                    self.complete_action()
                    return
                if (gx, gy) in self._path:
                    self.complete_action()
                    return
                sp = self.current_level.get_sprite_at(gx, gy, ignore_collidable=True)
                if sp and "wall" in sp.tags:
                    self.complete_action()
                    return
                self._path.append((gx, gy))
                self._redraw_path()
                ends = {epa, epb}
                if len(self._path) == self._need and set(self._path) >= ends:
                    self.next_level()
            self.complete_action()
            return

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
            if not sp or not sp.is_collidable:
                self._player.set_position(nx, ny)

        self.complete_action()
