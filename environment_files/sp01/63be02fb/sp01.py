"""Sandpile: ACTION6 adds a grain; cells with >=4 topple to neighbors. Win when total grains equals the level target sum."""

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
GW = GH = 12
CAM = 16
WALL_C = 3


class Sp01UI(RenderableUserDisplay):
    def __init__(self, steps: int) -> None:
        self._steps = steps

    def update(self, steps: int) -> None:
        self._steps = steps

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for i in range(min(self._steps, 20)):
            frame[h - 2, 1 + i] = 11
        return frame


def _px(n: int) -> Sprite:
    c = min(15, 5 + n)
    return Sprite(
        pixels=[[c]],
        name="sand",
        visible=True,
        collidable=False,
        tags=["sand"],
    )


def mk(
    walls: list[tuple[int, int]],
    target_sum: int,
    max_steps: int,
    diff: int,
) -> Level:
    sl = []
    for wx, wy in walls:
        sl.append(
            Sprite(
                pixels=[[WALL_C]],
                name="wall",
                visible=True,
                collidable=True,
                tags=["wall"],
            ).set_position(wx, wy),
        )
    return Level(
        sprites=sl,
        grid_size=(GW, GH),
        data={
            "difficulty": diff,
            "target_sum": target_sum,
            "max_steps": max_steps,
        },
    )


levels = [
    mk([], 24, 200, 1),
    mk([(6, y) for y in range(12) if y != 5], 40, 250, 2),
    mk([], 60, 300, 3),
    mk([(0, y) for y in range(12)] + [(11, y) for y in range(12)], 36, 350, 4),
    mk([], 80, 400, 5),
]


class Sp01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Sp01UI(0)
        super().__init__(
            "sp01",
            levels,
            Camera(0, 0, CAM, CAM, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 6],
        )

    def on_set_level(self, level: Level) -> None:
        self._target_sum = int(self.current_level.get_data("target_sum") or 0)
        self._g = [[0 for _ in range(GW)] for _ in range(GH)]
        self._steps_left = int(self.current_level.get_data("max_steps") or 200)
        self._refresh_sprites()

    def _wall(self, x: int, y: int) -> bool:
        sp = self.current_level.get_sprite_at(x, y, ignore_collidable=True)
        return sp is not None and "wall" in sp.tags

    def _refresh_sprites(self) -> None:
        for s in list(self.current_level.get_sprites_by_tag("sand")):
            self.current_level.remove_sprite(s)
        for y in range(GH):
            for x in range(GW):
                if self._wall(x, y):
                    continue
                n = self._g[y][x]
                if n > 0:
                    self.current_level.add_sprite(_px(n).set_position(x, y))

    def _topple(self) -> None:
        changed = True
        while changed:
            changed = False
            nxt = [row[:] for row in self._g]
            for y in range(GH):
                for x in range(GW):
                    if self._wall(x, y):
                        continue
                    if self._g[y][x] < 4:
                        continue
                    nxt[y][x] -= 4
                    for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < GW and 0 <= ny < GH and not self._wall(nx, ny):
                            nxt[ny][nx] += 1
                    changed = True
            self._g = nxt

    def _win(self) -> bool:
        if any(self._g[y][x] >= 4 for y in range(GH) for x in range(GW)):
            return False
        s = sum(self._g[y][x] for y in range(GH) for x in range(GW))
        return s == self._target_sum

    def step(self) -> None:
        if self.action.id.value in (1, 2, 3, 4):
            self.complete_action()
            return

        if self.action.id != GameAction.ACTION6:
            self.complete_action()
            return

        if self._steps_left <= 0:
            self.lose()
            self.complete_action()
            return

        x = self.action.data.get("x", 0)
        y = self.action.data.get("y", 0)
        coords = self.camera.display_to_grid(x, y)
        if coords is None:
            self.complete_action()
            return
        gx, gy = coords
        if not (0 <= gx < GW and 0 <= gy < GH) or self._wall(gx, gy):
            self.complete_action()
            return

        self._g[gy][gx] += 1
        self._topple()
        self._refresh_sprites()
        self._steps_left -= 1
        self._ui.update(self._steps_left)
        if self._win():
            self.next_level()
        elif self._steps_left <= 0:
            self.lose()

        self.complete_action()
