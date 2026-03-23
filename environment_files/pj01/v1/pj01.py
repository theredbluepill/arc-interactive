"""Plan #28: stepping bolt + mirrors."""
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

    def update(self, *, level_index: int | None = None, state=None) -> None:
        if level_index is not None:
            self._level_index = level_index
        if state is not None:
            self._state = state

    def render_interface(self, f):
        import numpy as np

        from arcengine import GameState

        if not isinstance(f, np.ndarray):
            return f
        h, w = f.shape
        _r_dots(f, h, w, self._level_index, self._num_levels, 0)
        go = self._state == GameState.GAME_OVER
        win = self._state == GameState.WIN
        _r_bar(f, h, w, go, win)
        return f

def spr():
    return {"p": Sprite(pixels=[[9]], name="p", visible=True, collidable=True, tags=["player"]),
            "b": Sprite(pixels=[[8]], name="b", visible=True, collidable=False, tags=["bolt"]),
            "k": Sprite(pixels=[[11]], name="k", visible=True, collidable=False, tags=["sink"]),
            "m": Sprite(pixels=[[7]], name="m", visible=True, collidable=False, tags=["mirror","fs"])}
s = spr()
def lvl(d,parts):
    return Level(sprites=parts, grid_size=(14,14), data={"difficulty":d})
levels = [
    lvl(1,[s["p"].clone().set_position(0,7), s["b"].clone().set_position(2,7), s["k"].clone().set_position(12,7)]),
    lvl(2,[s["p"].clone().set_position(0,3), s["b"].clone().set_position(1,7), s["k"].clone().set_position(12,3)]),
    lvl(3,[s["p"].clone().set_position(1,1), s["b"].clone().set_position(2,10), s["k"].clone().set_position(10,2)]),
    lvl(4,[s["p"].clone().set_position(2,2), s["b"].clone().set_position(3,7), s["k"].clone().set_position(11,11)]),
    lvl(5,[s["p"].clone().set_position(0,0), s["b"].clone().set_position(2,5), s["k"].clone().set_position(13,13)]),
]
def _mirror_paint(sp: Sprite) -> None:
    if "fs" in sp.tags:
        sp.pixels = [[7]]
    else:
        sp.pixels = [[15]]


class Pj01(ARCBaseGame):
    def __init__(self):
        self._ui = U(len(levels))
        super().__init__("pj01", levels, Camera(0,0,16,16,BG,PAD,[self._ui]), False, 1, [1,2,3,4,6])
    def on_set_level(self, level: Level):
        self._p = self.current_level.get_sprites_by_tag("player")[0]
        self._ui.update(level_index=self.level_index, state=self._state)

        self._bolt = self.current_level.get_sprites_by_tag("bolt")[0]
        self._sink = self.current_level.get_sprites_by_tag("sink")[0]
        self._bdx, self._bdy = 1, 0
        for sp in self.current_level.get_sprites_by_tag("mirror"):
            _mirror_paint(sp)
    def step(self):
        if self.action.id == GameAction.ACTION6:
            px, py = int(self.action.data.get("x",0)), int(self.action.data.get("y",0))
            h = self.camera.display_to_grid(px, py)
            if h:
                gx, gy = int(h[0]), int(h[1])
                cell = self.current_level.get_sprite_at(gx,gy,ignore_collidable=True)
                if not cell:
                    m = spr()["m"].clone().set_position(gx,gy)
                    _mirror_paint(m)
                    self.current_level.add_sprite(m)
                elif "mirror" in cell.tags:
                    if "fs" in cell.tags:
                        cell.tags.remove("fs")
                        cell.tags.append("bs")
                    else:
                        cell.tags.remove("bs")
                        cell.tags.append("fs")
                    _mirror_paint(cell)
            self._ui.update(level_index=self.level_index, state=self._state)
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
                self._p.set_position(nx,ny)
        bx, by = self._bolt.x + self._bdx, self._bolt.y + self._bdy
        if not (0 <= bx < gw and 0 <= by < gh):
            self._ui.update(level_index=self.level_index, state=self._state)
            self.complete_action()
            return
        mh = self.current_level.get_sprite_at(bx, by, ignore_collidable=True)
        if mh and "mirror" in mh.tags:
            if "fs" in mh.tags:
                self._bdx, self._bdy = -self._bdy, -self._bdx
            else:
                self._bdx, self._bdy = self._bdy, self._bdx
        self._bolt.set_position(bx, by)
        if self._bolt.x==self._p.x and self._bolt.y==self._p.y:
            self._ui.update(level_index=self.level_index, state=self._state)
            self.lose(); self.complete_action(); return
        if self._bolt.x==self._sink.x and self._bolt.y==self._sink.y:
            self.next_level()
        self._ui.update(level_index=self.level_index, state=self._state)
        self.complete_action()
