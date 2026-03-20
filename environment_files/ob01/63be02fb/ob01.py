"""Odd one out: three avatars; ACTION5 cycles who receives ACTION1–4. Each must reach its own green cell."""

from __future__ import annotations

from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)

BACKGROUND_COLOR = 5
PADDING_COLOR = 4
CAM = 16


class Ob01UI(RenderableUserDisplay):
    def __init__(self, active: int) -> None:
        self._active = active

    def update(self, active: int) -> None:
        self._active = active

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for i in range(3):
            frame[h - 2, 2 + i * 2] = 11 if i == self._active else 3
        return frame


def _p(c: int, tag: str) -> Sprite:
    return Sprite(
        pixels=[[c]],
        name=tag,
        visible=True,
        collidable=True,
        tags=["player", tag],
    )


sprites = {
    "p0": _p(9, "pa"),
    "p1": _p(10, "pb"),
    "p2": _p(6, "pc"),
    "g0": Sprite(
        pixels=[[14]],
        name="g0",
        visible=True,
        collidable=False,
        tags=["goal", "ga"],
    ),
    "g1": Sprite(
        pixels=[[14]],
        name="g1",
        visible=True,
        collidable=False,
        tags=["goal", "gb"],
    ),
    "g2": Sprite(
        pixels=[[14]],
        name="g2",
        visible=True,
        collidable=False,
        tags=["goal", "gc"],
    ),
    "wall": Sprite(
        pixels=[[3]],
        name="wall",
        visible=True,
        collidable=True,
        tags=["wall"],
    ),
}


def mk(
    ps: list[tuple[int, int]],
    gs: list[tuple[int, int]],
    walls: list[tuple[int, int]],
    diff: int,
) -> Level:
    sl = [
        sprites["p0"].clone().set_position(*ps[0]),
        sprites["p1"].clone().set_position(*ps[1]),
        sprites["p2"].clone().set_position(*ps[2]),
        sprites["g0"].clone().set_position(*gs[0]),
        sprites["g1"].clone().set_position(*gs[1]),
        sprites["g2"].clone().set_position(*gs[2]),
    ]
    for wx, wy in walls:
        sl.append(sprites["wall"].clone().set_position(wx, wy))
    return Level(sprites=sl, grid_size=(CAM, CAM), data={"difficulty": diff})


levels = [
    mk([(2, 8), (8, 2), (14, 8)], [(12, 8), (8, 12), (2, 8)], [], 1),
    mk([(1, 1), (8, 1), (15, 1)], [(1, 14), (8, 14), (15, 14)], [(8, y) for y in range(4, 12)], 2),
    mk([(2, 2), (13, 2), (8, 8)], [(13, 13), (2, 13), (8, 13)], [], 3),
    mk([(0, 8), (8, 0), (15, 15)], [(15, 8), (8, 15), (0, 0)], [(x, 8) for x in range(16) if x not in (7, 8, 9)], 4),
    mk([(4, 4), (11, 4), (4, 11)], [(11, 11), (4, 11), (11, 4)], [(8, y) for y in range(16) if y != 8], 5),
]


class Ob01(ARCBaseGame):
    TAGS = ("pa", "pb", "pc")
    GOALS = ("ga", "gb", "gc")

    def __init__(self) -> None:
        self._ui = Ob01UI(0)
        super().__init__(
            "ob01",
            levels,
            Camera(0, 0, CAM, CAM, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 5],
        )

    def on_set_level(self, level: Level) -> None:
        self._players = [
            self.current_level.get_sprites_by_tag(t)[0] for t in self.TAGS
        ]
        self._goals = [
            self.current_level.get_sprites_by_tag(t)[0] for t in self.GOALS
        ]
        self._active = 0
        self._ui.update(self._active)

    def step(self) -> None:
        aid = self.action.id.value
        if aid == 5:
            self._active = (self._active + 1) % 3
            self._ui.update(self._active)
            self.complete_action()
            return

        dx = dy = 0
        if aid == 1:
            dy = -1
        elif aid == 2:
            dy = 1
        elif aid == 3:
            dx = -1
        elif aid == 4:
            dx = 1
        else:
            self.complete_action()
            return

        pl = self._players[self._active]
        nx, ny = pl.x + dx, pl.y + dy
        gw, gh = self.current_level.grid_size
        if not (0 <= nx < gw and 0 <= ny < gh):
            self.complete_action()
            return
        sp = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
        if sp and "wall" in sp.tags:
            self.complete_action()
            return
        if sp and "player" in sp.tags:
            self.complete_action()
            return
        pl.set_position(nx, ny)

        ok = True
        for i, p in enumerate(self._players):
            g = self._goals[i]
            if p.x != g.x or p.y != g.y:
                ok = False
                break
        if ok:
            self.next_level()

        self.complete_action()
