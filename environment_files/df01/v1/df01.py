"""Plan #5: integer temperature field diffuses; sources in data; win on goal when temp in [t_lo,t_hi]."""

from arcengine import ARCBaseGame, Camera, GameAction, Level, RenderableUserDisplay, Sprite

BG, PAD = 5, 4


class Df01UI(RenderableUserDisplay):
    def __init__(self, t: int, lo: int, hi: int) -> None:
        self._t = t
        self._lo = lo
        self._hi = hi
        self._li = 0
        self._nlv = 1
        self._click_pos: tuple[int, int] | None = None
        self._click_frames = 0

    def set_click(self, x: int, y: int) -> None:
        self._click_pos = (x, y)
        self._click_frames = 8

    def update(
        self,
        t: int,
        lo: int | None = None,
        hi: int | None = None,
        level_index: int | None = None,
        num_levels: int | None = None,
    ) -> None:
        self._t = t
        if lo is not None:
            self._lo = lo
        if hi is not None:
            self._hi = hi
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
            # Coarse temp readout + goal band markers (learnable without prose).
            tt = min(15, max(0, (self._t + 24) // 4))
            frame[h - 2, 2] = tt
            lo_c = min(15, max(0, (self._lo + 24) // 4))
            hi_c = min(15, max(0, (self._hi + 24) // 4))
            frame[h - 2, 4] = lo_c
            frame[h - 2, 5] = hi_c
            frame[h - 2, 6] = 14 if self._lo <= self._t <= self._hi else 8
            if self._click_pos and self._click_frames > 0:
                cx, cy = self._click_pos
                hit = 11
                for px, py in (
                    (cx, cy),
                    (cx - 1, cy),
                    (cx + 1, cy),
                    (cx, cy - 1),
                    (cx, cy + 1),
                ):
                    if 0 <= px < w and 0 <= py < h:
                        frame[py, px] = hit
                self._click_frames -= 1
            else:
                self._click_pos = None
        return frame


def spr():
    return {
        "p": Sprite(pixels=[[9]], name="p", visible=True, collidable=True, tags=["player"]),
        "g": Sprite(pixels=[[14]], name="g", visible=True, collidable=False, tags=["goal"]),
        "h": Sprite(pixels=[[8]], name="h", visible=True, collidable=False, tags=["hot"]),
        "c": Sprite(pixels=[[10]], name="c", visible=True, collidable=False, tags=["cold"]),
    }


s = spr()


def lvl(d: int, parts: list, lo: int, hi: int) -> Level:
    return Level(sprites=parts, grid_size=(16, 16), data={"difficulty": d, "t_lo": lo, "t_hi": hi})


levels = [
    lvl(1, [s["p"].clone().set_position(1, 1), s["g"].clone().set_position(14, 14), s["h"].clone().set_position(8, 8)], 8, 20),
    lvl(2, [s["p"].clone().set_position(2, 2), s["g"].clone().set_position(13, 13), s["h"].clone().set_position(4, 4), s["c"].clone().set_position(12, 4)], 5, 15),
    lvl(3, [s["p"].clone().set_position(0, 8), s["g"].clone().set_position(15, 8), s["h"].clone().set_position(7, 8), s["c"].clone().set_position(9, 8)], 6, 14),
    lvl(4, [s["p"].clone().set_position(8, 1), s["g"].clone().set_position(8, 14), s["h"].clone().set_position(8, 4), s["c"].clone().set_position(8, 12)], 7, 16),
    lvl(5, [s["p"].clone().set_position(1, 14), s["g"].clone().set_position(14, 1), s["h"].clone().set_position(3, 3), s["c"].clone().set_position(13, 13)], 4, 12),
]


class Df01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Df01UI(0, 0, 0)
        super().__init__(
            "df01",
            levels,
            Camera(0, 0, 16, 16, BG, PAD, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 6],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._goal = self.current_level.get_sprites_by_tag("goal")[0]
        self._lo = int(level.get_data("t_lo"))
        self._hi = int(level.get_data("t_hi"))
        self._ui.update(
            0,
            lo=self._lo,
            hi=self._hi,
            level_index=self.level_index,
            num_levels=len(levels),
        )
        gw, gh = level.grid_size
        self._temp = [[0 for _ in range(gw)] for _ in range(gh)]
        for y in range(gh):
            for x in range(gw):
                sp = level.get_sprite_at(x, y, ignore_collidable=True)
                if sp and "hot" in sp.tags:
                    self._temp[y][x] = 40
                elif sp and "cold" in sp.tags:
                    self._temp[y][x] = -10

    def _diffuse(self) -> None:
        gw, gh = self.current_level.grid_size
        old = [row[:] for row in self._temp]
        for y in range(gh):
            for x in range(gw):
                s = old[y][x]
                n = 1
                for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < gw and 0 <= ny < gh:
                        s += old[ny][nx]
                        n += 1
                self._temp[y][x] = s // n

    def step(self) -> None:
        if self.action.id == GameAction.ACTION6:
            px, py = int(self.action.data.get("x", 0)), int(self.action.data.get("y", 0))
            self._ui.set_click(px, py)
            h = self.camera.display_to_grid(px, py)
            if h:
                gx, gy = int(h[0]), int(h[1])
                for dx in range(-1, 2):
                    for dy in range(-1, 2):
                        nx, ny = gx + dx, gy + dy
                        gw, gh = self.current_level.grid_size
                        if 0 <= nx < gw and 0 <= ny < gh:
                            self._temp[ny][nx] = max(-20, self._temp[ny][nx] - 2)
            t = self._temp[self._player.y][self._player.x]
            self._ui.update(
                t,
                lo=self._lo,
                hi=self._hi,
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
            self._player.set_position(nx, ny)
        self._diffuse()
        t = self._temp[self._player.y][self._player.x]
        self._ui.update(
            t,
            lo=self._lo,
            hi=self._hi,
            level_index=self.level_index,
            num_levels=len(levels),
        )
        if self._player.x == self._goal.x and self._player.y == self._goal.y and self._lo <= t <= self._hi:
            self.next_level()
        self.complete_action()
