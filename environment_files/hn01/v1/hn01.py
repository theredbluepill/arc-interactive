"""Plan #15: three-peg Hanoi with three disks."""
from arcengine import (
    ARCBaseGame,
    Camera,
    GameAction,
    GameState,
    Level,
    RenderableUserDisplay,
    Sprite,
)

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
        self._reject = 0

    def update(self, *, level_index: int | None = None, state=None, reject: bool = False) -> None:
        if level_index is not None:
            self._level_index = level_index
        if state is not None:
            self._state = state
        if reject:
            self._reject = 3
        elif self._reject > 0:
            self._reject -= 1

    def render_interface(self, f):
        import numpy as np

        if not isinstance(f, np.ndarray):
            return f
        h, w = f.shape
        _r_dots(f, h, w, self._level_index, self._num_levels, 0)
        if self._reject > 0:
            _rp(f, h, w, 14, h - 2, 8)
        go = self._state == GameState.GAME_OVER
        win = self._state == GameState.WIN
        _r_bar(f, h, w, go, win)
        return f

def spr():
    return {"d1": Sprite(pixels=[[11]], name="d1", visible=True, collidable=False, tags=["disk","1"]),
            "d2": Sprite(pixels=[[12]], name="d2", visible=True, collidable=False, tags=["disk","2"]),
            "d3": Sprite(pixels=[[13]], name="d3", visible=True, collidable=False, tags=["disk","3"]),
            "peg": Sprite(pixels=[[3]], name="peg", visible=True, collidable=True, tags=["peg"])}
s = spr()
PEGX = (2, 5, 8)
BASEY = 9


def lvl(d):
    parts = [s["peg"].clone().set_position(x, BASEY) for x in PEGX]
    parts += [s["d3"].clone().set_position(2, BASEY-1), s["d2"].clone().set_position(2, BASEY-2), s["d1"].clone().set_position(2, BASEY-3)]
    return Level(sprites=parts, grid_size=(10,12), data={"difficulty":d})
levels = [lvl(i) for i in range(1,6)]
class Hn01(ARCBaseGame):
    def __init__(self):
        self._ui = U(len(levels))
        super().__init__("hn01", levels, Camera(0,0,16,16,BG,PAD,[self._ui]), False, 1, [1,2,3,5])
    def on_set_level(self, level: Level):
        self._st = [[3,2,1], [], []]
        self._ui.update(level_index=self.level_index, state=self._state)

        self._hand = None
        self._peg = 0
        self._ds = {1: None, 2: None, 3: None}
        for sp in self.current_level._sprites:
            if "disk" not in sp.tags:
                continue
            for t in sp.tags:
                if t.isdigit():
                    self._ds[int(t)] = sp
        self._layout()
    def _layout(self):
        for pi, stack in enumerate(self._st):
            x = PEGX[pi]
            for i, sz in enumerate(stack):
                sp = self._ds[sz]
                if sp is not None:
                    sp.set_position(x, BASEY - 1 - i)
        if self._hand:
            sp = self._ds[self._hand]
            if sp is not None:
                sp.set_position(PEGX[self._peg], 2)
    def step(self):
        v = self.action.id.value
        rej = False
        if v in (1,2,3):
            self._peg = v - 1
        elif self.action.id == GameAction.ACTION5:
            st = self._st[self._peg]
            if self._hand is None and st:
                self._hand = st.pop()
            elif self._hand is not None:
                top = st[-1] if st else 99
                if top > self._hand:
                    st.append(self._hand)
                    self._hand = None
                else:
                    rej = True
        self._layout()
        if self._st[2] == [3,2,1]:
            self.next_level()
        self._ui.update(level_index=self.level_index, state=self._state, reject=rej)
        self.complete_action()
