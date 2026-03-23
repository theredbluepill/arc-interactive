"""Circuit stitch: **ACTION6** toggles wire; **ACTION5** tests path. Junctions forbid a **right turn** relative to incoming wire. **Checkpoint** cells (cyan) must lie on any successful test path."""

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
CHECKPOINT_C = 10

TEST_FX_FRAMES = 14
PATH_OK_C = 14
PATH_FAIL_C = 6


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


State5 = tuple[int, int, int, int, bool]


class Ck03UI(RenderableUserDisplay):
    def __init__(self, ok: bool, num_levels: int) -> None:
        self._ok = ok
        self._checks_left = 0
        self._check_cap = 1
        self._level_index = 0
        self._num_levels = num_levels
        self._gs: GameState | None = None
        self._grid_w = CAM_W
        self._grid_h = CAM_H
        self._path_ok: set[tuple[int, int]] = set()
        self._path_fail: set[tuple[int, int]] = set()
        self._test_fx_frames = 0

    def update(
        self,
        ok: bool,
        *,
        checks_left: int | None = None,
        check_cap: int | None = None,
        level_index: int | None = None,
        num_levels: int | None = None,
        gs: GameState | None = None,
        grid_wh: tuple[int, int] | None = None,
        path_ok: set[tuple[int, int]] | None = None,
        path_fail: set[tuple[int, int]] | None = None,
        test_fx_frames: int | None = None,
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
        if grid_wh is not None:
            self._grid_w, self._grid_h = grid_wh
        if path_ok is not None:
            self._path_ok = path_ok
        if path_fail is not None:
            self._path_fail = path_fail
        if test_fx_frames is not None:
            self._test_fx_frames = test_fx_frames

    @staticmethod
    def _paint_cell(
        frame, fh: int, fw: int, gx: int, gy: int, gw: int, gh: int, color: int
    ) -> None:
        scale_x = 64 // gw
        scale_y = 64 // gh
        scale = min(scale_x, scale_y)
        x_pad = (fw - (gw * scale)) // 2
        y_pad = (fh - (gh * scale)) // 2
        x0 = x_pad + gx * scale
        y0 = y_pad + gy * scale
        for sy in range(scale):
            for sx in range(scale):
                fx, fy = x0 + sx, y0 + sy
                if 0 <= fx < fw and 0 <= fy < fh:
                    frame[fy, fx] = color

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        gw, gh = self._grid_w, self._grid_h
        if self._test_fx_frames > 0:
            for cell in self._path_fail:
                self._paint_cell(frame, h, w, cell[0], cell[1], gw, gh, PATH_FAIL_C)
            for cell in self._path_ok:
                self._paint_cell(frame, h, w, cell[0], cell[1], gw, gh, PATH_OK_C)
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
    "checkpoint": Sprite(
        pixels=[[CHECKPOINT_C]],
        name="checkpoint",
        visible=True,
        collidable=False,
        tags=["checkpoint"],
    ),
}


def mk(
    walls: list[tuple[int, int]],
    inp: tuple[int, int],
    outp: tuple[int, int],
    max_checks: int,
    diff: int,
    junctions: list[tuple[int, int]] | None = None,
    checkpoints: list[tuple[int, int]] | None = None,
) -> Level:
    sl: list[Sprite] = []
    for wx, wy in walls:
        sl.append(sprites["wall"].clone().set_position(wx, wy))
    sl.append(sprites["in_port"].clone().set_position(inp[0], inp[1]))
    sl.append(sprites["out_port"].clone().set_position(outp[0], outp[1]))
    for jx, jy in junctions or []:
        sl.append(sprites["junction"].clone().set_position(jx, jy))
    for cx, cy in checkpoints or []:
        sl.append(sprites["checkpoint"].clone().set_position(cx, cy))
    return Level(
        sprites=sl,
        grid_size=(CAM_W, CAM_H),
        data={"difficulty": diff, "max_checks": max_checks},
    )


levels = [
    mk([(x, 12) for x in range(6, 18)], (3, 12), (21, 12), 40, 1, checkpoints=[(5, 12)]),
    mk(
        [(12, y) for y in range(24) if y != 12],
        (6, 12),
        (18, 12),
        50,
        2,
        junctions=[(12, 12)],
        checkpoints=[(10, 12)],
    ),
    mk(
        [(x, 8) for x in range(6, 18)] + [(x, 16) for x in range(6, 18)],
        (3, 12),
        (21, 12),
        60,
        3,
        checkpoints=[(12, 10)],
    ),
    mk(
        [(8, y) for y in range(24)] + [(16, y) for y in range(24)],
        (12, 4),
        (12, 20),
        70,
        4,
        checkpoints=[(12, 12)],
    ),
    mk(
        [(x, 12) for x in range(4, 20) if x % 3 != 1]
        + [(12, y) for y in range(4, 20) if y % 3 != 2],
        (2, 12),
        (22, 12),
        80,
        5,
        checkpoints=[(8, 12)],
    ),
]

_NUM_LEVELS = len(levels)


