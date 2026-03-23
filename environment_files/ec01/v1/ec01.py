"""Plan #12: vertical mirror ghost."""
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
        self._reject_frames = 0

    def flash_reject(self) -> None:
        self._reject_frames = 3

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
        if self._reject_frames > 0:
            f[2, min(3, w - 1)] = 11
            self._reject_frames -= 1
        go = self._state == GameState.GAME_OVER
        win = self._state == GameState.WIN
        _r_bar(f, h, w, go, win)
        return f

def spr():
    return {"p": Sprite(pixels=[[9]], name="p", visible=True, collidable=True, tags=["player"]),
            "g": Sprite(pixels=[[14]], name="g", visible=True, collidable=False, tags=["goal"]),
            "w": Sprite(pixels=[[3]], name="w", visible=True, collidable=True, tags=["wall"]),
            "e": Sprite(pixels=[[7]], name="e", visible=True, collidable=False, tags=["echo"])}
s = spr()
def lvl(d,parts):
    return Level(sprites=parts, grid_size=(12,12), data={"difficulty":d})
levels = [
    lvl(1,[s["p"].clone().set_position(2,6), s["e"].clone().set_position(9,6), s["g"].clone().set_position(5,6)]),
    lvl(2,[s["p"].clone().set_position(1,1), s["e"].clone().set_position(10,1), s["g"].clone().set_position(5,10), s["w"].clone().set_position(8,5)]),
    lvl(3,[s["p"].clone().set_position(3,3), s["e"].clone().set_position(8,3), s["g"].clone().set_position(5,9)]),
    lvl(4,[s["p"].clone().set_position(0,6), s["e"].clone().set_position(11,6), s["g"].clone().set_position(6,6)]),
    lvl(5,[s["p"].clone().set_position(2,2), s["e"].clone().set_position(9,2), s["g"].clone().set_position(5,8), s["w"].clone().set_position(4,5), s["w"].clone().set_position(7,5)]),
]
class Ec01(ARCBaseGame):
    def __init__(self):
        self._ui = U(len(levels))
        super().__init__("ec01", levels, Camera(0,0,16,16,BG,PAD,[self._ui]), False, 1, [1,2,3,4])
    def on_set_level(self, level: Level):
        self._p = self.current_level.get_sprites_by_tag("player")[0]
        self._ui.update(level_index=self.level_index, state=self._state)

        self._e = self.current_level.get_sprites_by_tag("echo")[0]
        self._g = self.current_level.get_sprites_by_tag("goal")[0]
        self._mx = 5
    def step(self):
        dx=dy=0
        v=self.action.id.value
        if v==1: dy=-1
        elif v==2: dy=1
        elif v==3: dx=-1
        elif v==4: dx=1
        else: self.complete_action(); return
        gdx = -dx
        gw, gh = self.current_level.grid_size
        enx, eny = self._e.x + gdx, self._e.y + dy
        if not (0 <= enx < gw and 0 <= eny < gh):
            self._ui.flash_reject()
            self._ui.update(level_index=self.level_index, state=self._state)
            self.complete_action(); return
        eh = self.current_level.get_sprite_at(enx, eny, ignore_collidable=True)
        if eh and eh.is_collidable and "wall" in eh.tags:
            self._ui.flash_reject()
            self._ui.update(level_index=self.level_index, state=self._state)
            self.complete_action(); return
        nx, ny = self._p.x + dx, self._p.y + dy
        if not (0 <= nx < gw and 0 <= ny < gh):
            self._ui.flash_reject()
            self._ui.update(level_index=self.level_index, state=self._state)
            self.complete_action(); return
        h = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
        if h and h.is_collidable:
            self._ui.flash_reject()
            self._ui.update(level_index=self.level_index, state=self._state)
            self.complete_action(); return
        self._e.set_position(enx, eny)
        self._p.set_position(nx, ny)
        if self._p.x==self._g.x and self._p.y==self._g.y:
            self.next_level()
        self._ui.update(level_index=self.level_index, state=self._state)
        self.complete_action()
