"""Wall craft: reach the green goal; toggle build mode with ACTION5 and place/remove your own walls with ACTION6 (limited budget)."""

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


class Wl01UI(RenderableUserDisplay):
    def __init__(self, build: bool, budget: int, steps: int) -> None:
        self._build = build
        self._budget = budget
        self._steps = steps

    def update(self, build: bool, budget: int, steps: int) -> None:
        self._build = build
        self._budget = budget
        self._steps = steps

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        frame[h - 3, w - 3] = 12 if self._build else 3
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
}


def mk(
    grid: tuple[int, int],
    static_walls: list[tuple[int, int]],
    hazards: list[tuple[int, int]],
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


levels = [
    mk((32, 32), [], [], (2, 16), (29, 16), 12, 400, 1),
    mk(
        (32, 32),
        [(x, 15) for x in range(8, 24)],
        [],
        (4, 15),
        (28, 15),
        16,
        450,
        2,
    ),
    mk(
        (32, 32),
        [(15, y) for y in range(32) if y not in (15, 16)],
        [(20, 10)],
        (2, 2),
        (30, 30),
        20,
        500,
        3,
    ),
    mk(
        (32, 32),
        [(i, i) for i in range(32) if 8 < i < 24],
        [],
        (5, 27),
        (27, 5),
        24,
        550,
        4,
    ),
    mk(
        (32, 32),
        [(x, 8) for x in range(32) if x % 3 != 1]
        + [(x, 24) for x in range(32) if x % 3 != 2],
        [(16, 16)],
        (1, 16),
        (30, 16),
        30,
        600,
        5,
    ),
]


class Wl01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Wl01UI(False, 0, 0)
        super().__init__(
            "wl01",
            levels,
            Camera(0, 0, CAM_W, CAM_H, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 5, 6],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._budget = int(self.current_level.get_data("wall_budget") or 15)
        self._placed = 0
        self._build = False
        self._steps = int(self.current_level.get_data("max_steps") or 400)
        self._sync_ui()

    def _sync_ui(self) -> None:
        left = max(0, self._budget - self._placed)
        self._ui.update(self._build, left, self._steps)

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
                if sp and ("wall" in sp.tags or "mywall" in sp.tags):
                    pass
                elif sp and "hazard" in sp.tags:
                    self.lose()
                    self.complete_action()
                    return
                elif not sp or not sp.is_collidable:
                    self._player.set_position(nx, ny)
                elif "goal" in sp.tags:
                    self._player.set_position(nx, ny)
            if self._burn():
                self.complete_action()
                return
            g = self.current_level.get_sprites_by_tag("goal")[0]
            if self._player.x == g.x and self._player.y == g.y:
                self.next_level()
            self.complete_action()
            return

        if aid == GameAction.ACTION5:
            self._build = not self._build
            self._sync_ui()
            if self._burn():
                self.complete_action()
                return
            self.complete_action()
            return

        if aid != GameAction.ACTION6:
            self.complete_action()
            return

        if not self._build:
            if self._burn():
                self.complete_action()
                return
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
        if sp and "mywall" in sp.tags:
            self.current_level.remove_sprite(sp)
            self._placed -= 1
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

        self.current_level.add_sprite(sprites["mywall"].clone().set_position(gx, gy))
        self._placed += 1
        self._sync_ui()
        if self._burn():
            return
        self.complete_action()
