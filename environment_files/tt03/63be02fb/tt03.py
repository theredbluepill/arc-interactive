"""Like tt02 but new yellow targets may spawn every few moves (capped)."""

from __future__ import annotations

import random

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


class Tt03UI(RenderableUserDisplay):
    def __init__(self, targets_remaining: int, level_index: int = 0, num_levels: int = 3) -> None:
        self._targets = targets_remaining
        self._level_index = level_index
        self._num_levels = num_levels
        self._state: GameState | None = None
        self._target_cap = 6
        self._move_count = 0
        self._spawn_every = 10

    def update(
        self,
        targets_remaining: int,
        *,
        level_index: int | None = None,
        num_levels: int | None = None,
        state: GameState | None = None,
        target_cap: int | None = None,
        move_count: int | None = None,
        spawn_every: int | None = None,
    ) -> None:
        self._targets = targets_remaining
        if level_index is not None:
            self._level_index = level_index
        if num_levels is not None:
            self._num_levels = num_levels
        if state is not None:
            self._state = state
        if target_cap is not None:
            self._target_cap = max(1, target_cap)
        if move_count is not None:
            self._move_count = move_count
        if spawn_every is not None:
            self._spawn_every = max(1, spawn_every)

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        _r_dots(frame, h, w, self._level_index, self._num_levels, 0)
        _r_ticks(frame, h, w, self._targets)
        cap = min(6, self._target_cap)
        n = min(self._targets, cap)
        for i in range(cap):
            frame[h - 2, w - 1 - cap + i] = 11 if i < n else 5
        se = self._spawn_every
        ph = self._move_count % se
        for i in range(6):
            cx = w - 7 + i
            if cx >= 0:
                frame[h - 3, cx] = 10 if i < (ph * 6 // se) else 3
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
    "target": Sprite(
        pixels=[[11]],
        name="target",
        visible=True,
        collidable=False,
        tags=["target"],
    ),
    "wall": Sprite(
        pixels=[[3]],
        name="wall",
        visible=True,
        collidable=True,
        tags=["wall"],
    ),
    "hazard": Sprite(
        pixels=[[8]],
        name="hazard",
        visible=True,
        collidable=True,
        tags=["hazard", "patrol"],
    ),
}


def lvl(
    grid: tuple[int, int],
    sprites_list: list[Sprite],
    patrols: list[list[list[int]]],
    diff: int,
    *,
    spawn_every: int = 10,
    target_cap: int = 6,
) -> Level:
    return Level(
        sprites=sprites_list,
        grid_size=grid,
        data={
            "difficulty": diff,
            "patrols": patrols,
            "spawn_every": spawn_every,
            "target_cap": target_cap,
        },
    )


