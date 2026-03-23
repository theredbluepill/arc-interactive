"""Plan #27: follow-the-leader chain."""
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
        self._on_exit = False
        self._tails_near = (0, 0)

    def update(
        self,
        *,
        level_index: int | None = None,
        state=None,
        on_exit: bool | None = None,
        tails_near: tuple[int, int] | None = None,
    ) -> None:
        if level_index is not None:
            self._level_index = level_index
        if state is not None:
            self._state = state
        if on_exit is not None:
            self._on_exit = on_exit
        if tails_near is not None:
            self._tails_near = tails_near

    def render_interface(self, f):
        import numpy as np

        from arcengine import GameState

        if not isinstance(f, np.ndarray):
            return f
        h, w = f.shape
        _r_dots(f, h, w, self._level_index, self._num_levels, 0)
        row_y = h - 2
        if row_y >= 0 and self._on_exit:
            ok, total = self._tails_near
            for i in range(min(total, 5)):
                _rp(f, h, w, 34 + i * 2, row_y, 14 if i < ok else 8)
        go = self._state == GameState.GAME_OVER
        win = self._state == GameState.WIN
        _r_bar(f, h, w, go, win)
        return f

def spr():
    return {"p": Sprite(pixels=[[9]], name="p", visible=True, collidable=True, tags=["player"]),
            "t": Sprite(pixels=[[6]], name="t", visible=True, collidable=True, tags=["tail"]),
            "e": Sprite(pixels=[[14]], name="e", visible=True, collidable=False, tags=["exit"])}
s = spr()
def lvl(d,parts):
    return Level(sprites=parts, grid_size=(14,10), data={"difficulty":d})
levels = [
    lvl(1,[s["p"].clone().set_position(2,5), s["t"].clone().set_position(1,5), s["t"].clone().set_position(0,5), s["t"].clone().set_position(0,4), s["e"].clone().set_position(12,5)]),
    lvl(2,[s["p"].clone().set_position(1,1), s["t"].clone().set_position(0,1), s["t"].clone().set_position(0,0), s["t"].clone().set_position(1,0), s["e"].clone().set_position(12,8)]),
    lvl(3,[s["p"].clone().set_position(3,5), s["t"].clone().set_position(2,5), s["t"].clone().set_position(1,5), s["t"].clone().set_position(0,5), s["e"].clone().set_position(11,5)]),
    lvl(4,[s["p"].clone().set_position(2,3), s["t"].clone().set_position(1,3), s["t"].clone().set_position(1,2), s["t"].clone().set_position(1,1), s["e"].clone().set_position(10,7)]),
    lvl(5,[s["p"].clone().set_position(1,5), s["t"].clone().set_position(0,5), s["t"].clone().set_position(0,4), s["t"].clone().set_position(0,3), s["e"].clone().set_position(12,5)]),
]
class Fc01(ARCBaseGame):
    def __init__(self):
        self._ui = U(len(levels))
        super().__init__("fc01", levels, Camera(0,0,16,16,BG,PAD,[self._ui]), False, 1, [1,2,3,4])
    def on_set_level(self, level: Level):
        self._p = self.current_level.get_sprites_by_tag("player")[0]
        self._tails = self.current_level.get_sprites_by_tag("tail")
        self._ex = self.current_level.get_sprites_by_tag("exit")[0]
        self._sync_chain_ui()

    def _sync_chain_ui(self) -> None:
        def near(t):
            return max(abs(t.x - self._ex.x), abs(t.y - self._ex.y)) <= 1

        on_ex = self._p.x == self._ex.x and self._p.y == self._ex.y
        ok = sum(1 for t in self._tails if near(t))
        self._ui.update(
            level_index=self.level_index,
            state=self._state,
            on_exit=on_ex,
            tails_near=(ok, len(self._tails)),
        )

    def step(self):
        dx=dy=0
        v=self.action.id.value
        if v==1: dy=-1
        elif v==2: dy=1
        elif v==3: dx=-1
        elif v==4: dx=1
        else: self.complete_action(); return
        px, py = self._p.x, self._p.y
        gw, gh = self.current_level.grid_size
        nx, ny = px+dx, py+dy
        if 0<=nx<gw and 0<=ny<gh:
            h = self.current_level.get_sprite_at(nx,ny,ignore_collidable=True)
            if not h or not h.is_collidable or "tail" in h.tags:
                if h and "tail" in h.tags:
                    self._sync_chain_ui()
                    self.lose(); self.complete_action(); return
                prev = [(px,py)] + [(t.x,t.y) for t in self._tails]
                self._p.set_position(nx,ny)
                for i, t in enumerate(self._tails):
                    t.set_position(prev[i][0], prev[i][1])
        def near(t):
            return max(abs(t.x - self._ex.x), abs(t.y - self._ex.y)) <= 1

        ok_p = self._p.x == self._ex.x and self._p.y == self._ex.y
        if ok_p and all(near(t) for t in self._tails):
            self.next_level()
        self._sync_chain_ui()
        self.complete_action()
