"""Circuit stitch with T-junctions: **ACTION6** toggles wire; **ACTION5** tests path. Cells tagged `junction` forbid a **right turn** relative to the incoming wire direction (straight and left turns only)."""

from __future__ import annotations

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

BACKGROUND_COLOR = 5
PADDING_COLOR = 4
CAM_W = CAM_H = 24

WALL_C = 3
WIRE_C = 12
IN_C = 10
OUT_C = 11
JUNCTION_C = 13


# Unit dirs: map incoming (parent→current) to a forbidden outgoing (right turn).
_RIGHT_TURN: dict[tuple[int, int], tuple[int, int]] = {
    (0, -1): (1, 0),
    (1, 0): (0, 1),
    (0, 1): (-1, 0),
    (-1, 0): (0, -1),
}


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


class Ck02UI(RenderableUserDisplay):
    def __init__(self, ok: bool) -> None:
        self._ok = ok
        self._checks_left = 0
        self._check_cap = 1
        self._level_index = 0
        self._num_levels = 5
        self._gs: GameState | None = None

    def update(
        self,
        ok: bool,
        *,
        checks_left: int | None = None,
        check_cap: int | None = None,
        level_index: int | None = None,
        num_levels: int | None = None,
        gs: GameState | None = None,
    ) -> None:
        self._ok = ok
        if checks_left is not None:
            self._checks_left = checks_left
        if check_cap is not None:
            self._check_cap = max(1, check_cap)
        if level_index is not None:
            self._level_index = level_index
        if num_levels is not None:
            self._num_levels = num_levels
        if gs is not None:
            self._gs = gs

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        _r_dots(frame, h, w, self._level_index, self._num_levels, 0)
        frame[h - 2, 2] = 14 if self._ok else 8
        cap = min(self._check_cap, 12)
        for i in range(cap):
            col = 11 if i < self._checks_left else 3
            _rp(frame, h, w, 4 + i, h - 2, col)
        go = self._gs == GameState.GAME_OVER
        win = self._gs == GameState.WIN
        _r_bar(frame, h, w, go, win)
        return frame


sprites = {
    "wall": Sprite(
        pixels=[[WALL_C]],
        name="wall",
        visible=True,
        collidable=True,
        tags=["wall"],
    ),
    "in_port": Sprite(
        pixels=[[IN_C]],
        name="in_port",
        visible=True,
        collidable=False,
        tags=["in_port"],
    ),
    "out_port": Sprite(
        pixels=[[OUT_C]],
        name="out_port",
        visible=True,
        collidable=False,
        tags=["out_port"],
    ),
    "wire": Sprite(
        pixels=[[WIRE_C]],
        name="wire",
        visible=True,
        collidable=False,
        tags=["wire"],
    ),
    "junction": Sprite(
        pixels=[[JUNCTION_C]],
        name="junction",
        visible=True,
        collidable=False,
        tags=["junction"],
    ),
}


def mk(
    walls: list[tuple[int, int]],
    inp: tuple[int, int],
    outp: tuple[int, int],
    max_checks: int,
    diff: int,
    junctions: list[tuple[int, int]] | None = None,
) -> Level:
    sl: list[Sprite] = []
    for wx, wy in walls:
        sl.append(sprites["wall"].clone().set_position(wx, wy))
    sl.append(sprites["in_port"].clone().set_position(inp[0], inp[1]))
    sl.append(sprites["out_port"].clone().set_position(outp[0], outp[1]))
    for jx, jy in junctions or []:
        sl.append(sprites["junction"].clone().set_position(jx, jy))
    return Level(
        sprites=sl,
        grid_size=(CAM_W, CAM_H),
        data={"difficulty": diff, "max_checks": max_checks},
    )


levels = [
    mk([(x, 12) for x in range(6, 18)], (3, 12), (21, 12), 40, 1),
    mk(
        [(12, y) for y in range(24) if y != 12],
        (6, 12),
        (18, 12),
        50,
        2,
        junctions=[(12, 12)],
    ),
    mk([(x, 8) for x in range(6, 18)] + [(x, 16) for x in range(6, 18)], (3, 12), (21, 12), 60, 3),
    mk([(8, y) for y in range(24)] + [(16, y) for y in range(24)], (12, 4), (12, 20), 70, 4),
    mk(
        [(x, 12) for x in range(4, 20) if x % 3 != 1]
        + [(12, y) for y in range(4, 20) if y % 3 != 2],
        (2, 12),
        (22, 12),
        80,
        5,
    ),
]

