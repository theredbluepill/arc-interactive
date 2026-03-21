"""Wall craft: reach the green goal. Dark red chasms are deadly—bridge them with ACTION6 clicks (limited wall budget, step budget). Player draws above placed bridges."""

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
CAM_W = CAM_H = 32

WALL_C = 3
MYW_C = 2
PLAYER_C = 9
GOAL_C = 14
HAZ_C = 8
CHASM_C = 13  # maroon — deadly gap; bridgeable with mywall (distinct from red hazard mines)


class Wl01UI(RenderableUserDisplay):
    def __init__(self, budget: int, steps: int) -> None:
        self._budget = budget
        self._steps = steps

    def update(self, budget: int, steps: int) -> None:
        self._budget = budget
        self._steps = steps

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        frame[h - 3, w - 3] = MYW_C
        for i in range(min(self._budget, 24)):
            frame[h - 2, 1 + i] = 11
        for i in range(min(self._steps, 30)):
            frame[h - 1, 1 + i] = 10
        return frame


sprites = {
    "wall": Sprite(
        pixels=[[WALL_C]],
        name="wall",
        visible=True,
        collidable=True,
        tags=["wall"],
    ),
    "mywall": Sprite(
        pixels=[[MYW_C]],
        name="mywall",
        visible=True,
        collidable=True,
        tags=["mywall"],
    ),
    "player": Sprite(
        pixels=[[PLAYER_C]],
        name="player",
        visible=True,
        collidable=True,
        tags=["player"],
        layer=1,
    ),
    "goal": Sprite(
        pixels=[[GOAL_C]],
        name="goal",
        visible=True,
        collidable=False,
        tags=["goal"],
    ),
    "hazard": Sprite(
        pixels=[[HAZ_C]],
        name="hazard",
        visible=True,
        collidable=True,
        tags=["hazard"],
    ),
    "chasm": Sprite(
        pixels=[[CHASM_C]],
        name="chasm",
        visible=True,
        collidable=False,
        tags=["chasm"],
    ),
}


def mk(
    grid: tuple[int, int],
    static_walls: list[tuple[int, int]],
    hazards: list[tuple[int, int]],
    chasms: list[tuple[int, int]],
    player: tuple[int, int],
    goal: tuple[int, int],
    wall_budget: int,
    max_steps: int,
    diff: int,
) -> Level:
    sl: list[Sprite] = []
    for wx, wy in static_walls:
        sl.append(sprites["wall"].clone().set_position(wx, wy))
    for hx, hy in hazards:
        sl.append(sprites["hazard"].clone().set_position(hx, hy))
    for cx, cy in chasms:
        sl.append(sprites["chasm"].clone().set_position(cx, cy))
    sl.append(sprites["player"].clone().set_position(player[0], player[1]))
    sl.append(sprites["goal"].clone().set_position(goal[0], goal[1]))
    return Level(
        sprites=sl,
        grid_size=grid,
        data={
            "difficulty": diff,
            "wall_budget": wall_budget,
            "max_steps": max_steps,
        },
    )


def _sealed_chasm_column(
    x_lo: int, x_hi: int
) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    """Static walls around a vertical x-band so only the middle row (y=15) crosses it."""
    xs = range(x_lo, x_hi + 1)
    top_bottom = [(x, 14) for x in xs] + [(x, 16) for x in xs]
    seal_north = [(x, y) for x in xs for y in range(0, 14)]
    seal_south = [(x, y) for x in xs for y in range(17, 32)]
    return top_bottom + seal_north + seal_south, [(x, 15) for x in xs]


def _mk_sealed_row(
    x_lo: int,
    x_hi: int,
    hazards: list[tuple[int, int]],
    player: tuple[int, int],
    goal: tuple[int, int],
    wall_budget: int,
    max_steps: int,
    diff: int,
) -> Level:
    sw, ch = _sealed_chasm_column(x_lo, x_hi)
    return mk((32, 32), sw, hazards, ch, player, goal, wall_budget, max_steps, diff)


# Levels require bridging chasms (no land path); hazards are optional extra threats.
levels = [
    mk(
        (32, 32),
        [(x, y) for x in (8, 9, 10) for y in range(32) if y != 16],
        [],
        [(8, 16), (9, 16), (10, 16)],
        (3, 16),
        (16, 16),
        5,
        220,
        1,
    ),
    _mk_sealed_row(9, 18, [], (3, 15), (28, 15), 10, 280, 2),
    _mk_sealed_row(10, 18, [(24, 8)], (2, 15), (29, 15), 11, 360, 3),
    _mk_sealed_row(10, 17, [], (4, 15), (28, 15), 8, 380, 4),
    _mk_sealed_row(5, 26, [(8, 10)], (2, 15), (29, 15), 24, 520, 5),
]


class Wl01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Wl01UI(0, 0)
        super().__init__(
            "wl01",
            levels,
            Camera(0, 0, CAM_W, CAM_H, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 6],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._budget = int(self.current_level.get_data("wall_budget") or 15)
        self._placed = 0
        self._steps = int(self.current_level.get_data("max_steps") or 400)
        self._chasm_orig: set[tuple[int, int]] = set()
        for s in self.current_level.get_sprites_by_tag("chasm"):
            self._chasm_orig.add((s.x, s.y))
        self._sync_ui()

    def _sync_ui(self) -> None:
        left = max(0, self._budget - self._placed)
        self._ui.update(left, self._steps)

    @staticmethod
    def _mywall_at(level: Level, gx: int, gy: int) -> Sprite | None:
        for s in level.get_sprites_by_tag("mywall"):
            if s.x == gx and s.y == gy:
                return s
        return None

    def _burn(self) -> bool:
        self._steps -= 1
        self._sync_ui()
        if self._steps <= 0:
            self.lose()
            return True
        return False

    def step(self) -> None:
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
                elif sp and "hazard" in sp.tags:
                    self.lose()
                    self.complete_action()
                    return
                elif sp and "chasm" in sp.tags:
                    self.lose()
                    self.complete_action()
                    return
                elif sp and "goal" in sp.tags:
                    self._player.set_position(nx, ny)
                elif sp and "mywall" in sp.tags:
                    self._player.set_position(nx, ny)
                elif not sp or not sp.is_collidable:
                    self._player.set_position(nx, ny)
            if self._burn():
                self.complete_action()
                return
            g = self.current_level.get_sprites_by_tag("goal")[0]
            if self._player.x == g.x and self._player.y == g.y:
                self.next_level()
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

        sp = self.current_level.get_sprite_at(gx, gy, ignore_collidable=True)
        mw = self._mywall_at(self.current_level, gx, gy)
        if mw is not None:
            self.current_level.remove_sprite(mw)
            self._placed -= 1
            if (gx, gy) in self._chasm_orig:
                self.current_level.add_sprite(sprites["chasm"].clone().set_position(gx, gy))
            self._sync_ui()
            if self._burn():
                self.complete_action()
                return
            self.complete_action()
            return

        if sp and (
            "wall" in sp.tags
            or "goal" in sp.tags
            or "hazard" in sp.tags
            or "player" in sp.tags
        ):
            if self._burn():
                self.complete_action()
                return
            self.complete_action()
            return

        if self._placed >= self._budget:
            if self._burn():
                self.complete_action()
                return
            self.complete_action()
            return

        if sp and "chasm" in sp.tags:
            self.current_level.remove_sprite(sp)

        self.current_level.add_sprite(sprites["mywall"].clone().set_position(gx, gy))
        self._placed += 1
        self._sync_ui()
        if self._burn():
            self.complete_action()
            return
        self.complete_action()
