"""Pipe drop: ACTION6 cycles empty / H / V straight pipe on floor; connect cyan source to yellow sink (orthogonal flow)."""

from collections import deque

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


def _r_bar(frame, h, w, win):
    if not win:
        return
    r = h - 3
    if r < 0:
        return
    for x in range(min(w, 16)):
        _rp(frame, h, w, x, r, 14)


class Pd01UI(RenderableUserDisplay):
    def __init__(self, ok: bool, level_index: int = 0, num_levels: int = 5) -> None:
        self._ok = ok
        self._level_index = level_index
        self._num_levels = num_levels
        self._end: GameState | None = None
        self._click_pos: tuple[int, int] | None = None
        self._click_frames = 0

    def update(
        self,
        ok: bool,
        *,
        level_index: int | None = None,
        num_levels: int | None = None,
        end: GameState | None = None,
    ) -> None:
        self._ok = ok
        if level_index is not None:
            self._level_index = level_index
        if num_levels is not None:
            self._num_levels = num_levels
        if end is not None:
            self._end = end

    def set_click(self, x: int, y: int) -> None:
        self._click_pos = (int(x), int(y))
        self._click_frames = 10

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        _r_dots(frame, h, w, self._level_index, self._num_levels, 0)
        frame[h - 2, 28] = 14 if self._ok else 8
        go = self._end == GameState.GAME_OVER
        win = self._end == GameState.WIN
        if go:
            for x in range(min(w, 20)):
                _rp(frame, h, w, x, h - 3, 8)
        _r_bar(frame, h, w, win)
        if self._click_pos and self._click_frames > 0:
            cx, cy = self._click_pos
            hit = 11
            for px, py in (
                (cx, cy),
                (cx - 1, cy),
                (cx + 1, cy),
                (cx, cy - 1),
                (cx, cy + 1),
            ):
                if 0 <= px < w and 0 <= py < h:
                    frame[py, px] = hit
            self._click_frames -= 1
        else:
            self._click_pos = None
        return frame


sprites = {
    "wall": Sprite(
        pixels=[[3]],
        name="wall",
        visible=True,
        collidable=True,
        tags=["wall"],
    ),
    "source": Sprite(
        pixels=[[10]],
        name="source",
        visible=True,
        collidable=False,
        tags=["source"],
    ),
    "sink": Sprite(
        pixels=[[11]],
        name="sink",
        visible=True,
        collidable=False,
        tags=["sink"],
    ),
    "pipe": Sprite(
        pixels=[[12]],
        name="pipe",
        visible=True,
        collidable=False,
        tags=["pipe"],
    ),
}


def mk(
    walls: list[tuple[int, int]],
    src: tuple[int, int],
    snk: tuple[int, int],
    d: int,
) -> Level:
    sl: list[Sprite] = [sprites["wall"].clone().set_position(wx, wy) for wx, wy in walls]
    sl.append(sprites["source"].clone().set_position(*src))
    sl.append(sprites["sink"].clone().set_position(*snk))
    return Level(sprites=sl, grid_size=(10, 10), data={"difficulty": d})


