"""Plan #6: guard cone + scent grid."""
from arcengine import ARCBaseGame, GameState, Camera, GameAction, Level, RenderableUserDisplay, Sprite
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
        self._mask = 0
        self._scent_px = 0

    def update(
        self,
        *,
        level_index: int | None = None,
        state=None,
        mask: int | None = None,
        scent_px: int | None = None,
    ) -> None:
        if level_index is not None:
            self._level_index = level_index
        if state is not None:
            self._state = state
        if mask is not None:
            self._mask = mask
        if scent_px is not None:
            self._scent_px = scent_px

    def render_interface(self, f):
        import numpy as np

        from arcengine import GameState

        if not isinstance(f, np.ndarray):
            return f
        h, w = f.shape
        _r_dots(f, h, w, self._level_index, self._num_levels, 0)
        f[h - 2, 4] = 11 if self._mask > 0 else 5
        # Local scent at player (coarse); rises with trail + decays — testable under guard LOS.
        f[h - 2, 6] = min(15, max(0, self._scent_px))
        go = self._state == GameState.GAME_OVER
        win = self._state == GameState.WIN
        _r_bar(f, h, w, go, win)
        return f

def spr():
    return {"p": Sprite(pixels=[[9]], name="p", visible=True, collidable=True, tags=["player"]),
            "g": Sprite(pixels=[[14]], name="g", visible=True, collidable=False, tags=["goal"]),
            "w": Sprite(pixels=[[3]], name="w", visible=True, collidable=True, tags=["wall"]),
            "u": Sprite(pixels=[[8]], name="u", visible=True, collidable=False, tags=["guard"])}
s = spr()
def lvl(d,parts): return Level(sprites=parts, grid_size=(14,14), data={"difficulty":d})
levels = [lvl(1,[s["p"].clone().set_position(1,7), s["g"].clone().set_position(12,7), s["u"].clone().set_position(6,7)]),
          lvl(2,[s["p"].clone().set_position(1,1), s["g"].clone().set_position(12,12), s["u"].clone().set_position(7,6), s["w"].clone().set_position(5,5)]),
          lvl(3,[s["p"].clone().set_position(0,7), s["g"].clone().set_position(13,7), s["u"].clone().set_position(8,7)]),
          lvl(4,[s["p"].clone().set_position(2,2), s["g"].clone().set_position(11,11), s["u"].clone().set_position(6,4)]),
          lvl(5,[s["p"].clone().set_position(1,12), s["g"].clone().set_position(12,1), s["u"].clone().set_position(7,7)])]
class Sc01(ARCBaseGame):
    def __init__(self):
        self._ui = U(len(levels))
        super().__init__("sc01", levels, Camera(0,0,16,16,BG,PAD,[self._ui]), False, 1, [1,2,3,4,5])
    def on_set_level(self, level: Level):
        self._p = self.current_level.get_sprites_by_tag("player")[0]
        self._ui.update(level_index=self.level_index, state=self._state, mask=0, scent_px=0)

        self._g = self.current_level.get_sprites_by_tag("goal")[0]
        self._gu = self.current_level.get_sprites_by_tag("guard")[0]
        gw, gh = level.grid_size
        self._sc = [[0.0]*gw for _ in range(gh)]
        self._mask = 0
    def _cone(self, px, py, gx, gy):
        return gy == py and px > gx
    def step(self):
        if self.action.id == GameAction.ACTION5:
            self._mask = 3
            sx = int(min(15, self._sc[self._p.y][self._p.x]))
            self._ui.update(
                level_index=self.level_index,
                state=self._state,
                mask=self._mask,
                scent_px=sx,
            )
            self.complete_action(); return
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
            h = self.current_level.get_sprite_at(nx,ny,ignore_collidable=True)
            if not h or not h.is_collidable:
                self._sc[self._p.y][self._p.x] += 2.0
                self._p.set_position(nx,ny)
        for y in range(gh):
            for x in range(gw):
                self._sc[y][x] *= 0.85
        if self._mask > 0:
            self._mask -= 1
        else:
            if self._cone(self._p.x,self._p.y,self._gu.x,self._gu.y) and self._sc[self._p.y][self._p.x] > 1.5:
                sx = int(min(15, self._sc[self._p.y][self._p.x]))
                self._ui.update(
                    level_index=self.level_index,
                    state=self._state,
                    mask=self._mask,
                    scent_px=sx,
                )
                self.lose(); self.complete_action(); return
        if self._p.x==self._g.x and self._p.y==self._g.y:
            self.next_level()
        sx = int(min(15, self._sc[self._p.y][self._p.x]))
        self._ui.update(
            level_index=self.level_index,
            state=self._state,
            mask=self._mask,
            scent_px=sx,
        )
        self.complete_action()
