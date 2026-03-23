"""Plan #3: ACTION5 toggles plane A/B; walls tagged ``plane_a`` or ``plane_b`` collide only on that plane."""

from arcengine import ARCBaseGame, Camera, GameAction, Level, RenderableUserDisplay, Sprite

BG, PAD = 5, 4


class Dp01UI(RenderableUserDisplay):
    def __init__(self, plane: str) -> None:
        self._p = plane
        self._li = 0
        self._nlv = 1
        self._reject_frames = 0

    def flash_reject(self) -> None:
        self._reject_frames = 3

    def update(
        self,
        plane: str,
        level_index: int | None = None,
        num_levels: int | None = None,
    ) -> None:
        self._p = plane
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
            # Bottom: active **plane** A=blue / B=magenta; top-right yellow = spatial overlay mode (not timeline).
            frame[h - 2, 2] = 9 if self._p == "a" else 7
            frame[1, min(w - 2, 20)] = 11
            if self._reject_frames > 0:
                frame[2, min(3, w - 1)] = 11
                self._reject_frames -= 1
        return frame


def S():
    return {
        "p": Sprite(pixels=[[9]], name="p", visible=True, collidable=True, tags=["player"]),
        "g": Sprite(pixels=[[14]], name="g", visible=True, collidable=False, tags=["goal"]),
        "wa": Sprite(pixels=[[3]], name="wa", visible=True, collidable=True, tags=["wall", "plane_a"]),
        "wb": Sprite(pixels=[[2]], name="wb", visible=True, collidable=True, tags=["wall", "plane_b"]),
    }


s = S()


def lvl(d: int, parts: list) -> Level:
    return Level(sprites=parts, grid_size=(10, 14), data={"difficulty": d})


levels = [
    lvl(1, [s["p"].clone().set_position(1, 1), s["g"].clone().set_position(8, 12), s["wa"].clone().set_position(5, 6)]),
    lvl(2, [s["p"].clone().set_position(1, 1), s["g"].clone().set_position(8, 12), s["wb"].clone().set_position(5, 6)]),
    lvl(
        3,
        [
            s["p"].clone().set_position(2, 2),
            s["g"].clone().set_position(7, 11),
            s["wa"].clone().set_position(4, 7),
            s["wb"].clone().set_position(6, 7),
        ],
    ),
    lvl(
        4,
        [s["p"].clone().set_position(0, 0), s["g"].clone().set_position(9, 13)]
        + [s["wa"].clone().set_position(3, y) for y in range(6, 10)]
        + [s["wb"].clone().set_position(7, y) for y in range(4, 8)],
    ),
    lvl(
        5,
        [s["p"].clone().set_position(1, 6), s["g"].clone().set_position(8, 6)]
        + [s["wa"].clone().set_position(x, 3) for x in range(3, 8)]
        + [s["wb"].clone().set_position(x, 9) for x in range(3, 8)],
    ),
]


class Dp01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Dp01UI("a")
        super().__init__(
            "dp01",
            levels,
            Camera(0, 0, 16, 16, BG, PAD, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 5],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._goal = self.current_level.get_sprites_by_tag("goal")[0]
        self._plane_a = True
        self._ui.update("a", level_index=self.level_index, num_levels=len(levels))

    def _wall_blocks(self, sp: Sprite | None) -> bool:
        if sp is None or not sp.is_collidable or "wall" not in sp.tags:
            return False
        if self._plane_a:
            return "plane_a" in sp.tags
        return "plane_b" in sp.tags

    def step(self) -> None:
        if self.action.id == GameAction.ACTION5:
            self._plane_a = not self._plane_a
            self._ui.update(
                "a" if self._plane_a else "b",
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
            if not self._wall_blocks(hit):
                self._player.set_position(nx, ny)
            else:
                self._ui.flash_reject()
        else:
            self._ui.flash_reject()
        if self._player.x == self._goal.x and self._player.y == self._goal.y:
            self.next_level()
        self._ui.update(
            "a" if self._plane_a else "b",
            level_index=self.level_index,
            num_levels=len(levels),
        )
        self.complete_action()
