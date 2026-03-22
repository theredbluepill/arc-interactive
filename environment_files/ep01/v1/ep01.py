"""Plan #9: visit-count entry cost + global pain budget."""
from arcengine import ARCBaseGame, Camera, Level, RenderableUserDisplay, Sprite
BG, PAD = 5, 4
class U(RenderableUserDisplay):
    def __init__(self, pain):
        self.p = pain
        self._li = 0
        self._nlv = 1
    def update(self, pain, level_index=None, num_levels=None):
        self.p = pain
        if level_index is not None:
            self._li = level_index
        if num_levels is not None:
            self._nlv = num_levels
    def render_interface(self, f):
        import numpy as np
        if isinstance(f, np.ndarray):
            h,w=f.shape
            for i in range(min(self._nlv, 14)):
                cx = 1 + i * 2
                if cx >= w:
                    break
                dot = 14 if i < self._li else (11 if i == self._li else 3)
                f[0, cx] = dot
            c = 8 if self.p < 5 else 14
            f[h-2,2]=c
        return f
def spr():
    return {"p": Sprite(pixels=[[9]], name="p", visible=True, collidable=True, tags=["player"]),
            "g": Sprite(pixels=[[14]], name="g", visible=True, collidable=False, tags=["goal"])}
s = spr()
def lvl(d,parts,budget):
    return Level(sprites=parts, grid_size=(12,12), data={"difficulty":d,"budget":budget})
levels = [lvl(1,[s["p"].clone().set_position(1,1), s["g"].clone().set_position(10,10)],40),
          lvl(2,[s["p"].clone().set_position(0,0), s["g"].clone().set_position(11,11)],35),
          lvl(3,[s["p"].clone().set_position(2,2), s["g"].clone().set_position(9,9)],45),
          lvl(4,[s["p"].clone().set_position(1,6), s["g"].clone().set_position(10,6)],38),
          lvl(5,[s["p"].clone().set_position(5,1), s["g"].clone().set_position(5,10)],42)]
class Ep01(ARCBaseGame):
    def __init__(self):
        self._ui = U(40)
        super().__init__("ep01", levels, Camera(0,0,16,16,BG,PAD,[self._ui]), False, 1, [1,2,3,4])
    def on_set_level(self, level: Level):
        self._p = self.current_level.get_sprites_by_tag("player")[0]
        self._g = self.current_level.get_sprites_by_tag("goal")[0]
        self._bud = int(level.get_data("budget"))
        self._pain = 0
        self._vc = {}
        self._ui.update(self._bud - self._pain, level_index=self.level_index, num_levels=len(levels))
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
            c = self._vc.get((nx,ny),0)
            self._pain += c
            if self._pain > self._bud:
                self._ui.update(self._bud - self._pain, level_index=self.level_index, num_levels=len(levels))
                self.lose(); self.complete_action(); return
            self._vc[(nx,ny)] = c + 1
            self._p.set_position(nx,ny)
        self._ui.update(self._bud - self._pain, level_index=self.level_index, num_levels=len(levels))
        if self._p.x==self._g.x and self._p.y==self._g.y:
            self.next_level()
        self.complete_action()
