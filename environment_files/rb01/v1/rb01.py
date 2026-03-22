"""Plan #20: beat-gated moves."""
from arcengine import ARCBaseGame, Camera, GameState, Level, RenderableUserDisplay, Sprite

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
        self._beat_t = 0
        self._beat_b = 3

    def update(
        self,
        *,
        level_index: int | None = None,
        state=None,
        beat_t: int | None = None,
        beat_b: int | None = None,
    ) -> None:
        if level_index is not None:
            self._level_index = level_index
        if state is not None:
            self._state = state
        if beat_t is not None:
            self._beat_t = beat_t
        if beat_b is not None:
            self._beat_b = beat_b

    def render_interface(self, f):
        import numpy as np

        if not isinstance(f, np.ndarray):
            return f
        h, w = f.shape
        _r_dots(f, h, w, self._level_index, self._num_levels, 0)
        b = max(1, self._beat_b)
        f[h - 2, 2] = 14 if self._beat_t % b == 0 else 2
        go = self._state == GameState.GAME_OVER
        win = self._state == GameState.WIN
        _r_bar(f, h, w, go, win)
        return f


def spr():
    return {"p": Sprite(pixels=[[9]], name="p", visible=True, collidable=True, tags=["player"]),
            "g": Sprite(pixels=[[14]], name="g", visible=True, collidable=False, tags=["goal"])}
s = spr()
def lvl(d,parts,B=3):
    return Level(sprites=parts, grid_size=(11,11), data={"difficulty":d,"beat":B})
levels = [lvl(i,[s["p"].clone().set_position(1,5), s["g"].clone().set_position(9,5)]) for i in range(1,6)]
class Rb01(ARCBaseGame):
    def __init__(self):
        self._ui = U(len(levels))
        super().__init__("rb01", levels, Camera(0,0,16,16,BG,PAD,[self._ui]), False, 1, [1,2,3,4])
    def on_set_level(self, level: Level):
        self._p = self.current_level.get_sprites_by_tag("player")[0]
        self._g = self.current_level.get_sprites_by_tag("goal")[0]
        self._B = int(level.get_data("beat") or 3)
        self._t = 0
        self._ui.update(
            level_index=self.level_index,
            state=self._state,
            beat_t=0,
            beat_b=self._B,
        )
    def step(self):
        dx = dy = 0
        v = self.action.id.value
        if v == 1:
            dy = -1
        elif v == 2:
            dy = 1
        elif v == 3:
            dx = -1
        elif v == 4:
            dx = 1
        else:
            self.complete_action()
            return
        self._t += 1
        self._ui.update(
            level_index=self.level_index,
            state=self._state,
            beat_t=self._t,
            beat_b=self._B,
        )
        if self._t % self._B != 0:
            self.complete_action()
            return
        gw, gh = self.current_level.grid_size
        nx, ny = self._p.x+dx, self._p.y+dy
        if 0<=nx<gw and 0<=ny<gh:
            h = self.current_level.get_sprite_at(nx,ny,ignore_collidable=True)
            if not h or not h.is_collidable:
                self._p.set_position(nx,ny)
        if self._p.x==self._g.x and self._p.y==self._g.y:
            self.next_level()
        self._ui.update(level_index=self.level_index, state=self._state, beat_t=self._t, beat_b=self._B)
        self.complete_action()
