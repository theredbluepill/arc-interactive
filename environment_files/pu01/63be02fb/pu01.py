"""Pipe twist: horizontal/vertical ducts. ACTION6 on a pipe cell toggles orientation. Connect cyan source to yellow sink (orthogonal flow)."""

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
CAM = 16
# N, E, S, W
H_PIPE = (0, 1, 0, 1)
V_PIPE = (1, 0, 1, 0)
OPP = (2, 3, 0, 1)
DX = (0, 1, 0, -1)
DY = (-1, 0, 1, 0)


class Pu01UI(RenderableUserDisplay):
    def __init__(self, ok: bool) -> None:
        self._ok = ok

    def update(self, ok: bool) -> None:
        self._ok = ok

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        frame[h - 2, 2] = 14 if self._ok else 8
        return frame


sprites = {
    "wall": Sprite(
        pixels=[[3]],
        name="wall",
        visible=True,
        collidable=True,
        tags=["wall"],
    ),
    "source": Sprite(
        pixels=[[10]],
        name="source",
        visible=True,
        collidable=False,
        tags=["source"],
    ),
    "sink": Sprite(
        pixels=[[11]],
        name="sink",
        visible=True,
        collidable=False,
        tags=["sink"],
    ),
    "pipe": Sprite(
        pixels=[[12]],
        name="pipe",
        visible=True,
        collidable=False,
        tags=["pipe"],
    ),
}


def mk(
    walls: list[tuple[int, int]],
    pipes: list[tuple[int, int, int]],
    src: tuple[int, int],
    snk: tuple[int, int],
    diff: int,
) -> Level:
    sl: list[Sprite] = []
    for wx, wy in walls:
        sl.append(sprites["wall"].clone().set_position(wx, wy))
    for px, py, _ in pipes:
        sl.append(sprites["pipe"].clone().set_position(px, py))
    sl.append(sprites["source"].clone().set_position(*src))
    sl.append(sprites["sink"].clone().set_position(*snk))
    return Level(
        sprites=sl,
        grid_size=(CAM, CAM),
        data={"difficulty": diff, "pipes": [[x, y, o] for x, y, o in pipes]},
    )


levels = [
    mk(
        [(x, 0) for x in range(16)] + [(x, 15) for x in range(16)]
        + [(0, y) for y in range(16)] + [(15, y) for y in range(16)],
        [(x, 8, 0) for x in range(2, 8)]
        + [(8, 8, 1)]
        + [(x, 8, 0) for x in range(9, 14)],
        (1, 8),
        (14, 8),
        1,
    ),
    mk(
        [(x, 0) for x in range(16)] + [(x, 15) for x in range(16)]
        + [(0, y) for y in range(16)] + [(15, y) for y in range(16)],
        [(8, y, 1 - (y % 2)) for y in range(2, 14)],
        (8, 1),
        (8, 14),
        2,
    ),
    mk(
        [(x, 0) for x in range(16)] + [(x, 15) for x in range(16)]
        + [(0, y) for y in range(16)] + [(15, y) for y in range(16)],
        [(x, 8, 0) for x in range(2, 7)]
        + [(7, y, 1) for y in range(8, 12)]
        + [(x, 11, 0) for x in range(7, 14)],
        (1, 8),
        (14, 11),
        3,
    ),
    mk(
        [(x, 0) for x in range(16)] + [(x, 15) for x in range(16)]
        + [(0, y) for y in range(16)] + [(15, y) for y in range(16)],
        [(4, y, 1) for y in range(3, 13)] + [(11, y, 1) for y in range(3, 13)],
        (4, 2),
        (11, 13),
        4,
    ),
    mk(
        [(x, 0) for x in range(16)] + [(x, 15) for x in range(16)]
        + [(0, y) for y in range(16)] + [(15, y) for y in range(16)],
        [(x, 5, 0) for x in range(3, 13)] + [(x, 10, 0) for x in range(3, 13)]
        + [(8, y, 1) for y in range(6, 10)],
        (2, 5),
        (13, 10),
        5,
    ),
]


class Pu01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Pu01UI(False)
        super().__init__(
            "pu01",
            levels,
            Camera(0, 0, CAM, CAM, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 6],
        )

    def on_set_level(self, level: Level) -> None:
        raw = self.current_level.get_data("pipes") or []
        self._pipe: dict[tuple[int, int], int] = {}
        for row in raw:
            x, y, o = int(row[0]), int(row[1]), int(row[2])
            self._pipe[(x, y)] = o % 2
        em = self.current_level.get_sprites_by_tag("source")[0]
        sk = self.current_level.get_sprites_by_tag("sink")[0]
        self._src = (em.x, em.y)
        self._snk = (sk.x, sk.y)
        self._ui.update(self._reachable())
        self._sync_pipe_sprites()

    def _sync_pipe_sprites(self) -> None:
        """H vs V: distinct hues (12 vs 13) so orientation is visible without toggling."""
        for sp in self.current_level.get_sprites_by_tag("pipe"):
            o = self._pipe.get((sp.x, sp.y), 0)
            want = 12 if o == 0 else 13
            cur = int(sp.pixels[0][0])
            if cur != want:
                sp.color_remap(cur, want)

    def _shape(self, x: int, y: int) -> tuple[int, int, int, int]:
        if (x, y) == self._src:
            return (0, 1, 0, 0)
        if (x, y) == self._snk:
            return (0, 0, 0, 1)
        o = self._pipe.get((x, y), 0)
        return V_PIPE if o else H_PIPE

    def _reachable(self) -> bool:
        q: deque[tuple[int, int]] = deque([self._src])
        seen = {self._src}
        gw, gh = self.current_level.grid_size
        while q:
            x, y = q.popleft()
            if (x, y) == self._snk:
                return True
            sh = self._shape(x, y)
            for d in range(4):
                if not sh[d]:
                    continue
                nx, ny = x + DX[d], y + DY[d]
                if not (0 <= nx < gw and 0 <= ny < gh):
                    continue
                sp = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
                if sp and "wall" in sp.tags:
                    continue
                nh = self._shape(nx, ny)
                if not nh[OPP[d]]:
                    continue
                if (nx, ny) not in seen:
                    seen.add((nx, ny))
                    q.append((nx, ny))
        return False

    def step(self) -> None:
        if self.action.id.value in (1, 2, 3, 4):
            self.complete_action()
            return

        if self.action.id != GameAction.ACTION6:
            self.complete_action()
            return

        px = self.action.data.get("x", 0)
        py = self.action.data.get("y", 0)
        coords = self.camera.display_to_grid(px, py)
        if coords is None:
            self.complete_action()
            return
        gx, gy = coords
        if (gx, gy) in self._pipe:
            self._pipe[(gx, gy)] = 1 - self._pipe[(gx, gy)]
            self._sync_pipe_sprites()
            ok = self._reachable()
            self._ui.update(ok)
            if ok:
                self.next_level()
        self.complete_action()
