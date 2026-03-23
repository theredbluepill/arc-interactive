"""Sentry sweep: guard looks along a 90° cone; get spotted and you lose. ACTION5 whistles to make the guard step forward one cell."""

from arcengine import (
    ARCBaseGame,
    Camera,
    GameAction,
    Level,
    RenderableUserDisplay,
    Sprite,
)


CONE_OVERLAY_C = 4
GRID_W = 16
GRID_H = 16


class St01UI(RenderableUserDisplay):
    def __init__(self, face: int) -> None:
        self._face = face
        self._cone: set[tuple[int, int]] = set()

    def update(
        self,
        face: int,
        cone: set[tuple[int, int]],
    ) -> None:
        self._face = face % 4
        self._cone = cone

    @staticmethod
    def _paint_cell(
        frame, fh: int, fw: int, gx: int, gy: int, gw: int, gh: int, color: int
    ) -> None:
        scale_x = 64 // gw
        scale_y = 64 // gh
        scale = min(scale_x, scale_y)
        x_pad = (fw - (gw * scale)) // 2
        y_pad = (fh - (gh * scale)) // 2
        x0 = x_pad + gx * scale
        y0 = y_pad + gy * scale
        for sy in range(scale):
            for sx in range(scale):
                fx, fy = x0 + sx, y0 + sy
                if 0 <= fx < fw and 0 <= fy < fh:
                    frame[fy, fx] = color

    @staticmethod
    def _draw_facing_glyph(frame, fh: int, fw: int, face: int) -> None:
        cx, cy = 6, fh - 3
        c = 9
        if face == 0:
            if cy - 2 >= 0:
                frame[cy - 2, cx] = c
            if cy - 1 >= 0:
                frame[cy - 1, cx - 1] = c
                frame[cy - 1, cx + 1] = c
            frame[cy, cx] = c
        elif face == 1:
            if cx + 2 < fw:
                frame[cy, cx + 2] = c
            if cx + 1 < fw:
                frame[cy - 1, cx + 1] = c
                frame[cy + 1, cx + 1] = c
            frame[cy, cx] = c
        elif face == 2:
            frame[cy, cx] = c
            if cy + 1 < fh:
                frame[cy + 1, cx - 1] = c
                frame[cy + 1, cx + 1] = c
            if cy + 2 < fh:
                frame[cy + 2, cx] = c
        else:
            if cx - 2 >= 0:
                frame[cy, cx - 2] = c
            if cx - 1 >= 0:
                frame[cy - 1, cx - 1] = c
                frame[cy + 1, cx - 1] = c
            frame[cy, cx] = c

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for cell in self._cone:
            self._paint_cell(
                frame, h, w, cell[0], cell[1], GRID_W, GRID_H, CONE_OVERLAY_C
            )
        frame[h - 2, 2] = 8
        self._draw_facing_glyph(frame, h, w, self._face)
        return frame


sprites = {
    "player": Sprite(
        pixels=[[9]],
        name="player",
        visible=True,
        collidable=True,
        tags=["player"],
    ),
    "guard": Sprite(
        pixels=[[8]],
        name="guard",
        visible=True,
        collidable=False,
        tags=["guard"],
    ),
    "goal": Sprite(
        pixels=[[14]],
        name="goal",
        visible=True,
        collidable=False,
        tags=["goal"],
    ),
    "wall": Sprite(
        pixels=[[3]],
        name="wall",
        visible=True,
        collidable=True,
        tags=["wall"],
    ),
}

DX = (0, 1, 0, -1)
DY = (-1, 0, 1, 0)


def mk(sl, facing: int, d: int):
    return Level(
        sprites=sl,
        grid_size=(16, 16),
        data={"difficulty": d, "guard_facing": facing},
    )


