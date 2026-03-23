"""Vector arrows: landing on an arrow adds its vector to pending; your next input is combined and clamped to one orthogonal step (remainder stays pending)."""

from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)

# Directional arrow tiles (1×1): distinct ARC palette indices so orientation is visible.
_ARROW_UP = 6
_ARROW_DOWN = 7
_ARROW_RIGHT = 12
_ARROW_LEFT = 13
_ARROW_OTHER = 15


def _arrow_color(dx: int, dy: int) -> int:
    if (dx, dy) == (0, -1):
        return _ARROW_UP
    if (dx, dy) == (0, 1):
        return _ARROW_DOWN
    if (dx, dy) == (-1, 0):
        return _ARROW_LEFT
    if (dx, dy) == (1, 0):
        return _ARROW_RIGHT
    return _ARROW_OTHER


def arrow_sprite_for_vec(dx: int, dy: int) -> Sprite:
    c = _arrow_color(dx, dy)
    return Sprite(
        pixels=[[c]],
        name="arrow",
        visible=True,
        collidable=False,
        tags=["arrow"],
    )


def _sgn_hud(v: int) -> int:
    if v > 0:
        return 1
    if v < 0:
        return -1
    return 0


class Nw02UI(RenderableUserDisplay):
    def __init__(self, px: int, py: int) -> None:
        self._px = px
        self._py = py

    def update(self, px: int, py: int) -> None:
        self._px = px
        self._py = py

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        # Pending vector: 3×3 compass (gray cross + blue tip toward (sgn(px), sgn(py))).
        cy, cx0 = h - 4, 2
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                frame[cy + 1 + dy, cx0 + 1 + dx] = 4
        frame[cy + 1, cx0 + 1] = 2
        ox, oy = _sgn_hud(self._px), _sgn_hud(self._py)
        if ox != 0 or oy != 0:
            frame[cy + 1 + oy, cx0 + 1 + ox] = 9
        # Legend: which color means which push (R U L D).
        leg_y = h - 2
        frame[leg_y, 6] = _ARROW_RIGHT
        frame[leg_y, 7] = _ARROW_UP
        frame[leg_y, 8] = _ARROW_LEFT
        frame[leg_y, 9] = _ARROW_DOWN
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
    "arrow": Sprite(
        pixels=[[_ARROW_UP]],
        name="arrow",
        visible=True,
        collidable=False,
        tags=["arrow"],
    ),
}


def mk(sl, grid_size, difficulty, arrows):
    return Level(
        sprites=sl,
        grid_size=grid_size,
        data={"difficulty": difficulty, "arrows": arrows},
    )


levels = [
    mk(
        [
            sprites["player"].clone().set_position(0, 3),
            sprites["arrow"].clone().set_position(2, 3),
            sprites["target"].clone().set_position(6, 1),
        ],
        (8, 8),
        1,
        [[(2, 3), [0, -1]]],
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["arrow"].clone().set_position(3, 2),
            sprites["target"].clone().set_position(6, 6),
        ],
        (8, 8),
        2,
        [[(3, 2), [1, 0]]],
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["arrow"].clone().set_position(2, 2),
            sprites["target"].clone().set_position(7, 0),
        ],
        (8, 8),
        3,
        [[(2, 2), [0, 1]], [(4, 5), [-1, 0]]],
    ),
    mk(
        [
            sprites["player"].clone().set_position(2, 2),
            sprites["arrow"].clone().set_position(4, 2),
            sprites["target"].clone().set_position(1, 6),
        ],
        (8, 8),
        4,
        [[(4, 2), [0, 1]]],
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["arrow"].clone().set_position(1, 1),
            sprites["target"].clone().set_position(7, 7),
        ],
        (8, 8),
        5,
        [[(1, 1), [1, 0]]],
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


def _sgn(x: int) -> int:
    if x > 0:
        return 1
    if x < 0:
        return -1
    return 0


class Nw02(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Nw02UI(0, 0)
        super().__init__(
            "nw02",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._targets = self.current_level.get_sprites_by_tag("target")
        self._arrow_map: dict[tuple[int, int], tuple[int, int]] = {}
        for entry in level.get_data("arrows") or []:
            pos, vec = entry
            self._arrow_map[tuple(pos)] = tuple(vec)
        for s in list(self.current_level.get_sprites_by_tag("arrow")):
            pos = (s.x, s.y)
            vec = self._arrow_map.get(pos)
            if vec is None:
                continue
            self.current_level.remove_sprite(s)
            dx, dy = int(vec[0]), int(vec[1])
            self.current_level.add_sprite(
                arrow_sprite_for_vec(dx, dy).set_position(pos[0], pos[1]),
            )
        self._pend_x = 0
        self._pend_y = 0
        self._ui.update(0, 0)

    def step(self) -> None:
        ix = iy = 0
        if self.action.id.value == 1:
            iy = -1
        elif self.action.id.value == 2:
            iy = 1
        elif self.action.id.value == 3:
            ix = -1
        elif self.action.id.value == 4:
            ix = 1

        if ix == 0 and iy == 0:
            self.complete_action()
            return

        vx = ix + self._pend_x
        vy = iy + self._pend_y
        if vx == 0 and vy == 0:
            self.complete_action()
            return

        if abs(vx) >= abs(vy):
            dx, dy = _sgn(vx), 0
        else:
            dx, dy = 0, _sgn(vy)

        self._pend_x = vx - dx
        self._pend_y = vy - dy
        self._ui.update(self._pend_x, self._pend_y)

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

        pos = (self._player.x, self._player.y)
        if pos in self._arrow_map:
            ax, ay = self._arrow_map[pos]
            self._pend_x += ax
            self._pend_y += ay
            self._ui.update(self._pend_x, self._pend_y)

        for t in self._targets:
            if self._player.x == t.x and self._player.y == t.y:
                self.next_level()
                break

        self.complete_action()
