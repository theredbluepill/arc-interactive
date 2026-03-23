"""Manhattan beacon: like beacon sweep but reveal uses L1 (taxicab) radius."""

from __future__ import annotations

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
CAM_W = CAM_H = 64

PLAYER_C = 9
WALL_C = 3
GHOST_C = 2
FLAG_C = 8


class Bn02UI(RenderableUserDisplay):
    def __init__(self, beacons: int, found: int, need: int) -> None:
        self._beacons = beacons
        self._found = found
        self._need = need
        self._reject_ttl = 0

    def update(
        self,
        beacons: int,
        found: int,
        need: int,
        *,
        reject_ttl: int | None = None,
    ) -> None:
        self._beacons = beacons
        self._found = found
        self._need = need
        if reject_ttl is not None:
            self._reject_ttl = reject_ttl

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for i in range(min(self._beacons, 12)):
            frame[1, 1 + i] = 12
        for i in range(min(self._need, 20)):
            frame[2, 1 + i] = 14 if i < self._found else 8
        if self._reject_ttl > 0:
            for x in range(min(w, 10)):
                frame[h - 1, x] = 8
        return frame


sprites = {
    "wall": Sprite(
        pixels=[[WALL_C]],
        name="wall",
        visible=True,
        collidable=True,
        tags=["wall"],
    ),
    "player": Sprite(
        pixels=[[PLAYER_C]],
        name="player",
        visible=True,
        collidable=True,
        tags=["player"],
    ),
    "ghost": Sprite(
        pixels=[[GHOST_C]],
        name="ghost",
        visible=True,
        collidable=False,
        tags=["ghost"],
    ),
    "flag": Sprite(
        pixels=[[FLAG_C]],
        name="flag",
        visible=True,
        collidable=False,
        tags=["flag"],
    ),
}


def mk(
    walls: list[tuple[int, int]],
    player: tuple[int, int],
    hidden: list[tuple[int, int]],
    beacon_budget: int,
    radius: int,
    max_steps: int,
    diff: int,
) -> Level:
    sl: list[Sprite] = []
    for wx, wy in walls:
        sl.append(sprites["wall"].clone().set_position(wx, wy))
    sl.append(sprites["player"].clone().set_position(player[0], player[1]))
    return Level(
        sprites=sl,
        grid_size=(CAM_W, CAM_H),
        data={
            "difficulty": diff,
            "hidden": [list(p) for p in hidden],
            "beacon_budget": beacon_budget,
            "reveal_radius": radius,
            "max_steps": max_steps,
        },
    )


