"""Plan #17: pushable ticking bombs."""
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
            "g": Sprite(pixels=[[14]], name="g", visible=True, collidable=False, tags=["goal"]),
            "b": Sprite(pixels=[[8]], name="b", visible=True, collidable=True, tags=["bomb"]),
            "w": Sprite(pixels=[[3]], name="w", visible=True, collidable=True, tags=["wall"]),
            "weak": Sprite(pixels=[[2]], name="weak", visible=True, collidable=True, tags=["weak"])}
s = spr()
def lvl(d, parts):
    return Level(sprites=parts, grid_size=(12,12), data={"difficulty":d})
levels = [
    lvl(1,[s["p"].clone().set_position(1,6), s["g"].clone().set_position(10,6), s["b"].clone().set_position(4,6), s["weak"].clone().set_position(7,6)]),
    lvl(2,[s["p"].clone().set_position(1,1), s["g"].clone().set_position(10,10), s["b"].clone().set_position(5,5), s["weak"].clone().set_position(8,5), s["weak"].clone().set_position(8,6)]),
    lvl(3,[s["p"].clone().set_position(2,6), s["g"].clone().set_position(10,6), s["b"].clone().set_position(5,6), s["weak"].clone().set_position(8,4), s["weak"].clone().set_position(8,8)]),
    lvl(4,[s["p"].clone().set_position(0,0), s["g"].clone().set_position(11,11), s["b"].clone().set_position(3,3), s["weak"].clone().set_position(6,6)]),
    lvl(5,[s["p"].clone().set_position(1,5), s["g"].clone().set_position(10,5), s["b"].clone().set_position(5,5), s["weak"].clone().set_position(9,5)]),
]
class Fb01(ARCBaseGame):
    def __init__(self):
        self._ui = U(len(levels))
        super().__init__("fb01", levels, Camera(0,0,16,16,BG,PAD,[self._ui]), False, 1, [1,2,3,4])
    def on_set_level(self, level: Level):
        self._p = self.current_level.get_sprites_by_tag("player")[0]
        self._ui.update(level_index=self.level_index, state=self._state)

        self._g = self.current_level.get_sprites_by_tag("goal")[0]
        self._fuse = {id(b): 5 for b in self.current_level.get_sprites_by_tag("bomb")}
        self._paint_bombs()

    def _paint_bombs(self) -> None:
        # Fuse remaining → distinct hues (remap from any prior fuse color).
        pal = {5: 8, 4: 12, 3: 11, 2: 2, 1: 7}
        hues = (8, 12, 11, 2, 7)
        for b in self.current_level.get_sprites_by_tag("bomb"):
            k = max(1, self._fuse.get(id(b), 5))
            tgt = pal[k]
            for c in hues:
                if c != tgt:
                    b.color_remap(c, tgt)

    def _tick(self):
        dead = []
        for b in self.current_level.get_sprites_by_tag("bomb"):
            k = id(b)
            self._fuse[k] = self._fuse.get(k, 5) - 1
            if self._fuse[k] <= 0:
                dead.append(b)
        for b in dead:
            bx, by = b.x, b.y
            self.current_level.remove_sprite(b)
            if id(b) in self._fuse:
                del self._fuse[id(b)]
            for sp in list(self.current_level._sprites):
                if "weak" in sp.tags and abs(sp.x - bx) + abs(sp.y - by) <= 1:
                    self.current_level.remove_sprite(sp)
            if abs(self._p.x - bx) + abs(self._p.y - by) <= 1:
                self.lose()
                return True
        return False
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
            self._ui.update(level_index=self.level_index, state=self._state)
            self.complete_action()
            return
        gw, gh = self.current_level.grid_size
        nx, ny = self._p.x + dx, self._p.y + dy
        if 0 <= nx < gw and 0 <= ny < gh:
            h = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
            if h and "bomb" in h.tags:
                bx, by = nx + dx, ny + dy
                if 0 <= bx < gw and 0 <= by < gh:
                    bh = self.current_level.get_sprite_at(bx, by, ignore_collidable=True)
                    if bh and bh.is_collidable and "weak" not in bh.tags:
                        self._ui.update(level_index=self.level_index, state=self._state)
                        self.complete_action()
                        return
                    if bh and "weak" in bh.tags:
                        self.current_level.remove_sprite(bh)
                    h.set_position(bx, by)
                    self._p.set_position(nx, ny)
            elif not h or not h.is_collidable:
                self._p.set_position(nx, ny)
        if self._tick():
            self._paint_bombs()
            self._ui.update(level_index=self.level_index, state=self._state)
            self.complete_action()
            return
        self._paint_bombs()
        if self._p.x == self._g.x and self._p.y == self._g.y:
            self.next_level()
        self._ui.update(level_index=self.level_index, state=self._state)
        self.complete_action()
