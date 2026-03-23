"""Plan #23: tumbler combo."""
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
        self._t = (0, 0, 0)
        self._tar = (0, 0, 0)
        self._sep_flash = 0

    def update(
        self,
        *,
        level_index: int | None = None,
        state=None,
        t=None,
        tar=None,
        tumbler_pulse: bool = False,
    ) -> None:
        if level_index is not None:
            self._level_index = level_index
        if state is not None:
            self._state = state
        if t is not None:
            self._t = tuple(t)
        if tar is not None:
            self._tar = tuple(tar)
        if tumbler_pulse:
            self._sep_flash = 3
        elif self._sep_flash > 0:
            self._sep_flash -= 1

    def render_interface(self, f):
        import numpy as np

        from arcengine import GameState

        if not isinstance(f, np.ndarray):
            return f
        h, w = f.shape
        _r_dots(f, h, w, self._level_index, self._num_levels, 0)
        r = h - 2
        if r >= 0:
            dc = 11 if self._sep_flash > 0 else 5
            _rp(f, h, w, 7, r, dc)
            for i in range(3):
                _rp(f, h, w, 1 + i * 2, r, 8 + (self._t[i] % 6))
                _rp(f, h, w, 9 + i * 2, r, 8 + (self._tar[i] % 6))
        go = self._state == GameState.GAME_OVER
        win = self._state == GameState.WIN
        _r_bar(f, h, w, go, win)
        return f

def spr():
    return {"p": Sprite(pixels=[[9]], name="p", visible=True, collidable=True, tags=["player"]),
            "g": Sprite(pixels=[[14]], name="g", visible=True, collidable=False, tags=["goal"]),
            "d": Sprite(pixels=[[3]], name="d", visible=True, collidable=True, tags=["door"])}
s = spr()
def lvl(d, t0, t1, t2):
    return Level(sprites=[s["p"].clone().set_position(1,5), s["g"].clone().set_position(8,5), s["d"].clone().set_position(5,5)],
                 grid_size=(10,10), data={"difficulty":d,"target":[t0,t1,t2]})
levels = [lvl(1,2,3,1), lvl(2,1,1,4), lvl(3,0,5,2), lvl(4,3,3,3), lvl(5,4,2,0)]
class Lk01(ARCBaseGame):
    def __init__(self):
        self._ui = U(len(levels))
        super().__init__("lk01", levels, Camera(0,0,16,16,BG,PAD,[self._ui]), False, 1, [1,2,3,4])
    def on_set_level(self, level: Level):
        self._p = self.current_level.get_sprites_by_tag("player")[0]
        self._g = self.current_level.get_sprites_by_tag("goal")[0]
        ds = self.current_level.get_sprites_by_tag("door")
        self._door = ds[0] if ds else None
        self._t = [0, 0, 0]
        self._tar = list(level.get_data("target"))
        self._ui.update(
            level_index=self.level_index,
            state=self._state,
            t=self._t,
            tar=self._tar,
        )

    def step(self):
        v = self.action.id.value
        pulse = False
        if self._door is not None:
            if v == 1:
                self._t[0] = (self._t[0] + 1) % 6
                pulse = True
            elif v == 2:
                self._t[1] = (self._t[1] + 1) % 6
                pulse = True
            elif v == 3:
                self._t[2] = (self._t[2] + 1) % 6
                pulse = True
            if self._t == self._tar and self._door in self.current_level._sprites:
                self.current_level.remove_sprite(self._door)
                self._door = None
        else:
            dx = dy = 0
            if v == 1:
                dy = -1
            elif v == 2:
                dy = 1
            elif v == 3:
                dx = -1
            elif v == 4:
                dx = 1
            gw, gh = self.current_level.grid_size
            nx, ny = self._p.x + dx, self._p.y + dy
            if 0 <= nx < gw and 0 <= ny < gh:
                hit = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
                if not hit or not hit.is_collidable:
                    self._p.set_position(nx, ny)
        if self._p.x == self._g.x and self._p.y == self._g.y:
            self.next_level()
        self._ui.update(
            level_index=self.level_index,
            state=self._state,
            t=self._t,
            tar=self._tar,
            tumbler_pulse=pulse,
        )
        self.complete_action()
