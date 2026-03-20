from collections import deque

from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Va03UI(RenderableUserDisplay):
    def __init__(self, idx: int, total: int, steps_left: int) -> None:
        self._idx = idx
        self._total = total
        self._steps_left = steps_left

    def update(self, idx: int, total: int, steps_left: int) -> None:
        self._idx = idx
        self._total = total
        self._steps_left = steps_left

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for i in range(min(self._total, 5)):
            c = 14 if i < self._idx else 11
            for dy in range(2):
                for dx in range(2):
                    frame[h - 4 + dy, w - 10 + i * 2 + dx] = c
        m = min(max(self._steps_left, 0), 24)
        for i in range(m):
            frame[h - 5, w - 24 + i] = 10
        return frame


sprites = {
    "player": Sprite(
        pixels=[[9]],
        name="player",
        visible=True,
        collidable=True,
        tags=["player"],
        layer=2,
    ),
    "trail": Sprite(
        pixels=[[14]],
        name="trail",
        visible=True,
        collidable=False,
        tags=["trail"],
        layer=0,
    ),
    "mark": Sprite(
        pixels=[[11]],
        name="mark",
        visible=True,
        collidable=False,
        tags=["mark"],
        layer=1,
    ),
    "wall": Sprite(
        pixels=[[3]],
        name="wall",
        visible=True,
        collidable=True,
        tags=["wall"],
        layer=1,
    ),
}


def mk(sl, grid_size, difficulty, visit_order, step_limit: int):
    return Level(
        sprites=sl,
        grid_size=grid_size,
        data={
            "difficulty": difficulty,
            "visit_order": visit_order,
            "step_limit": step_limit,
        },
    )


def _bfs_dist(
    open_cells: set[tuple[int, int]],
    start: tuple[int, int],
    goal: tuple[int, int],
) -> int | None:
    if start == goal:
        return 0
    q: deque[tuple[int, int]] = deque([start])
    dist = {start: 0}
    while q:
        x, y = q.popleft()
        d0 = dist[(x, y)]
        for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            n = (x + dx, y + dy)
            if n not in open_cells or n in dist:
                continue
            dist[n] = d0 + 1
            if n == goal:
                return d0 + 1
            q.append(n)
    return None


def min_moves_visit_order(level: Level) -> int:
    """Shortest successful-move count to satisfy ``visit_order`` in sequence (matches game rules)."""
    raw = level.get_data("visit_order") or []
    order = [(int(p[0]), int(p[1])) for p in raw]
    if not order:
        return 0
    gw, gh = level.grid_size
    walls: set[tuple[int, int]] = set()
    player: tuple[int, int] | None = None
    for s in level.get_sprites():
        if "player" in s.tags:
            player = (s.x, s.y)
        elif "wall" in s.tags:
            walls.add((s.x, s.y))
    if player is None:
        return 10**9
    open_cells = {(x, y) for x in range(gw) for y in range(gh) if (x, y) not in walls}
    if player not in open_cells:
        return 10**9
    idx = 0
    pos = player
    if pos == order[0]:
        idx = 1
    total = 0
    while idx < len(order):
        g = order[idx]
        seg = _bfs_dist(open_cells, pos, g)
        if seg is None:
            return 10**9
        total += seg
        pos = g
        idx += 1
    return total


def level_with_marks(vo, walls, grid_size, diff, player_pos):
    sl = [sprites["player"].clone().set_position(*player_pos)]
    for p in vo:
        sl.append(sprites["mark"].clone().set_position(*p))
    for wp in walls:
        sl.append(sprites["wall"].clone().set_position(*wp))
    lvl = Level(
        sprites=sl,
        grid_size=grid_size,
        data={"difficulty": diff, "visit_order": vo},
    )
    need = min_moves_visit_order(lvl)
    if need >= 10**8:
        raise RuntimeError("va03: unsolvable visit_order for authored level")
    # Exact budget: you must clear the route in ``need`` successful moves; the last one lands
    # on the final waypoint. No slack — detours run you out of budget first.
    return mk(sl, grid_size, diff, vo, need)


