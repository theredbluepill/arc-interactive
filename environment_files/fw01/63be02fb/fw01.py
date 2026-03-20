"""Wildfire: fire spreads to random orth neighbors every few steps. ACTION6 splashes water (3×3) removing fire. Reach the green exit."""

from __future__ import annotations

import random

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
CAM = 24
FIRE_C = 8
GOAL_C = 14
PLAYER_C = 9
WALL_C = 3


class Fw01UI(RenderableUserDisplay):
    def __init__(self, tick: int) -> None:
        self._tick = tick

    def update(self, tick: int) -> None:
        self._tick = tick

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for i in range(min(self._tick % 5, 4)):
            frame[h - 2, 1 + i] = 12
        return frame


sprites = {
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
    "wall": Sprite(
        pixels=[[WALL_C]],
        name="wall",
        visible=True,
        collidable=True,
        tags=["wall"],
    ),
    "fire": Sprite(
        pixels=[[FIRE_C]],
        name="fire",
        visible=True,
        collidable=True,
        tags=["fire"],
    ),
}


def mk(
    p: tuple[int, int],
    g: tuple[int, int],
    walls: list[tuple[int, int]],
    fires: list[tuple[int, int]],
    spread_every: int,
    diff: int,
) -> Level:
    sl = [
        sprites["player"].clone().set_position(*p),
        sprites["goal"].clone().set_position(*g),
    ]
    for wx, wy in walls:
        sl.append(sprites["wall"].clone().set_position(wx, wy))
    for fx, fy in fires:
        sl.append(sprites["fire"].clone().set_position(fx, fy))
    return Level(
        sprites=sl,
        grid_size=(CAM, CAM),
        data={"difficulty": diff, "spread_every": spread_every},
    )


levels = [
    mk((2, 12), (20, 12), [], [(15, 12)], 5, 1),
    mk((1, 1), (22, 22), [(12, y) for y in range(24) if y != 12], [(10, 10), (14, 14)], 4, 2),
    mk((3, 3), (21, 21), [], [(12, 12), (11, 12), (13, 12), (12, 11)], 3, 3),
    mk((0, 12), (23, 12), [(x, 8) for x in range(24) if x % 4 != 0], [(18, y) for y in range(10, 18)], 4, 4),
    mk((12, 2), (12, 22), [], [(12, 10), (12, 14), (8, 12), (16, 12)], 3, 5),
]


class Fw01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Fw01UI(0)
        super().__init__(
            "fw01",
            levels,
            Camera(0, 0, CAM, CAM, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 6],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._tick = 0
        self._every = int(self.current_level.get_data("spread_every") or 4)
        self._rng = random.Random(42 + hash(self.current_level.grid_size))
        self._ui.update(0)

    def _fire_cells(self) -> set[tuple[int, int]]:
        return {(s.x, s.y) for s in self.current_level.get_sprites_by_tag("fire")}

    def _spread(self) -> None:
        fc = list(self._fire_cells())
        if not fc:
            return
        self._rng.shuffle(fc)
        for x, y in fc[: max(1, len(fc) // 3)]:
            dx, dy = self._rng.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
            nx, ny = x + dx, y + dy
            gw, gh = self.current_level.grid_size
            if not (0 <= nx < gw and 0 <= ny < gh):
                continue
            sp = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
            if sp and ("wall" in sp.tags or "goal" in sp.tags):
                continue
            if sp and "fire" in sp.tags:
                continue
            if sp and "player" in sp.tags:
                continue
            self.current_level.add_sprite(sprites["fire"].clone().set_position(nx, ny))

    def _splash(self, cx: int, cy: int) -> None:
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                x, y = cx + dx, cy + dy
                sp = self.current_level.get_sprite_at(x, y, ignore_collidable=True)
                if sp and "fire" in sp.tags:
                    self.current_level.remove_sprite(sp)

    def step(self) -> None:
        aid = self.action.id

        if aid == GameAction.ACTION6:
            px = self.action.data.get("x", 0)
            py = self.action.data.get("y", 0)
            coords = self.camera.display_to_grid(px, py)
            if coords:
                self._splash(coords[0], coords[1])
            self._tick += 1
            if self._tick % self._every == 0:
                self._spread()
            self._ui.update(self._tick)
            self.complete_action()
            return

        dx = dy = 0
        if aid == GameAction.ACTION1:
            dy = -1
        elif aid == GameAction.ACTION2:
            dy = 1
        elif aid == GameAction.ACTION3:
            dx = -1
        elif aid == GameAction.ACTION4:
            dx = 1
        else:
            self.complete_action()
            return

        nx, ny = self._player.x + dx, self._player.y + dy
        gw, gh = self.current_level.grid_size
        if 0 <= nx < gw and 0 <= ny < gh:
            sp = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
            if sp and "wall" in sp.tags:
                pass
            elif sp and "fire" in sp.tags:
                pass
            else:
                self._player.set_position(nx, ny)

        self._tick += 1
        if self._tick % self._every == 0:
            self._spread()

        px, py = self._player.x, self._player.y
        here = self.current_level.get_sprite_at(px, py, ignore_collidable=True)
        if here and "fire" in here.tags:
            self.lose()
            self.complete_action()
            return

        gl = self.current_level.get_sprites_by_tag("goal")[0]
        if self._player.x == gl.x and self._player.y == gl.y:
            self.next_level()

        self._ui.update(self._tick)
        self.complete_action()
