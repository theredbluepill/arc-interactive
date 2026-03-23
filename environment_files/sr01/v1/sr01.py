"""Plan #30: RGB aura + XOR door."""
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
        self._ar = self._ag = self._ab = 0
        self._tr = self._tg = self._tb = 0

    def update(
        self,
        *,
        level_index: int | None = None,
        state=None,
        aura: tuple[int, int, int] | None = None,
        target: tuple[int, int, int] | None = None,
    ) -> None:
        if level_index is not None:
            self._level_index = level_index
        if state is not None:
            self._state = state
        if aura is not None:
            self._ar, self._ag, self._ab = aura
        if target is not None:
            self._tr, self._tg, self._tb = target

    def render_interface(self, f):
        import numpy as np

        from arcengine import GameState

        if not isinstance(f, np.ndarray):
            return f
        h, w = f.shape
        _r_dots(f, h, w, self._level_index, self._num_levels, 0)
        # Target triple + match locks (R,G,B): discoverable without repo text.
        base_x = 24
        row_y = h - 2
        if row_y >= 0:
            for i, (cur, tgt, hi, lo) in enumerate(
                (
                    (self._ar, self._tr, 8, 3),
                    (self._ag, self._tg, 14, 3),
                    (self._ab, self._tb, 10, 3),
                ),
            ):
                x0 = base_x + i * 6
                _rp(f, h, w, x0, row_y, hi if tgt else lo)
                _rp(f, h, w, x0 + 1, row_y, hi if cur else lo)
                match = cur == tgt
                _rp(f, h, w, x0 + 3, row_y, 14 if match else 8)
        go = self._state == GameState.GAME_OVER
        win = self._state == GameState.WIN
        _r_bar(f, h, w, go, win)
        return f

def spr():
    return {"p": Sprite(pixels=[[9]], name="p", visible=True, collidable=True, tags=["player"]),
            "g": Sprite(pixels=[[14]], name="g", visible=True, collidable=False, tags=["goal"]),
            "dr": Sprite(pixels=[[8]], name="dr", visible=True, collidable=False, tags=["zone","r"]),
            "dg": Sprite(pixels=[[14]], name="dg", visible=True, collidable=False, tags=["zone","gn"]),
            "db": Sprite(pixels=[[10]], name="db", visible=True, collidable=False, tags=["zone","b"]),
            "wash": Sprite(pixels=[[1]], name="wash", visible=True, collidable=False, tags=["wash"]),
            "door": Sprite(pixels=[[3]], name="door", visible=True, collidable=True, tags=["door"])}
s = spr()
def lvl(d, parts, tr, tg, tb):
    return Level(sprites=parts, grid_size=(12,12), data={"difficulty":d,"tr":tr,"tg":tg,"tb":tb})
levels = [
    lvl(1,[s["p"].clone().set_position(1,6), s["g"].clone().set_position(10,6), s["dr"].clone().set_position(3,6), s["dg"].clone().set_position(5,6), s["door"].clone().set_position(8,6)], 1,1,0),
    lvl(2,[s["p"].clone().set_position(2,2), s["g"].clone().set_position(9,9), s["db"].clone().set_position(4,4), s["wash"].clone().set_position(6,6), s["door"].clone().set_position(7,7)], 0,0,1),
    lvl(3,[s["p"].clone().set_position(1,1), s["g"].clone().set_position(10,10), s["dr"].clone().set_position(3,3), s["dg"].clone().set_position(4,4), s["db"].clone().set_position(5,5), s["door"].clone().set_position(8,8)], 1,0,1),
    lvl(4,[s["p"].clone().set_position(0,6), s["g"].clone().set_position(11,6), s["wash"].clone().set_position(2,6), s["dr"].clone().set_position(5,6), s["door"].clone().set_position(9,6)], 1,0,0),
    lvl(5,[s["p"].clone().set_position(2,5), s["g"].clone().set_position(9,5), s["dg"].clone().set_position(4,5), s["db"].clone().set_position(6,5), s["door"].clone().set_position(8,5)], 0,1,1),
]
class Sr01(ARCBaseGame):
    def __init__(self):
        self._ui = U(len(levels))
        super().__init__("sr01", levels, Camera(0,0,16,16,BG,PAD,[self._ui]), False, 1, [1,2,3,4])
    def on_set_level(self, level: Level):
        self._p = self.current_level.get_sprites_by_tag("player")[0]
        self._g = self.current_level.get_sprites_by_tag("goal")[0]
        self._ar, self._ag, self._ab = 0, 0, 0
        self._tr = int(level.get_data("tr"))
        self._tg = int(level.get_data("tg"))
        self._tb = int(level.get_data("tb"))
        ds = self.current_level.get_sprites_by_tag("door")
        self._door = ds[0] if ds else None
        self._ui.update(
            level_index=self.level_index,
            state=self._state,
            aura=(self._ar, self._ag, self._ab),
            target=(self._tr, self._tg, self._tb),
        )

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
        hit = self.current_level.get_sprite_at(self._p.x,self._p.y,ignore_collidable=True)
        if hit and "wash" in hit.tags:
            self._ar, self._ag, self._ab = 0, 0, 0
        elif hit and "zone" in hit.tags:
            if "r" in hit.tags:
                self._ar ^= 1
            if "gn" in hit.tags:
                self._ag ^= 1
            if "b" in hit.tags:
                self._ab ^= 1
        if ((self._ar ^ self._tr) | (self._ag ^ self._tg) | (self._ab ^ self._tb)) == 0 and self._door and self._door in self.current_level._sprites:
            self.current_level.remove_sprite(self._door)
            self._door = None
        if self._p.x==self._g.x and self._p.y==self._g.y:
            self.next_level()
        self._ui.update(
            level_index=self.level_index,
            state=self._state,
            aura=(self._ar, self._ag, self._ab),
            target=(self._tr, self._tg, self._tb),
        )
        self.complete_action()
