"""sy04: mirror across diagonal y=x; template on i<j; build on x>y."""

from __future__ import annotations

from arcengine import ARCBaseGame, Camera, Level, RenderableUserDisplay, Sprite

BG, PAD = 5, 4
G = 11
MAX_MOVES = 55

PAT = Sprite(pixels=[[9]], name="pat", visible=True, collidable=False, tags=["template"])
PLAY = Sprite(pixels=[[14]], name="pb", visible=True, collidable=False, tags=["player_block"])
DIAG = Sprite(pixels=[[3]], name="d", visible=True, collidable=False, tags=["diag"])


class Sy04UI(RenderableUserDisplay):
    CLICK_ANIM_FRAMES = 16

    def __init__(self, rem: int, need: int, have: int) -> None:
        self._rem = rem
        self._need = need
        self._have = have
        self._click_pos = None
        self._click_frames = 0

    def update(self, rem: int, need: int, have: int) -> None:
        self._rem = rem
        self._need = need
        self._have = have

    def set_click(self, fx: int, fy: int) -> None:
        self._click_pos = (fx, fy)
        self._click_frames = Sy04UI.CLICK_ANIM_FRAMES

    @staticmethod
    def _plot(frame, h, w, px, py, c):
        if 0 <= px < w and 0 <= py < h:
            frame[py, px] = c

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        if self._click_pos and self._click_frames > 0:
            cx, cy = self._click_pos
            ph = Sy04UI.CLICK_ANIM_FRAMES - self._click_frames
            r = (ph % 4) + 1
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    if max(abs(dx), abs(dy)) == r:
                        self._plot(frame, h, w, cx + dx, cy + dy, 12)
            self._click_frames -= 1
        else:
            self._click_pos = None
        for i in range(min(self._need, 8)):
            self._plot(frame, h, w, 2 + i, h - 2, 14 if i < self._have else 4)
        self._plot(frame, h, w, w - 3, 2, 8 if self._rem < 15 else 11)
        return frame


def mk(template: list[tuple[int, int]], diff: int) -> Level:
    sl: list[Sprite] = []
    for k in range(G):
        sl.append(DIAG.clone().set_position(k, k))
    for i, j in template:
        if i < j:
            sl.append(PAT.clone().set_position(i, j))
    return Level(
        sprites=sl,
        grid_size=(G, G),
        data={
            "template": [list(p) for p in template],
            "max_moves": MAX_MOVES + diff * 5,
            "difficulty": diff,
        },
    )


def mirrors(ts: list[tuple[int, int]]) -> set[tuple[int, int]]:
    return {(j, i) for i, j in ts if i < j}


levels = [
    mk([(2, 5), (3, 7), (1, 4)], 1),
    mk([(1, 3), (2, 6), (4, 8), (2, 4)], 2),
    mk([(1, 2), (2, 5), (3, 6), (4, 9), (1, 8)], 3),
    mk([(2, 3), (3, 5), (4, 7), (2, 7), (1, 6), (3, 8)], 4),
    mk([(1, 4), (2, 5), (3, 7), (4, 8), (2, 8), (3, 9), (1, 9)], 5),
    mk([(2, 4), (3, 5), (4, 6), (5, 7), (2, 6), (3, 8), (4, 9)], 6),
    mk([(1, 5), (2, 7), (3, 4), (4, 9), (5, 8), (6, 9), (2, 9), (3, 7)], 7),
]


class Sy04(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Sy04UI(MAX_MOVES, 0, 0)
        self._placed: list[Sprite] = []
        self._want: set[tuple[int, int]] = set()
        self._moves = 0
        self._mmax = MAX_MOVES
        self._end = 0
        self._pend = False
        super().__init__(
            "sy04",
            levels,
            Camera(0, 0, G, G, BG, PAD, [self._ui]),
            False,
            1,
            [6],
        )

    def on_set_level(self, level: Level) -> None:
        raw = level.get_data("template")
        self._template = [(int(a), int(b)) for a, b in raw]
        self._want = mirrors(self._template)
        self._mmax = level.get_data("max_moves")
        self._moves = 0
        self._placed = [
            s
            for s in self.current_level.get_sprites_by_tag("player_block")
        ]
        self._end = 0
        self._pend = False
        self._sync_ui()

    def _sync_ui(self) -> None:
        ps = {(b.x, b.y) for b in self._placed}
        ok = len(ps & self._want)
        self._ui.update(self._mmax - self._moves, len(self._want), ok)

    def _g2p(self, gx: int, gy: int) -> tuple[int, int]:
        sc = min(64 // G, 64 // G)
        p = (64 - G * sc) // 2
        return gx * sc + sc // 2 + p, gy * sc + sc // 2 + p

    def _win(self) -> bool:
        return {(b.x, b.y) for b in self._placed} == self._want

    def step(self) -> None:
        if self._end > 0:
            self._end -= 1
            self._sync_ui()
            if self._end == 0 and self._pend:
                self.next_level()
                self._pend = False
            self.complete_action()
            return

        self._moves += 1
        c = self.camera.display_to_grid(
            self.action.data.get("x", 0), self.action.data.get("y", 0)
        )
        if c:
            gx, gy = int(c[0]), int(c[1])
            self._ui.set_click(*self._g2p(gx, gy))
            if gx > gy:
                ex = self.current_level.get_sprite_at(
                    gx, gy, ignore_collidable=True
                )
                if ex and "player_block" in ex.tags:
                    self.current_level.remove_sprite(ex)
                    self._placed.remove(ex)
                else:
                    if not ex or "player_block" not in getattr(ex, "tags", []):
                        nb = PLAY.clone().set_position(gx, gy)
                        self.current_level.add_sprite(nb)
                        self._placed.append(nb)

        self._sync_ui()
        if self._win():
            self._pend = True
            self._end = 12
        elif self._moves >= self._mmax:
            self.lose()
        self.complete_action()
