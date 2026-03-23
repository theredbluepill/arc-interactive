"""Plan #8: fallow timer per cell."""
from arcengine import ARCBaseGame, GameState, Camera, Level, RenderableUserDisplay, Sprite
BG, PAD = 5, 4
def _rp(frame, h, w, x, y, c):
    if 0 <= x < w and 0 <= y < h:
        frame[y, x] = c


def _r_dots(frame, h, w, li, n, y0=0):
    for i in range(min(n, 14)):
        cx = 1 + i * 2
        if cx >= w:
            break
        c = 14 if i < li else (11 if i == li else 3)
        _rp(frame, h, w, cx, y0, c)


def _r_bar(frame, h, w, game_over, win):
    if not (game_over or win):
        return
    r = h - 3
    if r < 0:
        return
    c = 14 if win else 8
    for x in range(min(w, 16)):
        _rp(frame, h, w, x, r, c)


class U(RenderableUserDisplay):
    def __init__(self, num_levels: int) -> None:
        self._num_levels = num_levels
        self._level_index = 0
        self._state = None
        self._fallow = 4
        self._tick = 0
        self._reentry_remain = 0

    def update(
        self,
        *,
        level_index: int | None = None,
        state=None,
        fallow: int | None = None,
        tick: int | None = None,
        reentry_remain: int | None = None,
    ) -> None:
        if level_index is not None:
            self._level_index = level_index
        if state is not None:
            self._state = state
        if fallow is not None:
            self._fallow = fallow
        if tick is not None:
            self._tick = tick
        if reentry_remain is not None:
            self._reentry_remain = max(0, int(reentry_remain))

    def render_interface(self, f):
        import numpy as np

        from arcengine import GameState

        if not isinstance(f, np.ndarray):
            return f
        h, w = f.shape
        _r_dots(f, h, w, self._level_index, self._num_levels, 0)
        # Fallow depth F + world step (ties revisits to time without prose).
        ff = max(1, min(8, self._fallow))
        for i in range(ff):
            f[h - 2, 10 + i] = 11
        f[h - 2, 9] = min(15, self._tick % 16)
        # Per-cell re-entry remainder (orange row h-3); distinct from F (yellow) and t pixel.
        rr = min(8, self._reentry_remain)
        for i in range(rr):
            _rp(f, h, w, 1 + i, h - 3, 12)
        go = self._state == GameState.GAME_OVER
        win = self._state == GameState.WIN
        _r_bar(f, h, w, go, win)
        return f

def spr():
    return {"p": Sprite(pixels=[[9]], name="p", visible=True, collidable=True, tags=["player"]),
            "g": Sprite(pixels=[[14]], name="g", visible=True, collidable=False, tags=["goal"])}
s = spr()
def lvl(d,parts,F):
    return Level(sprites=parts, grid_size=(10,10), data={"difficulty":d,"fallow":F})
levels = [lvl(1,[s["p"].clone().set_position(1,1), s["g"].clone().set_position(8,8)],4),
          lvl(2,[s["p"].clone().set_position(0,0), s["g"].clone().set_position(9,9)],5),
          lvl(3,[s["p"].clone().set_position(2,2), s["g"].clone().set_position(7,7)],3),
          lvl(4,[s["p"].clone().set_position(1,5), s["g"].clone().set_position(8,5)],4),
          lvl(5,[s["p"].clone().set_position(0,9), s["g"].clone().set_position(9,0)],5)]
class Cf01(ARCBaseGame):
    def __init__(self):
        self._ui = U(len(levels))
        super().__init__("cf01", levels, Camera(0,0,16,16,BG,PAD,[self._ui]), False, 1, [1,2,3,4])
    def on_set_level(self, level: Level):
        self._p = self.current_level.get_sprites_by_tag("player")[0]
        self._g = self.current_level.get_sprites_by_tag("goal")[0]
        self._F = int(level.get_data("fallow"))
        self._last = {}
        self._t = 0
        self._ui.update(
            level_index=self.level_index,
            state=self._state,
            fallow=self._F,
            tick=self._t,
            reentry_remain=0,
        )
    def _reentry_remain(self) -> int:
        k = (self._p.x, self._p.y)
        if k not in self._last:
            return 0
        return max(0, self._last[k] + self._F - self._t)

    def step(self):
        dx=dy=0
        v=self.action.id.value
        if v==1: dy=-1
        elif v==2: dy=1
        elif v==3: dx=-1
        elif v==4: dx=1
        else: self.complete_action(); return
        gw, gh = self.current_level.grid_size
        nx, ny = self._p.x+dx, self._p.y+dy
        if 0<=nx<gw and 0<=ny<gh:
            k = (nx,ny)
            if k in self._last and self._t - self._last[k] < self._F:
                self._ui.update(
                    level_index=self.level_index,
                    state=self._state,
                    fallow=self._F,
                    tick=self._t,
                    reentry_remain=self._reentry_remain(),
                )
                self.lose(); self.complete_action(); return
            self._p.set_position(nx,ny)
            self._last[k] = self._t
        self._t += 1
        if self._p.x==self._g.x and self._p.y==self._g.y:
            self.next_level()
        self._ui.update(
            level_index=self.level_index,
            state=self._state,
            fallow=self._F,
            tick=self._t,
            reentry_remain=self._reentry_remain(),
        )
        self.complete_action()
