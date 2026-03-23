"""Plan #25: split/merge ghost positions."""
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
        self._split = False

    def update(self, *, level_index: int | None = None, state=None, split: bool | None = None) -> None:
        if level_index is not None:
            self._level_index = level_index
        if state is not None:
            self._state = state
        if split is not None:
            self._split = split

    def render_interface(self, f):
        import numpy as np

        from arcengine import GameState

        if not isinstance(f, np.ndarray):
            return f
        h, w = f.shape
        _r_dots(f, h, w, self._level_index, self._num_levels, 0)
        _rp(f, h, w, w - 2, h - 2, 6 if self._split else 5)
        go = self._state == GameState.GAME_OVER
        win = self._state == GameState.WIN
        _r_bar(f, h, w, go, win)
        return f

def spr():
    return {"p": Sprite(pixels=[[9]], name="p", visible=True, collidable=True, tags=["player"]),
            "g": Sprite(pixels=[[14]], name="g", visible=True, collidable=False, tags=["goal"]),
            "s": Sprite(pixels=[[7]], name="s", visible=True, collidable=False, tags=["split"]),
            "o": Sprite(pixels=[[10]], name="o", visible=True, collidable=False, tags=["observe"]),
            "w": Sprite(pixels=[[3]], name="w", visible=True, collidable=True, tags=["wall"]),
            "ghost": Sprite(pixels=[[6]], name="ghost", visible=True, collidable=False, tags=["ghost"])}
s = spr()
def lvl(d,parts):
    return Level(sprites=parts, grid_size=(10,10), data={"difficulty":d})
levels = [
    lvl(1,[s["p"].clone().set_position(1,5), s["g"].clone().set_position(8,5), s["s"].clone().set_position(3,5), s["o"].clone().set_position(6,5)]),
    lvl(2,[s["p"].clone().set_position(1,1), s["g"].clone().set_position(8,8), s["s"].clone().set_position(2,2), s["o"].clone().set_position(7,7)]),
    lvl(3,[s["p"].clone().set_position(0,5), s["g"].clone().set_position(9,5), s["s"].clone().set_position(4,5), s["o"].clone().set_position(8,5)]),
    lvl(4,[s["p"].clone().set_position(2,3), s["g"].clone().set_position(7,6), s["s"].clone().set_position(3,4), s["o"].clone().set_position(6,5), s["w"].clone().set_position(5,5)]),
    lvl(5,[s["p"].clone().set_position(1,2), s["g"].clone().set_position(8,7), s["s"].clone().set_position(2,4), s["o"].clone().set_position(7,3)]),
]
class Qt01(ARCBaseGame):
    def __init__(self):
        self._ghost_sp = None
        self._ui = U(len(levels))
        super().__init__("qt01", levels, Camera(0,0,16,16,BG,PAD,[self._ui]), False, 1, [1,2,3,4])

    def _sync_ghost_sprite(self) -> None:
        if self._split and self._gx is not None and self._gy is not None:
            if self._ghost_sp is None:
                self._ghost_sp = s["ghost"].clone().set_position(self._gx, self._gy)
                self.current_level.add_sprite(self._ghost_sp)
            else:
                self._ghost_sp.set_position(self._gx, self._gy)
        elif self._ghost_sp is not None:
            self.current_level.remove_sprite(self._ghost_sp)
            self._ghost_sp = None

    def on_set_level(self, level: Level):
        self._ghost_sp = None
        self._p = self.current_level.get_sprites_by_tag("player")[0]
        self._g = self.current_level.get_sprites_by_tag("goal")[0]
        self._split = False
        self._gx = self._gy = None
        for sp in list(self.current_level.get_sprites_by_tag("ghost")):
            self.current_level.remove_sprite(sp)
        self._ui.update(level_index=self.level_index, state=self._state, split=False)
    def _blocked(self, x, y):
        gw, gh = self.current_level.grid_size
        if not (0<=x<gw and 0<=y<gh):
            return True
        h = self.current_level.get_sprite_at(x,y,ignore_collidable=True)
        return h is not None and h.is_collidable and "wall" in h.tags
    def step(self):
        dx=dy=0
        v=self.action.id.value
        if v==1: dy=-1
        elif v==2: dy=1
        elif v==3: dx=-1
        elif v==4: dx=1
        else: self.complete_action(); return
        if not self._split:
            nx, ny = self._p.x+dx, self._p.y+dy
            if not self._blocked(nx,ny):
                self._p.set_position(nx,ny)
            hit = self.current_level.get_sprite_at(self._p.x,self._p.y,ignore_collidable=True)
            if hit and "split" in hit.tags:
                self._split = True
                self._gx, self._gy = self._p.x+1, self._p.y
            hit2 = self.current_level.get_sprite_at(self._p.x,self._p.y,ignore_collidable=True)
            if hit2 and "observe" in hit2.tags and self._split:
                self._split = False
                self._gx = self._gy = None
                self._sync_ghost_sprite()
        else:
            nx, ny = self._p.x+dx, self._p.y+dy
            gx, gy = self._gx+dx, self._gy+dy
            b1, b2 = self._blocked(nx,ny), self._blocked(gx,gy)
            if b1 and b2:
                self.lose()
                self._sync_ghost_sprite()
                self._ui.update(level_index=self.level_index, state=self._state, split=self._split)
                self.complete_action()
                return
            if not b1:
                self._p.set_position(nx,ny)
            if not b2:
                self._gx, self._gy = gx, gy
            hit = self.current_level.get_sprite_at(self._p.x,self._p.y,ignore_collidable=True)
            if hit and "observe" in hit.tags:
                self._split = False
                self._gx = self._gy = None
        self._sync_ghost_sprite()
        if self._p.x == self._g.x and self._p.y == self._g.y and not self._split:
            self.next_level()
        self._ui.update(level_index=self.level_index, state=self._state, split=self._split)
        self.complete_action()
