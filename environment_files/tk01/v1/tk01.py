"""Plan #13: ACTION5 tug nearest block."""
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
        self._block_on_goal = False

    def update(self, *, level_index: int | None = None, state=None, block_on_goal: bool | None = None) -> None:
        if level_index is not None:
            self._level_index = level_index
        if state is not None:
            self._state = state
        if block_on_goal is not None:
            self._block_on_goal = block_on_goal

    def render_interface(self, f):
        import numpy as np

        from arcengine import GameState

        if not isinstance(f, np.ndarray):
            return f
        h, w = f.shape
        _r_dots(f, h, w, self._level_index, self._num_levels, 0)
        if self._block_on_goal:
            _rp(f, h, w, 12, h - 2, 11)
        go = self._state == GameState.GAME_OVER
        win = self._state == GameState.WIN
        _r_bar(f, h, w, go, win)
        return f

def spr():
    return {"p": Sprite(pixels=[[9]], name="p", visible=True, collidable=True, tags=["player"]),
            "g": Sprite(pixels=[[14]], name="g", visible=True, collidable=False, tags=["goal"]),
            "b": Sprite(pixels=[[15]], name="b", visible=True, collidable=True, tags=["block"]),
            "w": Sprite(pixels=[[3]], name="w", visible=True, collidable=True, tags=["wall"])}
s = spr()
def lvl(d,parts):
    return Level(sprites=parts, grid_size=(10,10), data={"difficulty":d})
levels = [
    lvl(1,[s["p"].clone().set_position(1,5), s["g"].clone().set_position(8,5), s["b"].clone().set_position(5,5)]),
    lvl(2,[s["p"].clone().set_position(2,2), s["g"].clone().set_position(8,8), s["b"].clone().set_position(6,4)]),
    lvl(3,[s["p"].clone().set_position(1,1), s["g"].clone().set_position(8,8), s["b"].clone().set_position(4,4), s["w"].clone().set_position(5,4)]),
    lvl(4,[s["p"].clone().set_position(0,5), s["g"].clone().set_position(9,5), s["b"].clone().set_position(7,5)]),
    lvl(5,[s["p"].clone().set_position(3,3), s["g"].clone().set_position(7,7), s["b"].clone().set_position(5,6)]),
]
class Tk01(ARCBaseGame):
    def __init__(self):
        self._ui = U(len(levels))
        super().__init__("tk01", levels, Camera(0,0,16,16,BG,PAD,[self._ui]), False, 1, [1,2,3,4,5])
    def on_set_level(self, level: Level):
        self._p = self.current_level.get_sprites_by_tag("player")[0]
        self._g = self.current_level.get_sprites_by_tag("goal")[0]
        self._blocks = self.current_level.get_sprites_by_tag("block")
        self._ui.update(
            level_index=self.level_index,
            state=self._state,
            block_on_goal=any(b.x == self._g.x and b.y == self._g.y for b in self._blocks),
        )

    def step(self):
        if self.action.id == GameAction.ACTION5:
            best = None
            bd = 999
            for b in self._blocks:
                d = abs(b.x-self._p.x)+abs(b.y-self._p.y)
                if d < bd:
                    bd, best = d, b
            if best and bd > 0:
                dx = (1 if best.x < self._p.x else (-1 if best.x > self._p.x else 0))
                dy = (1 if best.y < self._p.y else (-1 if best.y > self._p.y else 0))
                if dx != 0 and dy != 0:
                    if abs(best.x-self._p.x) > abs(best.y-self._p.y): dy = 0
                    else: dx = 0
                nx, ny = best.x+dx, best.y+dy
                gw, gh = self.current_level.grid_size
                if 0<=nx<gw and 0<=ny<gh:
                    h = self.current_level.get_sprite_at(nx,ny,ignore_collidable=True)
                    if not h or (not h.is_collidable) or h is best:
                        best.set_position(nx,ny)
            bog = any(b.x == self._g.x and b.y == self._g.y for b in self._blocks)
            self._ui.update(level_index=self.level_index, state=self._state, block_on_goal=bog)
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
            if h and "block" in h.tags:
                bx, by = nx+dx, ny+dy
                if 0<=bx<gw and 0<=by<gh:
                    bh = self.current_level.get_sprite_at(bx,by,ignore_collidable=True)
                    if not bh or not bh.is_collidable:
                        h.set_position(bx,by)
                        self._p.set_position(nx,ny)
            elif not h or not h.is_collidable:
                self._p.set_position(nx,ny)
        bog = any(b.x == self._g.x and b.y == self._g.y for b in self._blocks)
        if bog:
            self.next_level()
        self._ui.update(level_index=self.level_index, state=self._state, block_on_goal=bog)
        self.complete_action()
