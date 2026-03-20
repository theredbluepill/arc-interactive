"""Relay pulse: place relays; ACTION5 fires a pulse from the source that spreads only through relay tiles and lights adjacent lamps."""

from __future__ import annotations

from collections import deque

from arcengine import (
    ARCBaseGame,
    Camera,
    GameAction,
    Level,
    RenderableUserDisplay,
    Sprite,
)

BACKGROUND_COLOR = 5
PADDING_COLOR = 4
CAM_W = CAM_H = 32

WALL_C = 3
RELAY_C = 10
SRC_C = 14
LAMP_C = 11

# Sub-frames after ACTION5 so the pulse reads in play / GIFs (one env.step may run many renders).
PULSE_FRAMES = 10
PULSE_RELAY_BRIGHT = 7
PULSE_RING = 10
PULSE_LAMP_FLASH = 1


class Rp01UI(RenderableUserDisplay):
    PULSE_FRAMES = PULSE_FRAMES

    def __init__(self, relays_left: int, fires_left: int) -> None:
        self._relays = relays_left
        self._fires = fires_left
        self._pulse_phase: int | None = None
        self._pulse_seen: set[tuple[int, int]] = set()
        self._pulse_lit: set[tuple[int, int]] = set()
        self._pulse_hop: dict[tuple[int, int], int] = {}
        self._pulse_src: tuple[int, int] = (0, 0)

    def update(self, relays_left: int, fires_left: int) -> None:
        self._relays = relays_left
        self._fires = fires_left

    def clear_pulse(self) -> None:
        self._pulse_phase = None
        self._pulse_seen = set()
        self._pulse_lit = set()
        self._pulse_hop = {}

    def begin_pulse(
        self,
        seen: set[tuple[int, int]],
        lit: set[tuple[int, int]],
        src: tuple[int, int],
        hop: dict[tuple[int, int], int],
    ) -> None:
        self._pulse_seen = set(seen)
        self._pulse_lit = set(lit)
        self._pulse_src = src
        self._pulse_hop = dict(hop)
        self._pulse_phase = 0

    def set_pulse_phase(self, phase: int) -> None:
        self._pulse_phase = phase

    def _cell_rect(
        self, gx: int, gy: int
    ) -> tuple[int, int, int, int] | None:
        scale = min(64 // CAM_W, 64 // CAM_H)
        x_pad = (64 - CAM_W * scale) // 2
        y_pad = (64 - CAM_H * scale) // 2
        if not (0 <= gx < CAM_W and 0 <= gy < CAM_H):
            return None
        x0 = gx * scale + x_pad
        y0 = gy * scale + y_pad
        return x0, y0, scale, scale

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for i in range(min(self._relays, 24)):
            frame[h - 2, 1 + i] = 12
        for i in range(min(self._fires, 8)):
            frame[h - 1, 1 + i] = 9

        if self._pulse_phase is not None:
            ph = self._pulse_phase
            sx, sy = self._pulse_src
            max_hop = max(self._pulse_hop.values(), default=-1)

            for gx, gy in self._pulse_seen:
                d = self._pulse_hop.get((gx, gy), 0)
                if d <= ph:
                    rect = self._cell_rect(gx, gy)
                    if rect is not None:
                        x0, y0, cw, ch = rect
                        c = PULSE_RELAY_BRIGHT if (ph + gx + gy) % 2 == 0 else PULSE_RING
                        frame[y0 : y0 + ch, x0 : x0 + cw] = c

            ring_r = ph + 1
            for gx in range(CAM_W):
                for gy in range(CAM_H):
                    if max(abs(gx - sx), abs(gy - sy)) != ring_r:
                        continue
                    rect = self._cell_rect(gx, gy)
                    if rect is None:
                        continue
                    x0, y0, cw, ch = rect
                    cur = int(frame[y0 + ch // 2, x0 + cw // 2])
                    if cur == BACKGROUND_COLOR or cur == PADDING_COLOR:
                        frame[y0 : y0 + ch, x0 : x0 + cw] = (
                            PULSE_RING if ph % 2 == 0 else PULSE_RELAY_BRIGHT
                        )

            if self._pulse_lit and ph >= max_hop:
                for lx, ly in self._pulse_lit:
                    rect = self._cell_rect(lx, ly)
                    if rect is None:
                        continue
                    x0, y0, cw, ch = rect
                    flash = PULSE_LAMP_FLASH if (ph + max_hop) % 2 == 0 else LAMP_C
                    frame[y0 : y0 + ch, x0 : x0 + cw] = flash

        return frame


sprites = {
    "wall": Sprite(
        pixels=[[WALL_C]],
        name="wall",
        visible=True,
        collidable=True,
        tags=["wall"],
    ),
    "source": Sprite(
        pixels=[[SRC_C]],
        name="source",
        visible=True,
        collidable=False,
        tags=["source"],
    ),
    "lamp": Sprite(
        pixels=[[LAMP_C]],
        name="lamp",
        visible=True,
        collidable=False,
        tags=["lamp"],
    ),
    "relay": Sprite(
        pixels=[[RELAY_C]],
        name="relay",
        visible=True,
        collidable=False,
        tags=["relay"],
    ),
}


def mk(
    grid: tuple[int, int],
    walls: list[tuple[int, int]],
    source: tuple[int, int],
    lamps: list[tuple[int, int]],
    max_relays: int,
    max_fires: int,
    diff: int,
) -> Level:
    sl: list[Sprite] = []
    for wx, wy in walls:
        sl.append(sprites["wall"].clone().set_position(wx, wy))
    sl.append(sprites["source"].clone().set_position(source[0], source[1]))
    for lx, ly in lamps:
        sl.append(sprites["lamp"].clone().set_position(lx, ly))
    return Level(
        sprites=sl,
        grid_size=grid,
        data={
            "difficulty": diff,
            "max_relays": max_relays,
            "max_fires": max_fires,
        },
    )


levels = [
    mk(
        (32, 32),
        [],
        (4, 16),
        [(28, 16)],
        40,
        12,
        1,
    ),
    mk(
        (32, 32),
        [(16, y) for y in range(32) if abs(y - 16) > 2],
        (2, 16),
        [(30, 16), (16, 4)],
        50,
        15,
        2,
    ),
    mk(
        (32, 32),
        [(x, 10) for x in range(8, 24)] + [(x, 22) for x in range(8, 24)],
        (4, 4),
        [(28, 28), (28, 4), (4, 28)],
        70,
        18,
        3,
    ),
    mk(
        (32, 32),
        [(12, y) for y in range(32) if y % 5 != 0]
        + [(20, y) for y in range(32) if y % 5 != 2],
        (6, 16),
        [(26, 8), (26, 24), (30, 16)],
        80,
        20,
        4,
    ),
    mk(
        (32, 32),
        [(6, y) for y in range(32) if y % 6 not in (0, 1)]
        + [(26, y) for y in range(32) if y % 6 not in (3, 4)],
        (2, 16),
        [(29, 16), (16, 4), (16, 28)],
        100,
        25,
        5,
    ),
]


class Rp01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Rp01UI(0, 0)
        self._pulse_tail = 0
        self._pending_win = False
        super().__init__(
            "rp01",
            levels,
            Camera(0, 0, CAM_W, CAM_H, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 5, 6],
        )

    def _grid_to_frame_pixel(self, gx: int, gy: int) -> tuple[int, int]:
        cam = self.camera
        cw, ch = cam.width, cam.height
        scale = min(64 // cw, 64 // ch)
        x_pad = (64 - cw * scale) // 2
        y_pad = (64 - ch * scale) // 2
        return gx * scale + scale // 2 + x_pad, gy * scale + scale // 2 + y_pad

    def on_set_level(self, level: Level) -> None:
        self._src = next(
            (s.x, s.y) for s in self.current_level.get_sprites_by_tag("source")
        )
        self._lamps = {(s.x, s.y) for s in self.current_level.get_sprites_by_tag("lamp")}
        self._max_relays = int(self.current_level.get_data("max_relays") or 50)
        self._max_fires = int(self.current_level.get_data("max_fires") or 15)
        self._fires_left = self._max_fires
        self._relay_count = len(self.current_level.get_sprites_by_tag("relay"))
        self._pulse_tail = 0
        self._pending_win = False
        self._ui.clear_pulse()
        self._sync_ui()

    def _sync_ui(self) -> None:
        left = max(0, self._max_relays - self._relay_count)
        self._ui.update(left, self._fires_left)

    def _relay_cells(self) -> set[tuple[int, int]]:
        return {(s.x, s.y) for s in self.current_level.get_sprites_by_tag("relay")}

    def _simulate_pulse(
        self,
    ) -> tuple[set[tuple[int, int]], set[tuple[int, int]], dict[tuple[int, int], int]]:
        sx, sy = self._src
        q: deque[tuple[int, int, int]] = deque()
        seen: set[tuple[int, int]] = set()
        hop: dict[tuple[int, int], int] = {}
        relays = self._relay_cells()
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nx, ny = sx + dx, sy + dy
            if (nx, ny) in relays:
                q.append((nx, ny, 0))
                seen.add((nx, ny))
                hop[(nx, ny)] = 0
        lit: set[tuple[int, int]] = set()
        gw, gh = self.current_level.grid_size
        while q:
            x, y, d = q.popleft()
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                nx, ny = x + dx, y + dy
                if not (0 <= nx < gw and 0 <= ny < gh):
                    continue
                if (nx, ny) in self._lamps:
                    lit.add((nx, ny))
                if (nx, ny) in relays and (nx, ny) not in seen:
                    seen.add((nx, ny))
                    hop[(nx, ny)] = d + 1
                    q.append((nx, ny, d + 1))
        return lit, seen, hop

    def step(self) -> None:
        if self._pulse_tail > 0:
            phase = PULSE_FRAMES - self._pulse_tail
            self._pulse_tail -= 1
            self._ui.set_pulse_phase(phase)
            if self._pulse_tail == 0:
                if self._pending_win:
                    self.next_level()
                self._pending_win = False
                self._ui.clear_pulse()
                self.complete_action()
            return

        aid = self.action.id
        if aid in (
            GameAction.ACTION1,
            GameAction.ACTION2,
            GameAction.ACTION3,
            GameAction.ACTION4,
        ):
            self.complete_action()
            return

        if aid == GameAction.ACTION5:
            if self._fires_left <= 0:
                self.lose()
                self.complete_action()
                return
            self._fires_left -= 1
            self._sync_ui()
            lit, seen, hop = self._simulate_pulse()
            self._pending_win = lit >= self._lamps
            self._ui.begin_pulse(seen, lit, self._src, hop)
            self._pulse_tail = PULSE_FRAMES
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
        if sp and "relay" in sp.tags:
            self.current_level.remove_sprite(sp)
            self._relay_count -= 1
            self._sync_ui()
            self.complete_action()
            return

        if sp and ("wall" in sp.tags or "source" in sp.tags or "lamp" in sp.tags):
            self.complete_action()
            return

        if self._relay_count >= self._max_relays:
            self.complete_action()
            return

        self.current_level.add_sprite(sprites["relay"].clone().set_position(gx, gy))
        self._relay_count += 1
        self._sync_ui()
        self.complete_action()
