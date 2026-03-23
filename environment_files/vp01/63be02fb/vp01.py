"""Void path: each floor cell can be entered only once; a second visit loses."""

from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)

CAM_GW = 10
CAM_GH = 10
VISITED_TINT_C = 4


class Vp01UI(RenderableUserDisplay):
    def __init__(self, n: int) -> None:
        self._n = n
        self._visited: set[tuple[int, int]] = set()
        self._grid_w = CAM_GW
        self._grid_h = CAM_GH
        self._skip_tint: tuple[int, int] | None = None

    def update(
        self,
        n: int,
        visited: set[tuple[int, int]] | None = None,
        grid_wh: tuple[int, int] | None = None,
        skip_tint: tuple[int, int] | None = None,
    ) -> None:
        self._n = n
        if visited is not None:
            self._visited = visited
        if grid_wh is not None:
            self._grid_w, self._grid_h = grid_wh
        if skip_tint is not None:
            self._skip_tint = skip_tint

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

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        gw, gh = self._grid_w, self._grid_h
        for cx, cy in self._visited:
            if self._skip_tint is not None and (cx, cy) == self._skip_tint:
                continue
            self._paint_cell(frame, h, w, cx, cy, gw, gh, VISITED_TINT_C)
        for i in range(min(max(0, self._n), 12)):
            frame[h - 2, 1 + i] = 2
        return frame


sprites = {
    "player": Sprite(
        pixels=[[9]],
        name="player",
        visible=True,
        collidable=True,
        tags=["player"],
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


def mk(sl: list, d: int) -> Level:
    return Level(sprites=sl, grid_size=(10, 10), data={"difficulty": d})


levels = [
    mk(
        [
            sprites["player"].clone().set_position(0, 5),
            sprites["goal"].clone().set_position(9, 5),
        ],
        1,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["goal"].clone().set_position(8, 8),
        ],
        2,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["goal"].clone().set_position(9, 9),
            sprites["wall"].clone().set_position(5, 5),
        ],
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(2, 5),
            sprites["goal"].clone().set_position(7, 5),
        ]
        + [sprites["wall"].clone().set_position(4, y) for y in range(3, 8)],
        4,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 9),
            sprites["goal"].clone().set_position(9, 0),
        ],
        5,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Vp01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Vp01UI(0)
        super().__init__(
            "vp01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._goal = self.current_level.get_sprites_by_tag("goal")[0]
        gw, gh = self.current_level.grid_size
        self._visited: set[tuple[int, int]] = {(self._player.x, self._player.y)}
        self._vp_sync_ui()

    def _vp_sync_ui(self) -> None:
        gw, gh = self.current_level.grid_size
        self._ui.update(
            max(0, gw * gh - len(self._visited)),
            visited=set(self._visited),
            grid_wh=(gw, gh),
            skip_tint=(self._player.x, self._player.y),
        )

    def step(self) -> None:
        dx = dy = 0
        if self.action.id.value == 1:
            dy = -1
        elif self.action.id.value == 2:
            dy = 1
        elif self.action.id.value == 3:
            dx = -1
        elif self.action.id.value == 4:
            dx = 1

        if dx == 0 and dy == 0:
            self._vp_sync_ui()
            self.complete_action()
            return

        nx = self._player.x + dx
        ny = self._player.y + dy
        gw, gh = self.current_level.grid_size
        if not (0 <= nx < gw and 0 <= ny < gh):
            self._vp_sync_ui()
            self.complete_action()
            return

        sp = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
        if sp and "wall" in sp.tags:
            self._vp_sync_ui()
            self.complete_action()
            return

        if (nx, ny) in self._visited:
            self.lose()
            self._vp_sync_ui()
            self.complete_action()
            return

        self._player.set_position(nx, ny)
        self._visited.add((nx, ny))
        self._vp_sync_ui()

        if self._player.x == self._goal.x and self._player.y == self._goal.y:
            self.next_level()

        self.complete_action()