_NUM_LEVELS = len(levels)


class Ck02(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Ck02UI(False)
        super().__init__(
            "ck02",
            levels,
            Camera(0, 0, CAM_W, CAM_H, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [5, 6],
        )

    def on_set_level(self, level: Level) -> None:
        ip = self.current_level.get_sprites_by_tag("in_port")[0]
        op = self.current_level.get_sprites_by_tag("out_port")[0]
        self._inp = (ip.x, ip.y)
        self._out = (op.x, op.y)
        cap = int(self.current_level.get_data("max_checks") or 50)
        self._check_cap = cap
        self._checks = cap
        self._junctions = {
            (s.x, s.y) for s in self.current_level.get_sprites_by_tag("junction")
        }
        self._ui.update(
            False,
            checks_left=self._checks,
            check_cap=self._check_cap,
            level_index=self.level_index,
            num_levels=_NUM_LEVELS,
            gs=self._state,
        )

    def _has_wire(self, x: int, y: int) -> bool:
        if (x, y) == self._out:
            return True
        sp = self.current_level.get_sprite_at(x, y, ignore_collidable=True)
        return sp is not None and "wire" in sp.tags

    def _reachable(self) -> bool:
        sx, sy = self._inp
        ox, oy = self._out
        gw, gh = self.current_level.grid_size
        q: deque[tuple[int, int, int, int]] = deque()
        seen: set[tuple[int, int, int, int]] = set()

        def push(nx: int, ny: int, px: int, py: int) -> bool:
            if (nx, ny) == (ox, oy):
                return True
            if not (0 <= nx < gw and 0 <= ny < gh):
                return False
            if not self._has_wire(nx, ny):
                return False
            st = (nx, ny, px, py)
            if st in seen:
                return False
            seen.add(st)
            q.append(st)
            return False

        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nx, ny = sx + dx, sy + dy
            if push(nx, ny, sx, sy):
                return True

        while q:
            x, y, px, py = q.popleft()
            inc = (x - px, y - py)
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                if (x + dx, y + dy) == (px, py):
                    continue
                nx, ny = x + dx, y + dy
                outv = (dx, dy)
                if (x, y) in self._junctions:
                    rt = _RIGHT_TURN.get(inc)
                    if rt is not None and outv == rt:
                        continue
                if (nx, ny) == (ox, oy):
                    return True
                if push(nx, ny, x, y):
                    return True
        return False

    def step(self) -> None:
        aid = self.action.id

        if aid == GameAction.ACTION5:
            if self._checks <= 0:
                self.lose()
                self._ui.update(
                    False,
                    checks_left=self._checks,
                    check_cap=self._check_cap,
                    level_index=self.level_index,
                    num_levels=_NUM_LEVELS,
                    gs=self._state,
                )
                self.complete_action()
                return
            self._checks -= 1
            ok = self._reachable()
            self._ui.update(
                ok,
                checks_left=self._checks,
                check_cap=self._check_cap,
                level_index=self.level_index,
                num_levels=_NUM_LEVELS,
                gs=self._state,
            )
            if ok:
                self.next_level()
                self._ui.update(
                    ok,
                    checks_left=self._checks,
                    check_cap=self._check_cap,
                    level_index=self.level_index,
                    num_levels=_NUM_LEVELS,
                    gs=self._state,
                )
            self.complete_action()
            return

        if aid != GameAction.ACTION6:
            self.complete_action()
            return

        x = self.action.data.get("x", 0)
        y = self.action.data.get("y", 0)
        coords = self.camera.display_to_grid(x, y)
        if coords is None:
            self.complete_action()
            return
        gx, gy = coords
        gw, gh = self.current_level.grid_size
        if not (0 <= gx < gw and 0 <= gy < gh):
            self.complete_action()
            return

        sp = self.current_level.get_sprite_at(gx, gy, ignore_collidable=True)
        if sp and ("in_port" in sp.tags or "out_port" in sp.tags or "wall" in sp.tags):
            self.complete_action()
            return

        if sp and "wire" in sp.tags:
            self.current_level.remove_sprite(sp)
            self.complete_action()
            return

        self.current_level.add_sprite(sprites["wire"].clone().set_position(gx, gy))
        self.complete_action()
