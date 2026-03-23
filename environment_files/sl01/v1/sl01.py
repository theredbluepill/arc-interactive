"""Sliding tile puzzle (8-puzzle): hole swaps with orth-adjacent tiles until the board matches the goal.

Spec:
- Tags: ``player`` (hole, non-collidable, background-colored), ``tile`` + ``"1"``..``"8"`` (identity).
- ``level.data``: ``goal`` — 3×3 nested list; cell is 0 (hole) or 1..8 (tile id at that cell).
- Actions: 1–4 swap hole with tile above / below / left / right (same mapping as movement games: 1=up −y).
- Win: tile ids and hole position match ``goal``. Lose: optional ``step_limit`` exceeded.
- Camera/grid: 3×3 playfield, camera 8×8 (letterbox).
"""

from __future__ import annotations

from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


_GOAL_TILE_COLORS = [6, 7, 8, 10, 11, 12, 13, 14]


class Sl01UI(RenderableUserDisplay):
    def __init__(self, n_levels: int) -> None:
        self._steps = 0
        self._limit: int | None = None
        self._goal: list[list[int]] = [[1, 2, 3], [4, 5, 6], [7, 8, 0]]
        self._n_levels = n_levels
        self._li = 0
        self._edge_bump = False

    def update(
        self,
        steps: int,
        limit: int | None,
        level_index: int | None = None,
        goal: list[list[int]] | None = None,
        *,
        edge_bump: bool = False,
    ) -> None:
        self._steps = steps
        self._limit = limit
        self._edge_bump = edge_bump
        if goal is not None:
            self._goal = goal
        if level_index is not None:
            self._li = level_index

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for i in range(min(self._n_levels, 14)):
            cx = 1 + i * 2
            if cx >= w:
                break
            c = 14 if i < self._li else (11 if i == self._li else 3)
            frame[0, cx] = c
        gh = len(self._goal)
        gw = len(self._goal[0]) if gh else 0
        for y in range(min(gh, 3)):
            for x in range(min(gw, 3)):
                v = int(self._goal[y][x])
                tc = 5 if v == 0 else _GOAL_TILE_COLORS[v - 1]
                frame[1 + y, 1 + x] = tc
        c = 14 if self._limit is None or self._steps < self._limit else 8
        for dy in range(3):
            for dx in range(3):
                frame[h - 3 + dy, w - 6 + dx] = c
        if self._edge_bump:
            frame[min(h - 1, 7), min(w - 1, 7)] = 8
        return frame


sprites = {
    "player": Sprite(
        pixels=[[5]],
        name="hole",
        visible=True,
        collidable=False,
        tags=["player"],
    ),
}


def _tile_sprite(tile_id: int) -> Sprite:
    colors = [6, 7, 8, 10, 11, 12, 13, 14]
    c = colors[tile_id - 1]
    s = Sprite(
        pixels=[[c]],
        name=f"tile{tile_id}",
        visible=True,
        collidable=True,
        tags=["tile", str(tile_id)],
    )
    return s


def make_level(
    layout: list[list[int]],
    goal: list[list[int]],
    difficulty: int,
    step_limit: int | None,
) -> Level:
    """layout[y][x]: 0 = hole, 1..8 = tile id."""
    gw = len(layout[0])
    gh = len(layout)
    sl: list[Sprite] = []
    for y in range(gh):
        for x in range(gw):
            v = layout[y][x]
            if v == 0:
                sl.append(sprites["player"].clone().set_position(x, y))
            else:
                sl.append(_tile_sprite(v).clone().set_position(x, y))
    return Level(
        sprites=sl,
        grid_size=(gw, gh),
        data={
            "difficulty": difficulty,
            "goal": goal,
            "step_limit": step_limit,
        },
    )


# Solvable layouts (hand-authored); goal is canonical order.
_GOAL3 = [[1, 2, 3], [4, 5, 6], [7, 8, 0]]

levels = [
    make_level([[1, 2, 3], [4, 5, 6], [7, 0, 8]], _GOAL3, 1, 120),
    make_level([[1, 2, 3], [4, 0, 6], [7, 5, 8]], _GOAL3, 2, 150),
    make_level([[0, 1, 3], [4, 2, 6], [7, 5, 8]], _GOAL3, 3, 180),
    make_level([[4, 1, 3], [7, 2, 6], [0, 5, 8]], _GOAL3, 4, 220),
    make_level([[4, 1, 3], [7, 5, 6], [8, 2, 0]], _GOAL3, 5, 260),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Sl01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Sl01UI(len(levels))
        super().__init__(
            "sl01",
            levels,
            Camera(0, 0, 8, 8, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._goal = level.get_data("goal") or _GOAL3
        self._step_limit = level.get_data("step_limit")
        self._steps = 0
        self._ui.update(
            self._steps,
            self._step_limit,
            self.level_index,
            goal=[list(row) for row in self._goal],
            edge_bump=False,
        )

    def _solved(self) -> bool:
        px, py = self._player.x, self._player.y
        gh = len(self._goal)
        gw = len(self._goal[0])
        for y in range(gh):
            for x in range(gw):
                want = int(self._goal[y][x])
                if want == 0:
                    if px != x or py != y:
                        return False
                    continue
                sp = self.current_level.get_sprite_at(x, y, ignore_collidable=True)
                if sp is None or "tile" not in sp.tags:
                    return False
                if str(want) not in sp.tags:
                    return False
        return True

    def step(self) -> None:
        dx = dy = 0
        if self.action.id.value == 1:
            dy = -1
        elif self.action.id.value == 2:
            dy = 1
        elif self.action.id.value == 3:
            dx = -1
        elif self.action.id.value == 4:
            dx = 1

        if dx == 0 and dy == 0:
            self.complete_action()
            return

        px, py = self._player.x, self._player.y
        tx, ty = px + dx, py + dy
        gw, gh = self.current_level.grid_size
        if not (0 <= tx < gw and 0 <= ty < gh):
            self._ui.update(
                self._steps,
                self._step_limit,
                self.level_index,
                goal=[list(row) for row in self._goal],
                edge_bump=True,
            )
            self.complete_action()
            return

        tile = self.current_level.get_sprite_at(tx, ty, ignore_collidable=True)
        if tile is None or "tile" not in tile.tags:
            self.complete_action()
            return

        tile.set_position(px, py)
        self._player.set_position(tx, ty)
        self._steps += 1
        self._ui.update(
            self._steps,
            self._step_limit,
            self.level_index,
            goal=[list(row) for row in self._goal],
            edge_bump=False,
        )

        if self._solved():
            self.next_level()
        elif self._step_limit is not None and self._steps >= self._step_limit:
            self.lose()

        self.complete_action()
