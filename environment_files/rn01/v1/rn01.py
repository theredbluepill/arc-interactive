"""Plan #4: rope segment between adjacent anchors via two ACTION6 clicks."""
from arcengine import ARCBaseGame, Camera, GameAction, Level, RenderableUserDisplay, Sprite

BG, PAD = 5, 4

class Rn01UI(RenderableUserDisplay):
    def __init__(self, p: bool) -> None:
        self._p = p
        self._li = 0
        self._nlv = 1
    def update(self, p: bool, level_index: int | None = None, num_levels: int | None = None) -> None:
        self._p = p
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
            frame[h-2,2] = 11 if self._p else 5
        return frame

def spr():
    return {
        "p": Sprite(pixels=[[9]], name="p", visible=True, collidable=True, tags=["player"]),
        "g": Sprite(pixels=[[14]], name="g", visible=True, collidable=False, tags=["goal"]),
        "w": Sprite(pixels=[[4]], name="w", visible=True, collidable=True, tags=["water"]),
        "a": Sprite(pixels=[[11]], name="a", visible=True, collidable=False, tags=["anchor"]),
        "r": Sprite(pixels=[[12]], name="r", visible=True, collidable=False, tags=["rope"]),
    }
s = spr()

def lvl(d, parts):
    return Level(sprites=parts, grid_size=(12, 12), data={"difficulty": d})

levels = [
    lvl(1, [s["p"].clone().set_position(2,5), s["g"].clone().set_position(10,5), s["w"].clone().set_position(6,5),
            s["a"].clone().set_position(5,5), s["a"].clone().set_position(7,5)]),
    lvl(2, [s["p"].clone().set_position(2,6), s["g"].clone().set_position(10,6), s["w"].clone().set_position(6,6),
            s["a"].clone().set_position(5,6), s["a"].clone().set_position(7,6)]),
    lvl(3, [s["p"].clone().set_position(1,1), s["g"].clone().set_position(10,10), s["w"].clone().set_position(5,5),
            s["a"].clone().set_position(4,5), s["a"].clone().set_position(6,5)]),
    lvl(4, [s["p"].clone().set_position(5,2), s["g"].clone().set_position(5,10), s["w"].clone().set_position(5,6),
            s["a"].clone().set_position(5,5), s["a"].clone().set_position(5,7)]),
    lvl(5, [s["p"].clone().set_position(3,6), s["g"].clone().set_position(9,6), s["w"].clone().set_position(6,6),
            s["a"].clone().set_position(5,6), s["a"].clone().set_position(7,6)]),
]

class Rn01(ARCBaseGame):
    def __init__(self):
        self._ui = Rn01UI(False)
        super().__init__("rn01", levels, Camera(0,0,16,16,BG,PAD,[self._ui]), False, 1, [1,2,3,4,6])
    def on_set_level(self, level: Level):
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._goal = self.current_level.get_sprites_by_tag("goal")[0]
        self._pend = None
        self._ui.update(False, level_index=self.level_index, num_levels=len(levels))
    def _walk(self, nx, ny):
        gw, gh = self.current_level.grid_size
        if not (0 <= nx < gw and 0 <= ny < gh):
            return
        hit = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
        if hit and hit.is_collidable and "water" in hit.tags:
            return
        self._player.set_position(nx, ny)
    def step(self):
        if self.action.id == GameAction.ACTION6:
            px, py = int(self.action.data.get("x",0)), int(self.action.data.get("y",0))
            h = self.camera.display_to_grid(px, py)
            if h:
                gx, gy = int(h[0]), int(h[1])
                sp = self.current_level.get_sprite_at(gx, gy, ignore_collidable=True)
                if sp and "anchor" in sp.tags:
                    if self._pend is None:
                        self._pend = (gx, gy)
                    else:
                        ax, ay = self._pend
                        self._pend = None
                        if abs(ax-gx)+abs(ay-gy) == 2 and (ax==gx or ay==gy):
                            mx, my = (ax+gx)//2, (ay+gy)//2
                            mid = self.current_level.get_sprite_at(mx, my, ignore_collidable=True)
                            if mid and "water" in mid.tags:
                                self.current_level.remove_sprite(mid)
                                self.current_level.add_sprite(spr()["r"].clone().set_position(mx, my))
                    self._ui.update(
                        self._pend is not None,
                        level_index=self.level_index,
                        num_levels=len(levels),
                    )
            self.complete_action()
            return
        dx = dy = 0
        v = self.action.id.value
        if v==1: dy=-1
        elif v==2: dy=1
        elif v==3: dx=-1
        elif v==4: dx=1
        else:
            self.complete_action(); return
        self._walk(self._player.x+dx, self._player.y+dy)
        self._ui.update(self._pend is not None, level_index=self.level_index, num_levels=len(levels))
        if self._player.x == self._goal.x and self._player.y == self._goal.y:
            self.next_level()
        self.complete_action()