levels = [
    # Level 1: ghosts within Manhattan radius of spawn so first beacon at (32,32) reveals them.
    mk([], (32, 32), [(38, 32), (32, 40), (26, 30)], 6, 10, 500, 1),
    mk([(x, 32) for x in range(64) if x % 7 not in (0, 1)], (8, 32), [(55, 10), (55, 55), (10, 55)], 8, 9, 600, 2),
    mk(
        [(16, y) for y in range(64) if y % 5 != 0]
        + [(48, y) for y in range(64) if y % 5 != 2],
        (4, 32),
        [(30, 30), (34, 34), (38, 30), (34, 26)],
        10,
        8,
        700,
        3,
    ),
    mk(
        [(i, i) for i in range(64) if i % 4 == 0 and 8 < i < 56],
        (10, 10),
        [(58, 58), (58, 10), (10, 58), (35, 35), (40, 40)],
        12,
        7,
        800,
        4,
    ),
    mk(
        [],
        (32, 32),
        [(10 + (i % 8) * 6, 10 + (i // 8) * 6) for i in range(9)],
        14,
        6,
        900,
        5,
    ),
]


class Bn02(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Bn02UI(0, 0, 1)
        super().__init__(
            "bn02",
            levels,
            Camera(0, 0, CAM_W, CAM_H, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 5, 6],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        raw = self.current_level.get_data("hidden") or []
        self._hidden = {tuple(int(t) for t in p) for p in raw}
        self._beacons: list[tuple[int, int]] = []
        self._budget = int(self.current_level.get_data("beacon_budget") or 8)
        self._radius = int(self.current_level.get_data("reveal_radius") or 8)
        self._steps = int(self.current_level.get_data("max_steps") or 500)
        self._flagged: set[tuple[int, int]] = set()
        self._reject_ttl = 0
        self._sync_ghosts()
        self._sync_ui()

    def _revealed(self) -> set[tuple[int, int]]:
        out: set[tuple[int, int]] = set()
        r = self._radius
        for bx, by in self._beacons:
            for y in range(by - r, by + r + 1):
                for x in range(bx - r, bx + r + 1):
                    if abs(x - bx) + abs(y - by) <= r:
                        if 0 <= x < CAM_W and 0 <= y < CAM_H:
                            out.add((x, y))
        return out

    def _sync_ghosts(self) -> None:
        for s in list(self.current_level.get_sprites_by_tag("ghost")):
            self.current_level.remove_sprite(s)
        rev = self._revealed()
        for x, y in self._hidden:
            if (x, y) in rev:
                self.current_level.add_sprite(sprites["ghost"].clone().set_position(x, y))

    def _sync_ui(self) -> None:
        ok = len(self._hidden & self._flagged)
        self._ui.update(
            self._budget,
            ok,
            max(1, len(self._hidden)),
            reject_ttl=self._reject_ttl,
        )

    def _burn(self) -> bool:
        self._steps -= 1
        self._sync_ui()
        if self._steps <= 0:
            self.lose()
            return True
        return False

    def step(self) -> None:
        if self._reject_ttl > 0:
            self._reject_ttl -= 1
            self._sync_ui()

        aid = self.action.id

        if aid in (GameAction.ACTION1, GameAction.ACTION2, GameAction.ACTION3, GameAction.ACTION4):
            dx = dy = 0
            if aid == GameAction.ACTION1:
                dy = -1
            elif aid == GameAction.ACTION2:
                dy = 1
            elif aid == GameAction.ACTION3:
                dx = -1
            elif aid == GameAction.ACTION4:
                dx = 1
            nx, ny = self._player.x + dx, self._player.y + dy
            gw, gh = self.current_level.grid_size
            if 0 <= nx < gw and 0 <= ny < gh:
                sp = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
                if sp and "wall" in sp.tags:
                    pass
                elif not sp or not sp.is_collidable:
                    self._player.set_position(nx, ny)
                    self._reject_ttl = 0
                elif "ghost" in sp.tags or "flag" in sp.tags:
                    self._player.set_position(nx, ny)
                    self._reject_ttl = 0
            if self._burn():
                self.complete_action()
                return
            self.complete_action()
            return

        if aid == GameAction.ACTION5:
            if self._budget <= 0:
                if self._burn():
                    self.complete_action()
                    return
                self.complete_action()
                return
            self._budget -= 1
            self._beacons.append((self._player.x, self._player.y))
            self._reject_ttl = 0
            self._sync_ghosts()
            self._sync_ui()
            if self._burn():
                self.complete_action()
                return
            self.complete_action()
            return

        if aid != GameAction.ACTION6:
            self.complete_action()
            return

        px = self.action.data.get("x", 0)
        py = self.action.data.get("y", 0)
        coords = self.camera.display_to_grid(px, py)
        if coords is None:
            if self._burn():
                self.complete_action()
                return
            self.complete_action()
            return
        gx, gy = coords
        gw, gh = self.current_level.grid_size
        if not (0 <= gx < gw and 0 <= gy < gh):
            if self._burn():
                self.complete_action()
                return
            self.complete_action()
            return

        if (gx, gy) in self._flagged:
            hit = next(
                (
                    s
                    for s in self.current_level.get_sprites_by_tag("flag")
                    if s.x == gx and s.y == gy
                ),
                None,
            )
            if hit:
                self.current_level.remove_sprite(hit)
            self._flagged.discard((gx, gy))
            self._reject_ttl = 0
            self._sync_ui()
            if self._burn():
                self.complete_action()
                return
            self.complete_action()
            return

        if (gx, gy) in self._hidden:
            self._flagged.add((gx, gy))
            self._reject_ttl = 0
            self.current_level.add_sprite(sprites["flag"].clone().set_position(gx, gy))
            self._sync_ui()
            if self._flagged == self._hidden:
                self.next_level()
            if self._burn():
                self.complete_action()
                return
            self.complete_action()
            return

        self._reject_ttl = 3
        self._sync_ui()
        if self._burn():
            self.complete_action()
            return
        self.complete_action()