levels = [
    mk([(x, 0) for x in range(10)] + [(x, 9) for x in range(10)] + [(0, y) for y in range(10)] + [(9, y) for y in range(10)], (1, 5), (8, 5), 1),
    mk([(x, 0) for x in range(10)] + [(x, 9) for x in range(10)] + [(0, y) for y in range(10)] + [(9, y) for y in range(10)], (5, 1), (5, 8), 2),
    mk([(x, 0) for x in range(10)] + [(x, 9) for x in range(10)] + [(0, y) for y in range(10)] + [(9, y) for y in range(10)], (1, 1), (8, 8), 3),
    mk([(x, 0) for x in range(10)] + [(x, 9) for x in range(10)] + [(0, y) for y in range(10)] + [(9, y) for y in range(10)], (2, 5), (7, 5), 4),
    mk([(x, 0) for x in range(10)] + [(x, 9) for x in range(10)] + [(0, y) for y in range(10)] + [(9, y) for y in range(10)], (1, 8), (8, 1), 5),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4
DX = (0, 1, 0, -1)
DY = (-1, 0, 1, 0)


class Pd01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Pd01UI(False, 0, len(levels))
        super().__init__(
            "pd01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 6],
        )

    def _grid_to_frame_pixel(self, gx: int, gy: int) -> tuple[int, int]:
        cam = self.camera
        cw, ch = cam.width, cam.height
        scale_x = int(64 / cw)
        scale_y = int(64 / ch)
        scale = min(scale_x, scale_y)
        x_pad = int((64 - (cw * scale)) / 2)
        y_pad = int((64 - (ch * scale)) / 2)
        px = gx * scale + scale // 2 + x_pad
        py = gy * scale + scale // 2 + y_pad
        return px, py

    def on_set_level(self, level: Level) -> None:
        self._source = self.current_level.get_sprites_by_tag("source")[0]
        self._sink = self.current_level.get_sprites_by_tag("sink")[0]
        self._pipes: dict[tuple[int, int], str] = {}
        self._pipe_sprites: dict[tuple[int, int], Sprite] = {}
        self._check()

    def _wall_at(self, x: int, y: int) -> bool:
        sp = self.current_level.get_sprite_at(x, y, ignore_collidable=True)
        return bool(sp and "wall" in sp.tags)

    def _kind_at(self, x: int, y: int) -> str | None:
        if self._source.x == x and self._source.y == y:
            return "S"
        if self._sink.x == x and self._sink.y == y:
            return "K"
        return self._pipes.get((x, y))

    def _opens(self, k: str | None, di: int) -> bool:
        if k == "S" or k == "K":
            return True
        if k == "h":
            return di in (1, 3)
        if k == "v":
            return di in (0, 2)
        return False

    def _connected(self) -> bool:
        sx, sy = self._source.x, self._source.y
        tx, ty = self._sink.x, self._sink.y
        q = deque([(sx, sy)])
        seen = {(sx, sy)}
        while q:
            x, y = q.popleft()
            if x == tx and y == ty:
                return True
            for di in range(4):
                nx, ny = x + DX[di], y + DY[di]
                gw, gh = self.current_level.grid_size
                if not (0 <= nx < gw and 0 <= ny < gh):
                    continue
                if self._wall_at(nx, ny):
                    continue
                ka = self._kind_at(x, y)
                kb = self._kind_at(nx, ny)
                if not self._opens(ka, di):
                    continue
                opp = (di + 2) % 4
                if not self._opens(kb, opp):
                    continue
                if (nx, ny) not in seen:
                    seen.add((nx, ny))
                    q.append((nx, ny))
        return False

    def _check(self) -> None:
        ok = self._connected()
        self._ui.update(
            ok,
            level_index=self.level_index,
            num_levels=len(self._levels),
            end=self._state,
        )
        if ok:
            self.next_level()

    def step(self) -> None:
        if self.action.id == GameAction.ACTION6:
            raw_x = self.action.data.get("x", 0)
            raw_y = self.action.data.get("y", 0)
            g = self.camera.display_to_grid(int(raw_x), int(raw_y))
            if g is None:
                self._ui.set_click(int(raw_x), int(raw_y))
                self.complete_action()
                return
            gx, gy = g
            self._ui.set_click(*self._grid_to_frame_pixel(gx, gy))
            if self._wall_at(gx, gy):
                self.complete_action()
                return
            if (self._source.x, self._source.y) == (gx, gy) or (self._sink.x, self._sink.y) == (gx, gy):
                self.complete_action()
                return
            cur = self._pipes.get((gx, gy))
            nxt = "h" if cur is None else ("v" if cur == "h" else None)
            if cur is not None:
                sp_old = self._pipe_sprites.pop((gx, gy), None)
                if sp_old:
                    self.current_level.remove_sprite(sp_old)
            if nxt is not None:
                ps = sprites["pipe"].clone().set_position(gx, gy)
                self.current_level.add_sprite(ps)
                self._pipe_sprites[(gx, gy)] = ps
                self._pipes[(gx, gy)] = nxt
            else:
                self._pipes.pop((gx, gy), None)
            self._check()
            self.complete_action()
            return

        self.complete_action()
