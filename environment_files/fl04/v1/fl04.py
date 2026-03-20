"""fl04: connect A–B with a path of length at most L (fl01 with cap)."""

from __future__ import annotations

from arcengine import ARCBaseGame, Camera, GameAction, Level, RenderableUserDisplay, Sprite

BG, PAD = 5, 4
sprites = {
    "player": Sprite(
        pixels=[[9]], name="p", visible=True, collidable=True, tags=["player"]
    ),
    "a": Sprite(
        pixels=[[11]], name="a", visible=True, collidable=False, tags=["a"]
    ),
    "b": Sprite(
        pixels=[[11]], name="b", visible=True, collidable=False, tags=["b"]
    ),
    "path": Sprite(
        pixels=[[10]], name="path", visible=True, collidable=False, tags=["path_px"]
    ),
    "wall": Sprite(
        pixels=[[3]], name="w", visible=True, collidable=True, tags=["wall"]
    ),
}


class Fl04UI(RenderableUserDisplay):
    def __init__(self, ln: int, cap: int) -> None:
        self._ln, self._cap = ln, cap

    def update(self, ln: int, cap: int) -> None:
        self._ln, self._cap = ln, cap

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for i in range(min(self._ln, 15)):
            frame[h - 2, 1 + i] = 10
        for i in range(min(self._cap, 15)):
            frame[h - 1, 1 + i] = 14 if i < self._ln else 4
        return frame


def mk(sl: list, cap: int, d: int) -> Level:
    return Level(
        sprites=sl,
        grid_size=(12, 12),
        data={"difficulty": d, "max_len": cap},
    )


levels = [
    mk(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["a"].clone().set_position(1, 1),
            sprites["b"].clone().set_position(1, 5),
        ],
        8,
        1,
    ),
    mk(
        [
            sprites["player"].clone().set_position(2, 2),
            sprites["a"].clone().set_position(2, 2),
            sprites["b"].clone().set_position(8, 2),
        ],
        12,
        2,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["a"].clone().set_position(0, 0),
            sprites["b"].clone().set_position(5, 5),
        ]
        + [sprites["wall"].clone().set_position(3, y) for y in range(6)],
        14,
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(6, 6),
            sprites["a"].clone().set_position(6, 6),
            sprites["b"].clone().set_position(6, 0),
        ],
        10,
        4,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 5),
            sprites["a"].clone().set_position(1, 5),
            sprites["b"].clone().set_position(10, 5),
        ],
        18,
        5,
    ),
    mk(
        [
            sprites["player"].clone().set_position(2, 1),
            sprites["a"].clone().set_position(2, 1),
            sprites["b"].clone().set_position(9, 8),
        ],
        20,
        6,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 5),
            sprites["a"].clone().set_position(0, 5),
            sprites["b"].clone().set_position(11, 5),
        ],
        22,
        7,
    ),
]


class Fl04(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Fl04UI(0, 1)
        super().__init__(
            "fl04",
            levels,
            Camera(0, 0, 16, 16, BG, PAD, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 6],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._cap = int(self.current_level.get_data("max_len") or 10)
        self._path: list[tuple[int, int]] = []
        self._clear_path()
        self._ui.update(0, self._cap)

    def _clear_path(self) -> None:
        for s in list(self.current_level.get_sprites_by_tag("path_px")):
            self.current_level.remove_sprite(s)

    def _eps(self) -> tuple[tuple[int, int], tuple[int, int]]:
        a = self.current_level.get_sprites_by_tag("a")[0]
        b = self.current_level.get_sprites_by_tag("b")[0]
        return (a.x, a.y), (b.x, b.y)

    def _redraw(self) -> None:
        self._clear_path()
        epa, epb = self._eps()
        for x, y in self._path:
            if (x, y) in (epa, epb):
                continue
            self.current_level.add_sprite(sprites["path"].clone().set_position(x, y))
        self._ui.update(len(self._path), self._cap)

    def step(self) -> None:
        if self.action.id == GameAction.ACTION6:
            hit = self.camera.display_to_grid(
                self.action.data.get("x", 0), self.action.data.get("y", 0)
            )
            if not hit:
                self.complete_action()
                return
            gx, gy = int(hit[0]), int(hit[1])
            gw, gh = self.current_level.grid_size
            if not (0 <= gx < gw and 0 <= gy < gh):
                self.complete_action()
                return
            epa, epb = self._eps()
            if not self._path:
                if (gx, gy) in (epa, epb):
                    self._path.append((gx, gy))
                    self._redraw()
            else:
                lx, ly = self._path[-1]
                if abs(gx - lx) + abs(gy - ly) != 1:
                    self.complete_action()
                    return
                if (gx, gy) in self._path:
                    self.complete_action()
                    return
                sp = self.current_level.get_sprite_at(gx, gy, ignore_collidable=True)
                if sp and "wall" in sp.tags:
                    self.complete_action()
                    return
                self._path.append((gx, gy))
                self._redraw()
                ps = set(self._path)
                if epa in ps and epb in ps and len(self._path) <= self._cap:
                    self.next_level()
            self.complete_action()
            return

        dx = dy = 0
        if self.action.id.value == 1:
            dy = -1
        elif self.action.id.value == 2:
            dy = 1
        elif self.action.id.value == 3:
            dx = -1
        elif self.action.id.value == 4:
            dx = 1
        else:
            self.complete_action()
            return
        nx, ny = self._player.x + dx, self._player.y + dy
        gw, gh = self.current_level.grid_size
        if 0 <= nx < gw and 0 <= ny < gh:
            sp = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
            if not sp or not sp.is_collidable:
                self._player.set_position(nx, ny)
        self.complete_action()
