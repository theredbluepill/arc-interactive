"""Plan #1: whole level rotates 90° CW every ``rotate_every`` steps; ACTION5 spends brace budget to skip once."""

from __future__ import annotations

from arcengine import ARCBaseGame, Camera, GameAction, Level, RenderableUserDisplay, Sprite

BG, PAD = 5, 4


def rot_cw(g: int, x: int, y: int) -> tuple[int, int]:
    return y, g - 1 - x


class Wr01UI(RenderableUserDisplay):
    def __init__(self, brace: int, until: int) -> None:
        self._b, self._u = brace, until
        self._li = 0
        self._nlv = 1

    def update(
        self,
        brace: int,
        until: int,
        level_index: int | None = None,
        num_levels: int | None = None,
    ) -> None:
        self._b, self._u = brace, until
        if level_index is not None:
            self._li = level_index
        if num_levels is not None:
            self._nlv = num_levels

    def render_interface(self, frame):
        import numpy as np

        if isinstance(frame, np.ndarray):
            h, w = frame.shape
            for i in range(min(self._nlv, 14)):
                cx = 1 + i * 2
                if cx >= w:
                    break
                dot = 14 if i < self._li else (11 if i == self._li else 3)
                frame[0, cx] = dot
            for i in range(min(self._b, 6)):
                frame[h - 2, 2 + i] = 11
            frame[h - 2, 10] = min(15, self._u % 16)
        return frame


def sp():
    return {
        "p": Sprite(pixels=[[9]], name="p", visible=True, collidable=True, tags=["player"]),
        "g": Sprite(pixels=[[14]], name="g", visible=True, collidable=False, tags=["goal"]),
        "w": Sprite(pixels=[[3]], name="w", visible=True, collidable=True, tags=["wall"]),
    }


S = sp()


def lvl(diff: int, rotate_every: int, brace: int, parts: list) -> Level:
    return Level(
        sprites=parts,
        grid_size=(12, 12),
        data={"difficulty": diff, "rotate_every": rotate_every, "brace_budget": brace},
    )


levels = [
    lvl(1, 10, 2, [S["p"].clone().set_position(1, 1), S["g"].clone().set_position(10, 10)]),
    lvl(
        2,
        8,
        2,
        [
            S["p"].clone().set_position(1, 5),
            S["g"].clone().set_position(10, 5),
        ]
        + [S["w"].clone().set_position(6, y) for y in range(12) if y != 5],
    ),
    lvl(3, 12, 1, [S["p"].clone().set_position(2, 2), S["g"].clone().set_position(9, 9)]),
    lvl(
        4,
        7,
        3,
        [S["p"].clone().set_position(0, 0), S["g"].clone().set_position(11, 11)]
        + [S["w"].clone().set_position(x, 4) for x in range(4, 9)],
    ),
    lvl(5, 9, 2, [S["p"].clone().set_position(5, 1), S["g"].clone().set_position(5, 10)]),
]


class Wr01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Wr01UI(0, 0)
        super().__init__(
            "wr01",
            levels,
            Camera(0, 0, 16, 16, BG, PAD, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 5],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._goal = self.current_level.get_sprites_by_tag("goal")[0]
        self._every = int(level.get_data("rotate_every") or 10)
        self._brace = int(level.get_data("brace_budget") or 2)
        self._sub = 0
        self._skip_next = False
        self._ui.update(
            self._brace,
            self._every - (self._sub % self._every),
            level_index=self.level_index,
            num_levels=len(levels),
        )

    def _rotate_world(self) -> None:
        g = self.current_level.grid_size[0]
        for s in list(self.current_level._sprites):
            nx, ny = rot_cw(g, s.x, s.y)
            s.set_position(nx, ny)

    def step(self) -> None:
        if self.action.id == GameAction.ACTION5:
            if self._brace > 0:
                self._brace -= 1
                self._skip_next = True
            self._ui.update(
                self._brace,
                self._every - (self._sub % self._every),
                level_index=self.level_index,
                num_levels=len(levels),
            )
            self.complete_action()
            return

        dx = dy = 0
        v = self.action.id.value
        if v == 1:
            dy = -1
        elif v == 2:
            dy = 1
        elif v == 3:
            dx = -1
        elif v == 4:
            dx = 1
        else:
            self.complete_action()
            return

        gw, gh = self.current_level.grid_size
        nx, ny = self._player.x + dx, self._player.y + dy
        if 0 <= nx < gw and 0 <= ny < gh:
            hit = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
            if not hit or not hit.is_collidable:
                self._player.set_position(nx, ny)

        self._sub += 1
        if self._sub % self._every == 0:
            if self._skip_next:
                self._skip_next = False
            else:
                self._rotate_world()

        if self._player.x == self._goal.x and self._player.y == self._goal.y:
            self.next_level()

        self._ui.update(
            self._brace,
            self._every - (self._sub % self._every),
            level_index=self.level_index,
            num_levels=len(levels),
        )
        self.complete_action()
