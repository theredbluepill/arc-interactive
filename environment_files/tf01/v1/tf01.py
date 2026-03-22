"""Plan #11: light phase gate."""
from arcengine import ARCBaseGame, Camera, Level, RenderableUserDisplay, Sprite
BG, PAD = 5, 4
class U(RenderableUserDisplay):
    def __init__(self, ph):
        self.ph = ph
        self._li = 0
        self._nlv = 1
    def update(self, ph, level_index=None, num_levels=None):
        self.ph = ph
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
            f[h-2,2] = 14 if self.ph % 4 < 2 else 8
        return f
def spr():
    return {"p": Sprite(pixels=[[9]], name="p", visible=True, collidable=True, tags=["player"]),
            "g": Sprite(pixels=[[14]], name="g", visible=True, collidable=False, tags=["goal"]),
            "c": Sprite(pixels=[[12]], name="c", visible=True, collidable=False, tags=["crossing"])}
s = spr()
def lvl(d,parts):
    return Level(sprites=parts, grid_size=(14,14), data={"difficulty":d})
levels = [
    lvl(1,[s["p"].clone().set_position(1,7), s["g"].clone().set_position(12,7), s["c"].clone().set_position(7,7)]),
    lvl(2,[s["p"].clone().set_position(2,2), s["g"].clone().set_position(11,11), s["c"].clone().set_position(6,6)]),
    lvl(3,[s["p"].clone().set_position(0,7), s["g"].clone().set_position(13,7), s["c"].clone().set_position(8,7)]),
    lvl(4,[s["p"].clone().set_position(3,3), s["g"].clone().set_position(10,10), s["c"].clone().set_position(5,8)]),
    lvl(5,[s["p"].clone().set_position(1,12), s["g"].clone().set_position(12,1), s["c"].clone().set_position(7,6)]),
]
class Tf01(ARCBaseGame):
    def __init__(self):
        self._ui = U(0)
        super().__init__("tf01", levels, Camera(0,0,16,16,BG,PAD,[self._ui]), False, 1, [1,2,3,4])
    def on_set_level(self, level: Level):
        self._p = self.current_level.get_sprites_by_tag("player")[0]
        self._g = self.current_level.get_sprites_by_tag("goal")[0]
        self._cross = {(s.x,s.y) for s in self.current_level.get_sprites_by_tag("crossing")}
        self._t = 0
        self._ui.update(self._t, level_index=self.level_index, num_levels=len(levels))
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
            if (nx,ny) in self._cross and (self._t % 4) >= 2:
                self._ui.update(self._t, level_index=self.level_index, num_levels=len(levels))
                self.complete_action(); return
            self._p.set_position(nx,ny)
        self._t += 1
        self._ui.update(self._t, level_index=self.level_index, num_levels=len(levels))
        if self._p.x==self._g.x and self._p.y==self._g.y:
            self.next_level()
        self.complete_action()