levels = [
    mk(
        [
            sprites["player"].clone().set_position(1, 8),
            sprites["guard"].clone().set_position(10, 8),
            sprites["goal"].clone().set_position(14, 14),
        ],
        3,
        1,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["guard"].clone().set_position(8, 4),
            sprites["goal"].clone().set_position(15, 15),
        ],
        2,
        2,
    ),
    mk(
        [
            sprites["player"].clone().set_position(2, 14),
            sprites["guard"].clone().set_position(8, 8),
            sprites["goal"].clone().set_position(14, 0),
        ]
        + [sprites["wall"].clone().set_position(8, y) for y in range(16) if abs(y - 8) > 2],
        0,
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(4, 4),
            sprites["guard"].clone().set_position(12, 12),
            sprites["goal"].clone().set_position(0, 15),
        ],
        3,
        4,
    ),
    mk(
        [
            sprites["player"].clone().set_position(15, 15),
            sprites["guard"].clone().set_position(7, 7),
            sprites["goal"].clone().set_position(0, 0),
        ],
        1,
        5,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class St01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = St01UI(0)
        super().__init__(
            "st01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 5],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._guard = self.current_level.get_sprites_by_tag("guard")[0]
        self._face = int(self.current_level.get_data("guard_facing") or 0) % 4
        self._sync_cone_ui()

    def _cone_cells(self) -> set[tuple[int, int]]:
        gx, gy = self._guard.x, self._guard.y
        fdx, fdy = DX[self._face], DY[self._face]
        rdx, rdy = -fdy, fdx
        out: set[tuple[int, int]] = set()
        gw, gh = self.current_level.grid_size
        for dist in range(1, 8):
            cx = gx + fdx * dist
            cy = gy + fdy * dist
            if not (0 <= cx < gw and 0 <= cy < gh):
                break
            for w in (-1, 0, 1):
                tx = cx + rdx * w
                ty = cy + rdy * w
                if 0 <= tx < gw and 0 <= ty < gh:
                    out.add((tx, ty))
                sp = self.current_level.get_sprite_at(tx, ty, ignore_collidable=True)
                if sp and "wall" in sp.tags:
                    break
        return out

    def _sync_cone_ui(self) -> None:
        self._ui.update(self._face, self._cone_cells())

    def _seen(self) -> bool:
        gx, gy = self._guard.x, self._guard.y
        px, py = self._player.x, self._player.y
        fdx, fdy = DX[self._face], DY[self._face]
        rdx, rdy = -fdy, fdx
        for dist in range(1, 8):
            cx = gx + fdx * dist
            cy = gy + fdy * dist
            if not (
                0 <= cx < self.current_level.grid_size[0]
                and 0 <= cy < self.current_level.grid_size[1]
            ):
                break
            for w in (-1, 0, 1):
                tx = cx + rdx * w
                ty = cy + rdy * w
                if tx == px and ty == py:
                    return True
                sp = self.current_level.get_sprite_at(tx, ty, ignore_collidable=True)
                if sp and "wall" in sp.tags:
                    break
        return False

    def step(self) -> None:
        if self.action.id == GameAction.ACTION5:
            fdx, fdy = DX[self._face], DY[self._face]
            nx, ny = self._guard.x + fdx, self._guard.y + fdy
            gw, gh = self.current_level.grid_size
            if 0 <= nx < gw and 0 <= ny < gh:
                sp = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
                if not sp or "wall" not in sp.tags:
                    self._guard.set_position(nx, ny)
            self._sync_cone_ui()
            self.complete_action()
            return

        dx = dy = 0
        if self.action.id.value == 1:
            dy = -1
        elif self.action.id.value == 2:
            dy = 1
        elif self.action.id.value == 3:
            dx = -1
        elif self.action.id.value == 4:
            dx = 1
        else:
            self.complete_action()
            return

        nx, ny = self._player.x + dx, self._player.y + dy
        gw, gh = self.current_level.grid_size
        if 0 <= nx < gw and 0 <= ny < gh:
            sp = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
            if not sp or not sp.is_collidable:
                self._player.set_position(nx, ny)

        if self._seen():
            self.lose()
            self._sync_cone_ui()
            self.complete_action()
            return

        gl = self.current_level.get_sprites_by_tag("goal")
        if gl and self._player.x == gl[0].x and self._player.y == gl[0].y:
            self.next_level()
        self._sync_cone_ui()

        self.complete_action()
