"""Delay line: ACTION1–4 enqueue a cardinal move (FIFO, max 3 pending). Each step runs the oldest queued move first, then enqueues the current action. ACTION5 clears the queue."""

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
CAM = 12


class Dl01UI(RenderableUserDisplay):
    _DIR_COLOR = {(0, -1): 10, (0, 1): 6, (-1, 0): 11, (1, 0): 9}

    def __init__(self) -> None:
        self._q: list[tuple[int, int]] = []
        self._bump = 0

    def update(
        self,
        q: list[tuple[int, int]],
        *,
        bump: bool = False,
    ) -> None:
        self._q = list(q)
        if bump:
            self._bump = 6

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        base_x = 2
        for slot in range(3):
            cx = base_x + slot * 5
            if slot < len(self._q):
                dx, dy = self._q[slot]
                c = self._DIR_COLOR.get((dx, dy), 11)
                frame[h - 2, cx] = c
                if dy == -1:
                    frame[h - 3, cx] = c
                elif dy == 1:
                    frame[h - 1, cx] = c
                elif dx == -1:
                    frame[h - 2, cx - 1] = c
                elif dx == 1:
                    frame[h - 2, cx + 1] = c
            else:
                frame[h - 2, cx] = 3
        if self._bump > 0:
            frame[h - 2, w - 3] = 8
            self._bump -= 1
        return frame


sprites = {
    "player": Sprite(
        pixels=[[9]],
        name="player",
        visible=True,
        collidable=True,
        tags=["player"],
    ),
    "goal": Sprite(
        pixels=[[14]],
        name="goal",
        visible=True,
        collidable=False,
        tags=["goal"],
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
        tags=["hazard"],
    ),
}


def mk(
    player: tuple[int, int],
    goal: tuple[int, int],
    walls: list[tuple[int, int]],
    hazards: list[tuple[int, int]],
    diff: int,
) -> Level:
    sl: list[Sprite] = [
        sprites["player"].clone().set_position(player[0], player[1]),
        sprites["goal"].clone().set_position(goal[0], goal[1]),
    ]
    for wx, wy in walls:
        sl.append(sprites["wall"].clone().set_position(wx, wy))
    for hx, hy in hazards:
        sl.append(sprites["hazard"].clone().set_position(hx, hy))
    return Level(
        sprites=sl,
        grid_size=(CAM, CAM),
        data={"difficulty": diff},
    )


levels = [
    mk((1, 1), (10, 10), [], [], 1),
    mk((1, 1), (10, 10), [(6, y) for y in range(12) if y != 6], [], 2),
    # Two-cell gap in the x=5 wall so (5,6) is reachable from (5,7); hazards off the gap.
    mk((2, 2), (9, 9), [(5, y) for y in range(12) if y not in (6, 7)], [(3, 3), (9, 3)], 3),
    mk((0, 6), (11, 6), [(x, 5) for x in range(12) if x != 6], [], 4),
    mk((1, 1), (10, 10), [(x, x) for x in range(12) if x in (3, 8)], [(3, 8), (8, 3)], 5),
]


class Dl01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Dl01UI()
        self._q: deque[tuple[int, int]] = deque()
        super().__init__(
            "dl01",
            levels,
            Camera(0, 0, CAM, CAM, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 5],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._q.clear()
        self._ui.update(list(self._q))

    def _apply_move(self, dx: int, dy: int) -> bool:
        nx, ny = self._player.x + dx, self._player.y + dy
        gw, gh = self.current_level.grid_size
        if not (0 <= nx < gw and 0 <= ny < gh):
            return False
        sp = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
        if sp and ("wall" in sp.tags or "hazard" in sp.tags):
            return False
        self._player.set_position(nx, ny)
        g = self.current_level.get_sprites_by_tag("goal")[0]
        if self._player.x == g.x and self._player.y == g.y:
            self.next_level()
        return True

    def _sync_queue_ui(self, *, bump: bool = False) -> None:
        self._ui.update(list(self._q), bump=bump)

    def step(self) -> None:
        aid = self.action.id

        if aid == GameAction.ACTION5:
            self._q.clear()
            self._sync_queue_ui()
            self.complete_action()
            return

        blocked = False
        if self._q:
            dx, dy = self._q.popleft()
            if not self._apply_move(dx, dy):
                blocked = True

        if aid == GameAction.ACTION1:
            self._q.append((0, -1))
        elif aid == GameAction.ACTION2:
            self._q.append((0, 1))
        elif aid == GameAction.ACTION3:
            self._q.append((-1, 0))
        elif aid == GameAction.ACTION4:
            self._q.append((1, 0))

        while len(self._q) > 3:
            self._q.popleft()

        self._sync_queue_ui(bump=blocked)
        self.complete_action()
