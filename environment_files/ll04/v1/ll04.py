"""ll04: Conway Life on a torus; ACTION5 advances; match target after N generations."""

from __future__ import annotations

from arcengine import ARCBaseGame, Camera, GameAction, Level, RenderableUserDisplay, Sprite

BG, PAD = 5, 4
G = 12
CAM = 16
LIVE = 14
WALL = 3


class Ll04UI(RenderableUserDisplay):
    def __init__(self, g: int, need: int) -> None:
        self._g, self._n = g, need

    def update(self, g: int, need: int) -> None:
        self._g, self._n = g, need

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for i in range(min(self._n, 10)):
            frame[h - 2, 1 + i * 2] = 11 if i < self._g else 2
        return frame


def mk(
    walls: list[tuple[int, int]],
    target: list[tuple[int, int]],
    need: int,
    max_tog: int,
    d: int,
) -> Level:
    sl = [
        Sprite(
            pixels=[[WALL]], name="w", visible=True, collidable=True, tags=["wall"]
        ).clone().set_position(wx, wy)
        for wx, wy in walls
    ]
    return Level(
        sprites=sl,
        grid_size=(G, G),
        data={
            "target": [list(p) for p in target],
            "need_generations": need,
            "max_toggles": max_tog,
            "difficulty": d,
        },
    )


def block(ax: int, ay: int) -> list[tuple[int, int]]:
    return [(ax, ay), (ax + 1, ay), (ax, ay + 1), (ax + 1, ay + 1)]


levels = [
    mk([], block(5, 5), 2, 80, 1),
    mk([(6, y) for y in range(G)], block(8, 4), 1, 100, 2),
    mk([], block(2, 2) + block(8, 8), 3, 150, 3),
    mk([(4, x) for x in range(G) if 3 < x < 8], block(9, 6), 2, 180, 4),
    mk([], block(4, 4), 4, 200, 5),
    mk([(2, 2), (9, 9)], block(5, 7), 2, 160, 6),
    mk([], block(1, 1) + block(7, 7), 3, 220, 7),
]


class Ll04(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Ll04UI(0, 1)
        super().__init__(
            "ll04",
            levels,
            Camera(0, 0, CAM, CAM, BG, PAD, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 5, 6],
        )

    def on_set_level(self, level: Level) -> None:
        self._target = {tuple(int(t) for t in p) for p in level.get_data("target")}
        self._need = int(level.get_data("need_generations") or 1)
        self._tog = int(level.get_data("max_toggles") or 100)
        self._gen = 0
        self._sync()

    def _wall(self, x: int, y: int) -> bool:
        sp = self.current_level.get_sprite_at(x, y, ignore_collidable=True)
        return sp is not None and "wall" in sp.tags

    def _live(self) -> set[tuple[int, int]]:
        return {(s.x, s.y) for s in self.current_level.get_sprites_by_tag("live")}

    def _sync(self) -> None:
        self._ui.update(self._gen, self._need)

    def _nbr_cnt(self, x: int, y: int, alive: set[tuple[int, int]]) -> int:
        c = 0
        for dx, dy in (
            (-1, -1),
            (-1, 0),
            (-1, 1),
            (0, -1),
            (0, 1),
            (1, -1),
            (1, 0),
            (1, 1),
        ):
            if ((x + dx) % G, (y + dy) % G) in alive:
                c += 1
        return c

    def _step_gen(self) -> None:
        alive = self._live()
        nxt: set[tuple[int, int]] = set()
        for y in range(G):
            for x in range(G):
                if self._wall(x, y):
                    continue
                n = self._nbr_cnt(x, y, alive)
                on = (x, y) in alive
                if on and n in (2, 3):
                    nxt.add((x, y))
                elif not on and n == 3:
                    nxt.add((x, y))
        for s in list(self.current_level.get_sprites_by_tag("live")):
            self.current_level.remove_sprite(s)
        for x, y in nxt:
            self.current_level.add_sprite(
                Sprite(
                    pixels=[[LIVE]],
                    name="l",
                    visible=True,
                    collidable=False,
                    tags=["live"],
                ).clone().set_position(x, y)
            )
        self._gen += 1

    def step(self) -> None:
        if self.action.id == GameAction.ACTION5:
            self._step_gen()
            self._sync()
            if self._gen >= self._need and self._live() == self._target:
                self.next_level()
            self.complete_action()
            return
        if self.action.id == GameAction.ACTION6:
            if self._tog <= 0:
                self.complete_action()
                return
            c = self.camera.display_to_grid(
                self.action.data.get("x", 0), self.action.data.get("y", 0)
            )
            if c:
                gx, gy = int(c[0]), int(c[1])
                if not self._wall(gx, gy):
                    ex = self.current_level.get_sprite_at(
                        gx, gy, ignore_collidable=True
                    )
                    if ex and "live" in ex.tags:
                        self.current_level.remove_sprite(ex)
                    else:
                        self.current_level.add_sprite(
                            Sprite(
                                pixels=[[LIVE]],
                                name="l",
                                visible=True,
                                collidable=False,
                                tags=["live"],
                            ).clone().set_position(gx, gy)
                        )
                    self._tog -= 1
            self._sync()
            self.complete_action()
            return
        self.complete_action()
