"""Relay pulse with depth budget: each hop counts; stepping onto an amplifier relay resets hop depth so long chains need amps."""

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


class Rp03UI(RenderableUserDisplay):
    def __init__(self, relays_left: int, fires_left: int) -> None:
        self._relays = relays_left
        self._fires = fires_left

    def update(self, relays_left: int, fires_left: int) -> None:
        self._relays = relays_left
        self._fires = fires_left

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for i in range(min(self._relays, 24)):
            frame[h - 2, 1 + i] = 12
        for i in range(min(self._fires, 8)):
            frame[h - 1, 1 + i] = 9
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
    "amp_relay": Sprite(
        pixels=[[7]],
        name="amp_relay",
        visible=True,
        collidable=False,
        tags=["relay", "amp_relay"],
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
            "max_pulse_depth": 8,
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


class Rp03(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Rp03UI(0, 0)
        super().__init__(
            "rp03",
            levels,
            Camera(0, 0, CAM_W, CAM_H, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 5, 6],
        )

    def on_set_level(self, level: Level) -> None:
        self._src = next(
            (s.x, s.y) for s in self.current_level.get_sprites_by_tag("source")
        )
        self._lamps = {(s.x, s.y) for s in self.current_level.get_sprites_by_tag("lamp")}
        self._max_relays = int(self.current_level.get_data("max_relays") or 50)
        self._max_fires = int(self.current_level.get_data("max_fires") or 15)
        self._fires_left = self._max_fires
        self._relay_count = len(self.current_level.get_sprites_by_tag("relay"))
        self._sync_ui()

    def _sync_ui(self) -> None:
        left = max(0, self._max_relays - self._relay_count)
        self._ui.update(left, self._fires_left)

    def _relay_cells(self) -> set[tuple[int, int]]:
        return {(s.x, s.y) for s in self.current_level.get_sprites_by_tag("relay")}

    def _fire_pulse(self) -> None:
        sx, sy = self._src
        max_d = int(self.current_level.get_data("max_pulse_depth") or 8)
        amps = {
            (s.x, s.y)
            for s in self.current_level.get_sprites_by_tag("relay")
            if "amp_relay" in s.tags
        }
        relays = self._relay_cells()
        q: deque[tuple[int, int, int]] = deque()
        best: dict[tuple[int, int], int] = {}
        gw, gh = self.current_level.grid_size
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nx, ny = sx + dx, sy + dy
            if (nx, ny) in relays:
                q.append((nx, ny, 0))
                best[(nx, ny)] = 0
        lit: set[tuple[int, int]] = set()
        while q:
            x, y, d = q.popleft()
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                nx, ny = x + dx, y + dy
                if not (0 <= nx < gw and 0 <= ny < gh):
                    continue
                if (nx, ny) in self._lamps:
                    lit.add((nx, ny))
                if (nx, ny) not in relays:
                    continue
                nd = 1 if (x, y) in amps else d + 1
                if nd > max_d:
                    continue
                old = best.get((nx, ny), 999)
                if nd < old:
                    best[(nx, ny)] = nd
                    q.append((nx, ny, nd))
        if lit >= self._lamps:
            self.next_level()

    def step(self) -> None:
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
            self._fire_pulse()
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
