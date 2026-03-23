"""Plan #19: ordered letter tiles."""
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
        self._seq_len = 0
        self._ni = 0

    def update(
        self,
        *,
        level_index: int | None = None,
        state=None,
        seq_len: int | None = None,
        ni: int | None = None,
    ) -> None:
        if level_index is not None:
            self._level_index = level_index
        if state is not None:
            self._state = state
        if seq_len is not None:
            self._seq_len = seq_len
        if ni is not None:
            self._ni = ni

    def render_interface(self, f):
        import numpy as np

        from arcengine import GameState

        if not isinstance(f, np.ndarray):
            return f
        h, w = f.shape
        _r_dots(f, h, w, self._level_index, self._num_levels, 0)
        r = h - 2
        if r >= 0 and self._seq_len > 0:
            for i in range(min(self._seq_len, 12)):
                cx = 1 + i * 2
                if cx >= w:
                    break
                _rp(f, h, w, cx, r, 14 if i < self._ni else (11 if i == self._ni else 3))
        go = self._state == GameState.GAME_OVER
        win = self._state == GameState.WIN
        _r_bar(f, h, w, go, win)
        return f


# Distinct palette per letter (raster-discoverable); avoid 5 bg, 9 player, 14 goal.
_HUE = [11, 12, 13, 6, 7, 8, 15, 1, 2, 3, 4, 10, 0]


def L(letter, x, y):
    u = letter.upper()
    c = _HUE[(ord(u) - ord("A")) % len(_HUE)] if "A" <= u <= "Z" else 10
    sp = Sprite(pixels=[[c]], name=letter, visible=True, collidable=False, tags=["letter", letter])
    return sp.set_position(x, y)
def spr():
    return {"p": Sprite(pixels=[[9]], name="p", visible=True, collidable=True, tags=["player"]),
            "g": Sprite(pixels=[[14]], name="g", visible=True, collidable=False, tags=["goal"])}
s = spr()
def lvl(d, seq, positions, goal):
    parts = [s["p"].clone().set_position(*positions[0]), s["g"].clone().set_position(*goal)]
    for i, ch in enumerate(seq):
        parts.append(L(ch, positions[i+1][0], positions[i+1][1]).set_position(*positions[i+1]))
    return Level(sprites=parts, grid_size=(9,11), data={"difficulty":d,"seq":list(seq)})
levels = [
    lvl(1, "AB", [(1,5),(3,5),(7,5)], (7,9)),
    lvl(2, "ABC", [(1,1),(2,3),(4,5),(7,8)], (7,9)),
    lvl(3, "AB", [(2,9),(5,5),(8,2)], (8,3)),
    lvl(4, "ABC", [(0,0),(4,4),(6,2),(8,10)], (7,10)),
    lvl(5, "AB", [(3,3),(6,6),(3,9)], (3,8)),
]
class Lp01(ARCBaseGame):
    def __init__(self):
        self._ui = U(len(levels))
        super().__init__("lp01", levels, Camera(0,0,16,16,BG,PAD,[self._ui]), False, 1, [1,2,3,4])
    def on_set_level(self, level: Level):
        self._p = self.current_level.get_sprites_by_tag("player")[0]
        self._ui.update(level_index=self.level_index, state=self._state)

        self._g = self.current_level.get_sprites_by_tag("goal")[0]
        self._seq = list(level.get_data("seq"))
        self._ni = 0
        self._ui.update(
            level_index=self.level_index,
            state=self._state,
            seq_len=len(self._seq),
            ni=self._ni,
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
            if h and "letter" in h.tags:
                want = self._seq[self._ni] if self._ni < len(self._seq) else None
                got = [t for t in h.tags if len(t)==1 and t.isalpha()][0]
                if want and got == want:
                    self._ni += 1
                    self.current_level.remove_sprite(h)
                else:
                    self._ui.update(
                        level_index=self.level_index,
                        state=self._state,
                        seq_len=len(self._seq),
                        ni=self._ni,
                    )
                    self.lose(); self.complete_action(); return
            elif not h or not h.is_collidable:
                self._p.set_position(nx,ny)
        if self._ni >= len(self._seq) and self._p.x==self._g.x and self._p.y==self._g.y:
            self.next_level()
        self._ui.update(
            level_index=self.level_index,
            state=self._state,
            seq_len=len(self._seq),
            ni=self._ni,
        )
        self.complete_action()
