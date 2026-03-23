"""Plan #7: touch bonus pads for +step budget."""
from arcengine import ARCBaseGame, Camera, Level, RenderableUserDisplay, Sprite
BG, PAD = 5, 4
class U(RenderableUserDisplay):
    def __init__(self, s, b):
        self.s, self.b = s, b
        self._li = 0
        self._nlv = 1
    def update(self, s, b, level_index=None, num_levels=None):
        self.s, self.b = s, b
        if level_index is not None:
            self._li = level_index
        if num_levels is not None:
            self._nlv = num_levels
    def render_interface(self, f):
        import numpy as np
        if isinstance(f, np.ndarray):
            h, w = f.shape
            for i in range(min(self._nlv, 14)):
                cx = 1 + i * 2
                if cx >= w:
                    break
                dot = 14 if i < self._li else (11 if i == self._li else 3)
                f[0, cx] = dot
            # self.s = steps used, self.b = move cap — show remaining moves (discoverable budget).
            rem = max(0, self.b - self.s)
            for i in range(min(rem, 8)):
                f[h - 2, 2 + i] = 11
        return f
def spr():
    return {"p": Sprite(pixels=[[9]], name="p", visible=True, collidable=True, tags=["player"]),
            "g": Sprite(pixels=[[14]], name="g", visible=True, collidable=False, tags=["goal"]),
            "b": Sprite(pixels=[[10]], name="b", visible=True, collidable=False, tags=["bonus"])}
s = spr()
def lvl(d, parts, lim, add):
    return Level(sprites=parts, grid_size=(10,10), data={"difficulty":d,"limit":lim,"bonus":add})
levels = [
    lvl(1,[s["p"].clone().set_position(1,1), s["g"].clone().set_position(8,8), s["b"].clone().set_position(4,4)], 25, 20),
    lvl(2,[s["p"].clone().set_position(0,0), s["g"].clone().set_position(9,9), s["b"].clone().set_position(3,3), s["b"].clone().set_position(6,6)], 30, 15),
    lvl(3,[s["p"].clone().set_position(1,5), s["g"].clone().set_position(8,5), s["b"].clone().set_position(5,5)], 22, 25),
    lvl(4,[s["p"].clone().set_position(2,2), s["g"].clone().set_position(7,7), s["b"].clone().set_position(4,5)], 28, 18),
    lvl(5,[s["p"].clone().set_position(0,9), s["g"].clone().set_position(9,0), s["b"].clone().set_position(5,2), s["b"].clone().set_position(5,7)], 35, 12),
]
class Au01(ARCBaseGame):
    def __init__(self):
        self._ui = U(0,0)
        super().__init__("au01", levels, Camera(0,0,16,16,BG,PAD,[self._ui]), False, 1, [1,2,3,4])
    def on_set_level(self, level: Level):
        self._p = self.current_level.get_sprites_by_tag("player")[0]
        self._g = self.current_level.get_sprites_by_tag("goal")[0]
        self._lim = int(level.get_data("limit"))
        self._bonus = int(level.get_data("bonus"))
        self._steps = 0
        self._ui.update(self._steps, self._lim, level_index=self.level_index, num_levels=len(levels))
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
            h = self.current_level.get_sprite_at(nx,ny,ignore_collidable=True)
            if not h or not h.is_collidable:
                self._p.set_position(nx,ny)
                if h and "bonus" in h.tags:
                    self.current_level.remove_sprite(h)
                    self._lim += self._bonus
        self._steps += 1
        self._ui.update(self._steps, self._lim, level_index=self.level_index, num_levels=len(levels))
        if self._p.x==self._g.x and self._p.y==self._g.y:
            self.next_level()
        elif self._steps >= self._lim:
            self.lose()
        self.complete_action()
