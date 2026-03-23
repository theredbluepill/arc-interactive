"""Heatseeker: a hunter moves one step toward you every two player moves; same cell loses."""

from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Hs01UI(RenderableUserDisplay):
    def __init__(self, d: int) -> None:
        self._d = d
        self._hunter_fill = 0

    def update(self, d: int, hunter_fill: int = 0) -> None:
        self._d = d
        self._hunter_fill = hunter_fill

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for i in range(min(self._d, 12)):
            frame[h - 2, 1 + i] = 8
        # Two ticks = player moves before the hunter steps (period 2).
        for i in range(min(self._hunter_fill, 2)):
            frame[h - 3, min(20 + i * 2, w - 1)] = 8
        return frame


sprites = {
    "player": Sprite(
        pixels=[[9]],
        name="player",
        visible=True,
        collidable=True,
        tags=["player"],
    ),
    "hunter": Sprite(
        pixels=[[8]],
        name="hunter",
        visible=True,
        collidable=True,
        tags=["hunter"],
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
}


def mk(sl: list, d: int) -> Level:
    return Level(sprites=sl, grid_size=(10, 10), data={"difficulty": d})


levels = [
    mk(
        [
            sprites["player"].clone().set_position(0, 5),
            sprites["hunter"].clone().set_position(9, 5),
            sprites["goal"].clone().set_position(4, 5),
        ],
        1,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["hunter"].clone().set_position(8, 8),
            sprites["goal"].clone().set_position(5, 5),
        ],
        2,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["hunter"].clone().set_position(9, 9),
            sprites["goal"].clone().set_position(8, 0),
        ],
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(2, 5),
            sprites["hunter"].clone().set_position(7, 5),
            sprites["goal"].clone().set_position(4, 5),
            sprites["wall"].clone().set_position(5, 4),
            sprites["wall"].clone().set_position(5, 6),
        ],
        4,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 9),
            sprites["hunter"].clone().set_position(9, 0),
            sprites["goal"].clone().set_position(5, 5),
        ],
        5,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Hs01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Hs01UI(1)
        super().__init__(
            "hs01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._hunter = self.current_level.get_sprites_by_tag("hunter")[0]
        self._goal = self.current_level.get_sprites_by_tag("goal")[0]
        self._move_ctr = 0
        self._difficulty = int(level.get_data("difficulty") or 1)
        self._ui.update(self._difficulty, 0)

    def _blocked(self, x: int, y: int, ignore: Sprite | None = None) -> bool:
        gw, gh = self.current_level.grid_size
        if not (0 <= x < gw and 0 <= y < gh):
            return True
        sp = self.current_level.get_sprite_at(x, y, ignore_collidable=True)
        if sp is ignore:
            return False
        if not sp:
            return False
        if "goal" in sp.tags:
            return False
        return sp.is_collidable

    def _hunter_step(self) -> None:
        px, py = self._player.x, self._player.y
        hx, hy = self._hunter.x, self._hunter.y
        cand: list[tuple[int, int]] = []
        if abs(px - hx) >= abs(py - hy):
            if px > hx:
                cand.append((hx + 1, hy))
            elif px < hx:
                cand.append((hx - 1, hy))
            if py > hy:
                cand.append((hx, hy + 1))
            elif py < hy:
                cand.append((hx, hy - 1))
        else:
            if py > hy:
                cand.append((hx, hy + 1))
            elif py < hy:
                cand.append((hx, hy - 1))
            if px > hx:
                cand.append((hx + 1, hy))
            elif px < hx:
                cand.append((hx - 1, hy))
        for tx, ty in cand:
            if not self._blocked(tx, ty, ignore=self._hunter):
                self._hunter.set_position(tx, ty)
                return

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

        if dx != 0 or dy != 0:
            nx = self._player.x + dx
            ny = self._player.y + dy
            gw, gh = self.current_level.grid_size
            if (0 <= nx < gw and 0 <= ny < gh) and not self._blocked(nx, ny):
                self._player.set_position(nx, ny)

        self._move_ctr += 1
        hunter_moved = False
        if self._move_ctr >= 2:
            self._move_ctr = 0
            self._hunter_step()
            hunter_moved = True

        if self._hunter.x == self._player.x and self._hunter.y == self._player.y:
            self.lose()
            self.complete_action()
            return

        if self._player.x == self._goal.x and self._player.y == self._goal.y:
            self.next_level()

        fill = 0 if hunter_moved else self._move_ctr
        self._ui.update(self._difficulty, fill)
        self.complete_action()