levels = [
    level_with_marks([(0, 0), (1, 1), (2, 2)], [], (4, 4), 1, (0, 0)),
    level_with_marks([(0, 0), (2, 0), (2, 2), (0, 2)], [], (5, 5), 2, (0, 0)),
    level_with_marks(
        [(0, 0), (1, 0), (2, 0), (3, 0)],
        [(1, 1), (2, 1)],
        (8, 8),
        3,
        (0, 1),
    ),
    level_with_marks([(1, 1), (3, 1), (3, 3), (1, 3)], [(2, 2)], (6, 6), 4, (0, 0)),
    level_with_marks([(0, 0), (7, 0), (7, 7), (0, 7)], [], (8, 8), 5, (0, 0)),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Va03(ARCBaseGame):
    """
    Finish: step on every coordinate in ``visit_order`` in sequence (list order = visit order).
    If the player **starts** on waypoint 0, that one counts as already visited.
    **next_level()** runs right after you step onto the **last** waypoint.
    Yellow marks show the route; each completed waypoint turns **green**; floor you walked is
    also tinted **green** (trail).
    **Step budget** (``step_limit`` = shortest solve in successful moves): each **successful**
    move uses one step. Hitting OOB or a wall does not move you and does not spend a step.
    You **lose** if you use all ``step_limit`` successful moves without clearing the route —
    the winning move must be the last budgeted step onto the final waypoint.
    """

    def _add_trail(self, x: int, y: int) -> None:
        t = sprites["trail"].clone().set_position(x, y)
        self.current_level.add_sprite(t)

    def _green_mark_here(self, x: int, y: int) -> None:
        sp = self.current_level.get_sprite_at(x, y, ignore_collidable=True)
        if sp and "mark" in sp.tags:
            sp.color_remap(11, 14)

    def _sync_ui(self) -> None:
        budget = max(0, self._step_limit - self._steps)
        self._ui.update(self._next, len(self._order), budget)

    def __init__(self) -> None:
        self._ui = Va03UI(0, 1, 0)
        super().__init__(
            "va03",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        vo = level.get_data("visit_order") or []
        self._order = [(int(p[0]), int(p[1])) for p in vo]
        self._visited_floor: set[tuple[int, int]] = set()
        self._next = 0
        px, py = self._player.x, self._player.y
        self._visited_floor.add((px, py))
        self._add_trail(px, py)
        self._steps = 0
        lim = level.get_data("step_limit")
        self._step_limit = int(lim) if lim is not None else 10**9
        if self._order and (px, py) == self._order[0]:
            self._next = 1
            self._green_mark_here(px, py)
        self._sync_ui()

    def step(self) -> None:
        dx = 0
        dy = 0
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

        new_x = self._player.x + dx
        new_y = self._player.y + dy
        grid_w, grid_h = self.current_level.grid_size
        if not (0 <= new_x < grid_w and 0 <= new_y < grid_h):
            self.complete_action()
            return

        sprite = self.current_level.get_sprite_at(new_x, new_y, ignore_collidable=True)

        if sprite and "wall" in sprite.tags:
            self.complete_action()
            return

        if not sprite or not sprite.is_collidable:
            self._player.set_position(new_x, new_y)
        else:
            self.complete_action()
            return

        self._steps += 1
        pos = (self._player.x, self._player.y)
        if pos not in self._visited_floor:
            self._add_trail(*pos)
        self._visited_floor.add(pos)

        won = False
        if self._next < len(self._order) and pos == self._order[self._next]:
            self._green_mark_here(pos[0], pos[1])
            self._next += 1
            if self._next >= len(self._order):
                won = True
                if self._steps != self._step_limit:
                    self.lose()
                else:
                    self.next_level()

        if not won and self._steps >= self._step_limit:
            self.lose()

        self._sync_ui()
        self.complete_action()
