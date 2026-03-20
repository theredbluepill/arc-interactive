"""tc04: packages follow arrow tiles; ACTION5 conveyor step; ACTION6 flips arrow CW."""

from __future__ import annotations

from arcengine import ARCBaseGame, Camera, GameAction, Level, RenderableUserDisplay, Sprite

BG, PAD = 5, 4
G = 10
CAM = 16
PKG = 11
SNK = 14
ARW = 10


def rot(dx: int, dy: int) -> tuple[int, int]:
    return -dy, dx


class Tc04UI(RenderableUserDisplay):
    def __init__(self, n: int) -> None:
        self._n = n

    def update(self, n: int) -> None:
        self._n = n

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        frame[h - 2, 2] = 8 if self._n > 0 else 14
        return frame


def mk(
    arrows: dict[tuple[int, int], tuple[int, int]],
    packages: list[tuple[int, int]],
    sinks: list[tuple[int, int]],
    max_steps: int,
    d: int,
) -> Level:
    sl: list[Sprite] = []
    for (x, y), (dx, dy) in arrows.items():
        sl.append(
            Sprite(
                pixels=[[ARW]],
                name="a",
                visible=True,
                collidable=False,
                tags=["arrow", f"d{dx},{dy}"],
            ).clone().set_position(x, y)
        )
    for x, y in packages:
        sl.append(
            Sprite(
                pixels=[[PKG]],
                name="p",
                visible=True,
                collidable=False,
                tags=["package"],
            ).clone().set_position(x, y)
        )
    for x, y in sinks:
        sl.append(
            Sprite(
                pixels=[[SNK]],
                name="s",
                visible=True,
                collidable=True,
                tags=["sink"],
            ).clone().set_position(x, y)
        )
    ser = {f"{x},{y}": [dx, dy] for (x, y), (dx, dy) in arrows.items()}
    return Level(
        sprites=sl,
        grid_size=(G, G),
        data={
            "arrows": ser,
            "packages": [list(p) for p in packages],
            "sinks": [list(p) for p in sinks],
            "max_steps": max_steps,
            "difficulty": d,
        },
    )


levels = [
    mk({(2, 5): (1, 0), (4, 5): (1, 0)}, [(2, 5)], [(7, 5)], 40, 1),
    mk({(1, 2): (0, 1), (1, 4): (1, 0)}, [(1, 2)], [(5, 4)], 50, 2),
    mk({(3, 3): (1, 0), (5, 3): (0, 1), (5, 6): (-1, 0)}, [(3, 3)], [(4, 6)], 60, 3),
    mk({(0, 5): (1, 0), (8, 5): (0, -1)}, [(0, 5)], [(8, 4)], 45, 4),
    mk({(2, 2): (1, 0), (6, 2): (0, 1), (6, 7): (-1, 0)}, [(2, 2)], [(5, 7)], 70, 5),
    mk({(4, 1): (0, 1), (4, 8): (1, 0)}, [(4, 1)], [(8, 8)], 55, 6),
    mk({(1, 1): (1, 0), (3, 1): (1, 0), (5, 1): (0, 1)}, [(1, 1)], [(5, 3)], 65, 7),
]


class Tc04(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Tc04UI(0)
        super().__init__(
            "tc04",
            levels,
            Camera(0, 0, CAM, CAM, BG, PAD, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 5, 6],
        )

    def on_set_level(self, level: Level) -> None:
        self._arrows: dict[tuple[int, int], tuple[int, int]] = {}
        for k, v in (level.get_data("arrows") or {}).items():
            x, y = map(int, k.split(","))
            self._arrows[(x, y)] = (int(v[0]), int(v[1]))
        self._sinks = {tuple(int(t) for t in p) for p in level.get_data("sinks") or []}
        self._left = int(level.get_data("max_steps") or 50)
        self._sync()

    def _arrow_at(self, x: int, y: int) -> tuple[int, int] | None:
        return self._arrows.get((x, y))

    def _pkgs(self) -> list[Sprite]:
        return list(self.current_level.get_sprites_by_tag("package"))

    def _sync(self) -> None:
        self._ui.update(len(self._pkgs()))

    def _move(self) -> None:
        for p in self._pkgs():
            d = self._arrow_at(p.x, p.y)
            if not d:
                continue
            dx, dy = d
            nx, ny = p.x + dx, p.y + dy
            if 0 <= nx < G and 0 <= ny < G:
                if (nx, ny) in self._sinks:
                    self.current_level.remove_sprite(p)
                else:
                    p.set_position(nx, ny)

    def _flip(self, gx: int, gy: int) -> None:
        if (gx, gy) not in self._arrows:
            return
        dx, dy = self._arrows[(gx, gy)]
        ndx, ndy = rot(dx, dy)
        self._arrows[(gx, gy)] = (ndx, ndy)
        for s in self.current_level.get_sprites_by_tag("arrow"):
            if s.x == gx and s.y == gy:
                self.current_level.remove_sprite(s)
                self.current_level.add_sprite(
                    Sprite(
                        pixels=[[ARW]],
                        name="a",
                        visible=True,
                        collidable=False,
                        tags=["arrow"],
                    ).clone().set_position(gx, gy)
                )
                break

    def step(self) -> None:
        if self.action.id == GameAction.ACTION5:
            self._move()
            self._left -= 1
            self._sync()
            if not self._pkgs():
                self.next_level()
            elif self._left <= 0:
                self.lose()
            self.complete_action()
            return
        if self.action.id == GameAction.ACTION6:
            c = self.camera.display_to_grid(
                self.action.data.get("x", 0), self.action.data.get("y", 0)
            )
            if c:
                self._flip(int(c[0]), int(c[1]))
            self._left -= 1
            self._sync()
            if not self._pkgs():
                self.next_level()
            elif self._left <= 0:
                self.lose()
            self.complete_action()
            return
        self.complete_action()