class Ck03(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Ck03UI(False, _NUM_LEVELS)
        self._test_fx_frames = 0
        self._path_ok: set[tuple[int, int]] = set()
        self._path_fail: set[tuple[int, int]] = set()
        super().__init__(
            "ck03",
            levels,
            Camera(0, 0, CAM_W, CAM_H, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 5, 6],
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
        self._checkpoint_cells = {
            (s.x, s.y) for s in self.current_level.get_sprites_by_tag("checkpoint")
        }
        self._test_fx_frames = 0
        self._path_ok = set()
        self._path_fail = set()
        self._last_test_ok = False
        self._sync_ui(False)

    def _has_wire(self, x: int, y: int) -> bool:
        if (x, y) == self._out:
            return True
        if (x, y) in self._checkpoint_cells:
            return True
        sp = self.current_level.get_sprite_at(x, y, ignore_collidable=True)
        return sp is not None and "wire" in sp.tags

    def _probe_path(self) -> tuple[bool, set[tuple[int, int]], set[tuple[int, int]]]:
        """Return (success, success_path_cells, explored_cells)."""
        sx, sy = self._inp
        ox, oy = self._out
        gw, gh = self.current_level.grid_size
        require_cp = bool(self._checkpoint_cells)

        q: deque[State5] = deque()
        seen: set[State5] = set()
        parent: dict[State5, State5 | None] = {}
        explored_xy: set[tuple[int, int]] = set()

        def try_goal(
            nx: int, ny: int, px: int, py: int, hit_cp: bool
        ) -> State5 | None:
            if (nx, ny) != (ox, oy):
                return None
            nh = hit_cp or ((nx, ny) in self._checkpoint_cells)
            if require_cp and not nh:
                return None
            return (nx, ny, px, py, nh)

        def add_state(
            nx: int,
            ny: int,
            px: int,
            py: int,
            hit_cp: bool,
            prev: State5 | None,
        ) -> State5 | None:
            if not (0 <= nx < gw and 0 <= ny < gh):
                return None
            if not self._has_wire(nx, ny):
                return None
            nh = hit_cp or ((nx, ny) in self._checkpoint_cells)
            st: State5 = (nx, ny, px, py, nh)
            if st in seen:
                return None
            seen.add(st)
            explored_xy.add((nx, ny))
            parent[st] = prev
            q.append(st)
            return st

        goal: State5 | None = None

        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nx, ny = sx + dx, sy + dy
            h0 = (nx, ny) in self._checkpoint_cells
            tg = try_goal(nx, ny, sx, sy, h0)
            if tg is not None:
                goal = tg
                parent[tg] = None
                break
            add_state(nx, ny, sx, sy, h0, None)

        while q and goal is None:
            x, y, px, py, hit_cp = q.popleft()
            cur: State5 = (x, y, px, py, hit_cp)
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
                nh = hit_cp or ((nx, ny) in self._checkpoint_cells)
                tg = try_goal(nx, ny, x, y, nh)
                if tg is not None:
                    goal = tg
                    parent[tg] = cur
                    break
                add_state(nx, ny, x, y, hit_cp, cur)

        if goal is None:
            return False, set(), explored_xy

        path_cells: set[tuple[int, int]] = set()
        g: State5 | None = goal
        while g is not None:
            path_cells.add((g[0], g[1]))
            g = parent.get(g)
        path_cells.add((sx, sy))
        return True, path_cells, explored_xy

    def _sync_ui(self, ok: bool | None = None) -> None:
        if ok is None:
            ok = self._last_test_ok
        gw, gh = self.current_level.grid_size
        self._ui.update(
            ok,
            checks_left=self._checks,
            check_cap=self._check_cap,
            level_index=self.level_index,
            num_levels=_NUM_LEVELS,
            gs=self._state,
            grid_wh=(gw, gh),
            path_ok=set(self._path_ok),
            path_fail=set(self._path_fail),
            test_fx_frames=self._test_fx_frames,
        )

    def step(self) -> None:
        if self._test_fx_frames > 0:
            self._test_fx_frames -= 1
            if self._test_fx_frames == 0:
                self._path_ok.clear()
                self._path_fail.clear()
            self._sync_ui()

        aid = self.action.id

        if aid in (
            GameAction.ACTION1,
            GameAction.ACTION2,
            GameAction.ACTION3,
            GameAction.ACTION4,
        ):
            self._sync_ui()
            self.complete_action()
            return

        if aid == GameAction.ACTION5:
            if self._checks <= 0:
                self.lose()
                self._last_test_ok = False
                self._sync_ui(False)
                self.complete_action()
                return
            self._checks -= 1
            ok, path_ok, explored = self._probe_path()
            self._last_test_ok = ok
            self._path_ok = path_ok if ok else set()
            self._path_fail = explored if not ok else set()
            self._test_fx_frames = TEST_FX_FRAMES
            self._sync_ui(ok)
            if ok:
                self.next_level()
            self.complete_action()
            return

        if aid != GameAction.ACTION6:
            self._sync_ui()
            self.complete_action()
            return

        x = self.action.data.get("x", 0)
        y = self.action.data.get("y", 0)
        coords = self.camera.display_to_grid(x, y)
        if coords is None:
            self._sync_ui()
            self.complete_action()
            return
        gx, gy = coords
        gw, gh = self.current_level.grid_size
        if not (0 <= gx < gw and 0 <= gy < gh):
            self._sync_ui()
            self.complete_action()
            return

        sp = self.current_level.get_sprite_at(gx, gy, ignore_collidable=True)
        if sp and ("in_port" in sp.tags or "out_port" in sp.tags or "wall" in sp.tags):
            self._sync_ui()
            self.complete_action()
            return

        if sp and "checkpoint" in sp.tags:
            self._sync_ui()
            self.complete_action()
            return

        if sp and "wire" in sp.tags:
            self.current_level.remove_sprite(sp)
            self._sync_ui()
            self.complete_action()
            return

        self.current_level.add_sprite(sprites["wire"].clone().set_position(gx, gy))
        self._sync_ui()
        self.complete_action()
