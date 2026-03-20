"""After each move, gravity pulls one step down (if not blocked).

**Lose:** if the yellow goal is **unreachable** under the same move+gravity rules (BFS over
positions), the run ends after **two consecutive** steps in that state (confirmation beat so a
single check does not flicker if ordering ever surprises).
"""

from collections import deque

from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Gr01UI(RenderableUserDisplay):
    def __init__(self, _: int) -> None:
        pass

    def update(self, _: int) -> None:
        pass

    def render_interface(self, frame):
        return frame


sprites = {
    "player": Sprite(
        pixels=[[9]],
        name="player",
        visible=True,
        collidable=True,
        tags=["player"],
    ),
    "target": Sprite(
        pixels=[[11]],
        name="target",
        visible=True,
        collidable=False,
        tags=["target"],
    ),
    "wall": Sprite(
        pixels=[[3]],
        name="wall",
        visible=True,
        collidable=True,
        tags=["wall"],
    ),
}


def mk(sl, grid_size, difficulty):
    return Level(sprites=sl, grid_size=grid_size, data={"difficulty": difficulty})


# L0: gray **walls** form a 2-deep pocket under column 2 — walk down into it to trap yourself
# (goal unreachable); registry GIF uses this before the solve chain.
_GR01_TRAP_WALLS = ((1, 5), (3, 5), (1, 6), (3, 6), (2, 7))
# Extra obstacles (still solvable to (7,7) if you avoid the pit).
_GR01_L0_EXTRA = ((5, 0), (6, 0), (7, 0), (0, 4), (1, 3), (4, 2), (6, 3))
# Column chokes + side clutter — forces detours while descending.
_GR01_L1_WALLS = (
    (2, 3),
    (2, 5),
    (0, 2),
    (4, 2),
    (5, 2),
    (1, 4),
    (3, 4),
    (5, 4),
    (0, 6),
    (4, 6),
    (6, 6),
    (1, 6),
    (7, 5),
)
_GR01_L2_WALLS = (
    (3, 3),
    (5, 2),
    (6, 2),
    (2, 4),
    (3, 4),
    (4, 4),
    (5, 5),
    (6, 5),
    (4, 6),
    (2, 6),
    (0, 5),
    (7, 4),
    (0, 3),
    (7, 2),
    (4, 2),
)
_GR01_L3_WALLS = (
    (0, 3),
    (1, 3),
    (2, 3),
    (3, 3),
    (5, 3),
    (6, 3),
    (7, 3),
    (2, 1),
    (5, 1),
    (2, 5),
    (5, 5),
    (1, 6),
    (6, 6),
    (3, 7),
    (4, 0),
    (0, 2),
    (7, 1),
    (1, 0),
    (6, 0),
)
_GR01_L4_WALLS = (
    (2, 2),
    (4, 2),
    (2, 4),
    (4, 4),
    (2, 6),
    (4, 6),
    (0, 3),
    (5, 3),
    (6, 5),
    (1, 5),
    (5, 7),
    (7, 5),
    (1, 1),
    (5, 1),
    (6, 3),
)
_GR01_L5_WALLS = (
    (3, 2),
    (4, 2),
    (1, 4),
    (5, 4),
    (2, 5),
    (6, 5),
    (4, 6),
    (0, 6),
    (6, 3),
    (7, 3),
    (2, 0),
    (5, 0),
    (3, 0),
    (4, 4),
    (1, 1),
    (7, 5),
)


def _wall_sprites(coords: tuple[tuple[int, int], ...]):
    return [sprites["wall"].clone().set_position(x, y) for x, y in coords]


levels = [
    mk(
        [
            sprites["player"].clone().set_position(2, 1),
            sprites["target"].clone().set_position(7, 7),
        ]
        + _wall_sprites(_GR01_TRAP_WALLS + _GR01_L0_EXTRA),
        (8, 8),
        1,
    ),
    mk(
        [
            sprites["player"].clone().set_position(2, 0),
            sprites["target"].clone().set_position(2, 7),
        ]
        + _wall_sprites(_GR01_L1_WALLS),
        (8, 8),
        2,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["target"].clone().set_position(6, 7),
        ]
        + _wall_sprites(_GR01_L2_WALLS),
        (8, 8),
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["target"].clone().set_position(7, 7),
        ]
        + _wall_sprites(_GR01_L3_WALLS),
        (8, 8),
        4,
    ),
    mk(
        [
            sprites["player"].clone().set_position(3, 0),
            sprites["target"].clone().set_position(3, 7),
        ]
        + _wall_sprites(_GR01_L4_WALLS),
        (8, 8),
        5,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 2),
            sprites["target"].clone().set_position(7, 7),
        ]
        + _wall_sprites(_GR01_L5_WALLS),
        (8, 8),
        6,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Gr01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Gr01UI(0)
        super().__init__(
            "gr01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._targets = self.current_level.get_sprites_by_tag("target")
        self._deadend_pending = False

    def _blocked(self, x: int, y: int) -> bool:
        sp = self.current_level.get_sprite_at(x, y, ignore_collidable=True)
        return sp is not None and "wall" in sp.tags

    def _gravity(self) -> None:
        grid_w, grid_h = self.current_level.grid_size
        nx, ny = self._player.x, self._player.y + 1
        if 0 <= nx < grid_w and 0 <= ny < grid_h and not self._blocked(nx, ny):
            self._player.set_position(nx, ny)

    def _after_action_from(self, x: int, y: int, dx: int, dy: int) -> tuple[int, int] | None:
        """One cardinal step (if legal) then one gravity step — matches ``step()`` physics."""
        gw, gh = self.current_level.grid_size
        nx, ny = x + dx, y + dy
        if not (0 <= nx < gw and 0 <= ny < gh) or self._blocked(nx, ny):
            return None
        px, py = nx, ny
        gx, gy = px, py + 1
        if 0 <= gx < gw and 0 <= gy < gh and not self._blocked(gx, gy):
            px, py = gx, gy
        return (px, py)

    def _goal_reachable(self) -> bool:
        if not self._targets:
            return True
        goals = {(t.x, t.y) for t in self._targets}
        sx, sy = self._player.x, self._player.y
        if (sx, sy) in goals:
            return True
        q = deque([(sx, sy)])
        seen = {(sx, sy)}
        while q:
            x, y = q.popleft()
            for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                nxt = self._after_action_from(x, y, dx, dy)
                if nxt is None:
                    continue
                px, py = nxt
                if (px, py) in goals:
                    return True
                if (px, py) not in seen:
                    seen.add((px, py))
                    q.append((px, py))
        return False

    def _check_deadend(self) -> None:
        if self._goal_reachable():
            self._deadend_pending = False
            return
        if self._deadend_pending:
            self.lose()
            return
        self._deadend_pending = True

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
            self._check_deadend()
            self.complete_action()
            return

        new_x = self._player.x + dx
        new_y = self._player.y + dy
        grid_w, grid_h = self.current_level.grid_size
        if not (0 <= new_x < grid_w and 0 <= new_y < grid_h):
            self._check_deadend()
            self.complete_action()
            return

        sprite = self.current_level.get_sprite_at(new_x, new_y, ignore_collidable=True)

        if sprite and "wall" in sprite.tags:
            self._check_deadend()
            self.complete_action()
            return

        if not sprite or not sprite.is_collidable:
            self._player.set_position(new_x, new_y)

        self._gravity()

        for t in self._targets:
            if self._player.x == t.x and self._player.y == t.y:
                self.next_level()
                self.complete_action()
                return

        self._check_deadend()
        self.complete_action()
