"""Plan #21: pheromone + one ant."""

from arcengine import ARCBaseGame, Camera, GameAction, GameState, Level, RenderableUserDisplay, Sprite

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
        self._state: GameState | None = None
        self._ph_disp: list[list[int]] | None = None
        self._px = self._py = self._ax = self._ay = -1

    def update(
        self,
        *,
        level_index: int | None = None,
        state: GameState | None = None,
        ph: list[list[int]] | None = None,
        px: int | None = None,
        py: int | None = None,
        ax: int | None = None,
        ay: int | None = None,
    ) -> None:
        if level_index is not None:
            self._level_index = level_index
        if state is not None:
            self._state = state
        if ph is not None:
            self._ph_disp = [list(row) for row in ph]
        if px is not None:
            self._px = px
        if py is not None:
            self._py = py
        if ax is not None:
            self._ax = ax
        if ay is not None:
            self._ay = ay

    def render_interface(self, f):
        import numpy as np

        if not isinstance(f, np.ndarray):
            return f
        h, w = f.shape
        _r_dots(f, h, w, self._level_index, self._num_levels, 0)
        ph = self._ph_disp
        if ph and h > 5:
            gh, gw = len(ph), len(ph[0])
            row = h - 4
            if row >= 0:
                for gx in range(min(gw, min(w - 1, 16))):
                    mx = max(ph[y][gx] for y in range(gh))
                    c = min(15, mx // 4 + (4 if mx > 0 else 0))
                    _rp(f, h, w, 1 + gx, row, c)
            r2 = h - 2
            if r2 >= 0 and self._px >= 0 and self._py >= 0:
                sp = ph[self._py][self._px]
                _rp(f, h, w, 2, r2, min(15, sp // 3 + 5))
            if r2 >= 0 and self._ax >= 0 and self._ay >= 0:
                sa = ph[self._ay][self._ax]
                _rp(f, h, w, 5, r2, min(15, sa // 3 + 5))
        go = self._state == GameState.GAME_OVER
        win = self._state == GameState.WIN
        _r_bar(f, h, w, go, win)
        return f
def spr():
    return {"p": Sprite(pixels=[[9]], name="p", visible=True, collidable=True, tags=["player"]),
            "a": Sprite(pixels=[[6]], name="a", visible=True, collidable=False, tags=["ant"]),
            "h": Sprite(pixels=[[14]], name="h", visible=True, collidable=False, tags=["hole"]),
            "z": Sprite(pixels=[[8]], name="z", visible=True, collidable=True, tags=["hazard"])}
s = spr()
def lvl(d,parts):
    return Level(sprites=parts, grid_size=(16,16), data={"difficulty":d})
levels = [
    lvl(1,[s["p"].clone().set_position(1,1), s["a"].clone().set_position(3,3), s["h"].clone().set_position(14,14)]),
    lvl(2,[s["p"].clone().set_position(2,2), s["a"].clone().set_position(4,4), s["h"].clone().set_position(12,12), s["z"].clone().set_position(8,8)]),
    lvl(3,[s["p"].clone().set_position(0,8), s["a"].clone().set_position(2,8), s["h"].clone().set_position(15,8)]),
    lvl(4,[s["p"].clone().set_position(1,1), s["a"].clone().set_position(5,5), s["h"].clone().set_position(10,10)]),
    lvl(5,[s["p"].clone().set_position(3,3), s["a"].clone().set_position(6,6), s["h"].clone().set_position(13,13), s["z"].clone().set_position(9,9)]),
]
class At01(ARCBaseGame):
    def __init__(self):
        self._ui = U(len(levels))
        super().__init__(
            "at01", levels, Camera(0, 0, 16, 16, BG, PAD, [self._ui]), False, 1, [1, 2, 3, 4, 5]
        )

    def on_set_level(self, level: Level):
        self._p = self.current_level.get_sprites_by_tag("player")[0]
        self._ant = self.current_level.get_sprites_by_tag("ant")[0]
        self._hole = self.current_level.get_sprites_by_tag("hole")[0]
        gw, gh = level.grid_size
        self._ph = [[0] * gw for _ in range(gh)]
        self._ui.update(
            level_index=self.level_index,
            state=self._state,
            ph=self._ph,
            px=self._p.x,
            py=self._p.y,
            ax=self._ant.x,
            ay=self._ant.y,
        )

    def _sync_ph_ui(self) -> None:
        self._ui.update(
            level_index=self.level_index,
            state=self._state,
            ph=self._ph,
            px=self._p.x,
            py=self._p.y,
            ax=self._ant.x,
            ay=self._ant.y,
        )

    def step(self):
        if self.action.id == GameAction.ACTION5:
            self._ph[self._p.y][self._p.x] += 5
            self._sync_ph_ui()
            self.complete_action()
            return
        dx=dy=0
        v=self.action.id.value
        if v==1: dy=-1
        elif v==2: dy=1
        elif v==3: dx=-1
        elif v==4: dx=1
        else:
            self._sync_ph_ui()
            self.complete_action()
            return
        gw, gh = self.current_level.grid_size
        nx, ny = self._p.x+dx, self._p.y+dy
        if 0<=nx<gw and 0<=ny<gh:
            h = self.current_level.get_sprite_at(nx,ny,ignore_collidable=True)
            if not h or not h.is_collidable:
                self._p.set_position(nx,ny)
        for y in range(gh):
            for x in range(gw):
                self._ph[y][x] = max(0, int(self._ph[y][x] * 0.9))
        ax, ay = self._ant.x, self._ant.y
        best, bx, by = -1, ax, ay
        for ddx, ddy in ((0,1),(0,-1),(1,0),(-1,0)):
            tx, ty = ax+ddx, ay+ddy
            if 0<=tx<gw and 0<=ty<gh:
                hit = self.current_level.get_sprite_at(tx,ty,ignore_collidable=True)
                if hit and hit.is_collidable and "hazard" in hit.tags:
                    continue
                sc = self._ph[ty][tx]
                if sc > best:
                    best, bx, by = sc, tx, ty
        self._ant.set_position(bx,by)
        ah = self.current_level.get_sprite_at(bx,by,ignore_collidable=True)
        if ah and "hazard" in ah.tags:
            self.lose()
            self._sync_ph_ui()
            self.complete_action()
            return
        if bx == self._hole.x and by == self._hole.y:
            self.next_level()
        self._sync_ph_ui()
        self.complete_action()