levels = [
    lvl(
        (8, 8),
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["target"].clone().set_position(2, 6),
            sprites["target"].clone().set_position(6, 2),
            sprites["wall"].clone().set_position(2, 2),
            sprites["wall"].clone().set_position(4, 4),
            sprites["hazard"].clone().set_position(5, 3),
        ],
        [[[5, 3], [6, 3], [6, 4], [5, 4], [4, 4], [4, 3]]],
        1,
    ),
    lvl(
        (16, 16),
        [
            sprites["player"].clone().set_position(2, 2),
            sprites["target"].clone().set_position(10, 10),
            sprites["target"].clone().set_position(12, 4),
            sprites["hazard"].clone().set_position(6, 6),
            sprites["hazard"].clone().set_position(10, 6),
        ]
        + [sprites["wall"].clone().set_position(8, y) for y in range(16) if y != 7],
        [
            [[6, 6], [7, 6], [8, 6], [9, 6], [9, 7], [9, 8], [8, 8], [7, 8], [6, 8], [6, 7]],
            [[10, 6], [11, 6], [12, 6], [12, 7], [12, 8], [11, 8], [10, 8], [10, 7]],
        ],
        2,
    ),
    lvl(
        (24, 24),
        [
            sprites["player"].clone().set_position(3, 3),
            sprites["target"].clone().set_position(20, 20),
            sprites["target"].clone().set_position(15, 8),
            sprites["target"].clone().set_position(8, 18),
            sprites["hazard"].clone().set_position(12, 12),
        ],
        [[[12, 12], [13, 12], [14, 12], [14, 13], [14, 14], [13, 14], [12, 14], [12, 13]]],
        3,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Tt03(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Tt03UI(0)
        super().__init__(
            "tt03",
            levels,
            Camera(0, 0, 24, 24, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._targets = self.current_level.get_sprites_by_tag("target")
        paths = self.current_level.get_data("patrols") or []
        haz = [s for s in self.current_level.get_sprites_by_tag("patrol")]
        self._patrol_hazards: list[tuple[Sprite, list[tuple[int, int]], int]] = []
        for i, s in enumerate(haz):
            loop = paths[i] if i < len(paths) else [[s.x, s.y]]
            pts = [(int(p[0]), int(p[1])) for p in loop]
            self._patrol_hazards.append((s, pts, 0))
        self._spawn_every = int(self.current_level.get_data("spawn_every") or 10)
        self._target_cap = int(self.current_level.get_data("target_cap") or 6)
        self._move_count = 0
        self._sync_tt_ui()

    def _sync_tt_ui(self) -> None:
        self._ui.update(
            len(self._targets),
            level_index=self.level_index,
            num_levels=len(levels),
            state=self._state,
            target_cap=self._target_cap,
            move_count=self._move_count,
            spawn_every=self._spawn_every,
        )

    def _maybe_spawn_target(self) -> None:
        if len(self._targets) >= self._target_cap:
            return
        gw, gh = self.current_level.grid_size
        opts: list[tuple[int, int]] = []
        for x in range(gw):
            for y in range(gh):
                sp = self.current_level.get_sprite_at(x, y, ignore_collidable=True)
                if sp and (
                    "wall" in sp.tags
                    or "hazard" in sp.tags
                    or "target" in sp.tags
                ):
                    continue
                if not sp or not sp.is_collidable:
                    opts.append((x, y))
        if not opts:
            return
        sx, sy = random.choice(opts)
        t = sprites["target"].clone().set_position(sx, sy)
        self.current_level.add_sprite(t)
        self._targets.append(t)
        self._sync_tt_ui()

    def _advance_patrols(self) -> None:
        for i, (sp, pts, idx) in enumerate(self._patrol_hazards):
            if not pts:
                continue
            nidx = (idx + 1) % len(pts)
            nx, ny = pts[nidx]
            sp.set_position(nx, ny)
            self._patrol_hazards[i] = (sp, pts, nidx)

    def step(self) -> None:
        dx = dy = 0
        moved = False

        if self.action.id.value == 1:
            dy = -1
            moved = True
        elif self.action.id.value == 2:
            dy = 1
            moved = True
        elif self.action.id.value == 3:
            dx = -1
            moved = True
        elif self.action.id.value == 4:
            dx = 1
            moved = True

        if not moved:
            self.complete_action()
            return

        new_x = self._player.x + dx
        new_y = self._player.y + dy

        grid_w, grid_h = self.current_level.grid_size
        if 0 <= new_x < grid_w and 0 <= new_y < grid_h:
            sprite = self.current_level.get_sprite_at(
                new_x, new_y, ignore_collidable=True
            )

            if sprite and "target" in sprite.tags:
                self.current_level.remove_sprite(sprite)
                self._targets.remove(sprite)
                self._player.set_position(new_x, new_y)
                self._sync_tt_ui()
            elif not sprite or not sprite.is_collidable:
                self._player.set_position(new_x, new_y)
            elif sprite and "hazard" in sprite.tags:
                self.complete_action()
                return

        self._advance_patrols()

        self._move_count += 1
        if self._spawn_every > 0 and self._move_count % self._spawn_every == 0:
            self._maybe_spawn_target()

        px, py = self._player.x, self._player.y
        hit = self.current_level.get_sprite_at(px, py, ignore_collidable=True)
        if hit and "hazard" in hit.tags:
            self.lose()
            self._sync_tt_ui()
            self.complete_action()
            return

        if len(self._targets) == 0:
            self.next_level()

        self._sync_tt_ui()
        self.complete_action()
