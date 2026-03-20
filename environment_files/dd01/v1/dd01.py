"""Drone relay: pick up orange crates with ACTION5, deliver to yellow pads. Move on a 48×48 grid; when not picking up/dropping, ACTION5 pings the nearest pad (HUD flash)."""

from __future__ import annotations

from arcengine import (
    ARCBaseGame,
    Camera,
    GameAction,
    Level,
    RenderableUserDisplay,
    Sprite,
)

BACKGROUND_COLOR = 5
PADDING_COLOR = 4
CAM_W = CAM_H = 48

WALL_C = 3
PLAYER_C = 9
CRATE_C = 12
PAD_C = 11


class Dd01UI(RenderableUserDisplay):
    def __init__(self, holding: bool, remain: int, ping: tuple[int, int] | None, ping_frames: int) -> None:
        self._holding = holding
        self._remain = remain
        self._ping = ping
        self._ping_frames = ping_frames

    def update(
        self,
        holding: bool,
        remain: int,
        ping: tuple[int, int] | None,
        ping_frames: int,
    ) -> None:
        self._holding = holding
        self._remain = remain
        self._ping = ping
        self._ping_frames = ping_frames

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        frame[h - 2, 2] = 12 if self._holding else 2
        for i in range(min(self._remain, 15)):
            frame[h - 2, 4 + i] = 11
        if self._ping and self._ping_frames > 0:
            px, py = self._ping
            for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                x, y = px + dx, py + dy
                if 0 <= x < w and 0 <= y < h:
                    frame[y, x] = 7
        return frame


sprites = {
    "wall": Sprite(
        pixels=[[WALL_C]],
        name="wall",
        visible=True,
        collidable=True,
        tags=["wall"],
    ),
    "player": Sprite(
        pixels=[[PLAYER_C]],
        name="player",
        visible=True,
        collidable=True,
        tags=["player"],
    ),
    "crate": Sprite(
        pixels=[[CRATE_C]],
        name="crate",
        visible=True,
        collidable=False,
        tags=["crate"],
    ),
    "pad": Sprite(
        pixels=[[PAD_C]],
        name="pad",
        visible=True,
        collidable=False,
        tags=["pad"],
    ),
}


def mk(
    walls: list[tuple[int, int]],
    player: tuple[int, int],
    crates: list[tuple[int, int]],
    pads: list[tuple[int, int]],
    max_steps: int,
    diff: int,
) -> Level:
    sl: list[Sprite] = []
    for wx, wy in walls:
        sl.append(sprites["wall"].clone().set_position(wx, wy))
    sl.append(sprites["player"].clone().set_position(player[0], player[1]))
    for cx, cy in crates:
        sl.append(sprites["crate"].clone().set_position(cx, cy))
    for px, py in pads:
        sl.append(sprites["pad"].clone().set_position(px, py))
    return Level(
        sprites=sl,
        grid_size=(CAM_W, CAM_H),
        data={"difficulty": diff, "max_steps": max_steps},
    )


def _row_wall(y, x0, x1):
    return [(x, y) for x in range(x0, x1)]


levels = [
    mk([], (4, 24), [(10, 24), (14, 24)], [(40, 24), (36, 24)], 500, 1),
    mk(
        _row_wall(30, 5, 43) + _row_wall(18, 5, 25),
        (6, 6),
        [(12, 12), (20, 8)],
        [(42, 42), (38, 10)],
        600,
        2,
    ),
    mk(
        [(24, y) for y in range(48) if y % 6 not in (0, 1)],
        (4, 24),
        [(30, 10), (34, 38), (10, 40)],
        [(44, 24), (40, 8), (8, 8)],
        700,
        3,
    ),
    mk(
        [(x, x) for x in range(48) if 10 < x < 38 and x % 4 != 0],
        (5, 40),
        [(20, 20), (28, 28), (12, 30)],
        [(45, 5), (40, 45), (25, 5)],
        800,
        4,
    ),
    mk(
        [(15, y) for y in range(48) if y % 4 != 2]
        + [(32, y) for y in range(48) if y % 4 != 0],
        (2, 24),
        [(24, 8), (24, 40), (8, 24), (40, 24)],
        [(46, 24), (2, 46), (46, 8), (8, 2)],
        900,
        5,
    ),
]


class Dd01(ARCBaseGame):
    PING_FRAMES = 24

    def _grid_to_frame_pixel(self, gx: int, gy: int) -> tuple[int, int]:
        cam = self.camera
        cw, ch = cam.width, cam.height
        scale = min(64 // cw, 64 // ch)
        x_pad = (64 - cw * scale) // 2
        y_pad = (64 - ch * scale) // 2
        return gx * scale + scale // 2 + x_pad, gy * scale + scale // 2 + y_pad

    def __init__(self) -> None:
        self._ui = Dd01UI(False, 0, None, 0)
        super().__init__(
            "dd01",
            levels,
            Camera(0, 0, CAM_W, CAM_H, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 5],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._holding = False
        self._steps = int(self.current_level.get_data("max_steps") or 500)
        self._ping_pos: tuple[int, int] | None = None
        self._ping_frames = 0
        self._sync_ui()

    def _pads(self) -> list[Sprite]:
        return self.current_level.get_sprites_by_tag("pad")

    def _crates(self) -> list[Sprite]:
        return self.current_level.get_sprites_by_tag("crate")

    def _sync_ui(self) -> None:
        self._ui.update(
            self._holding,
            len(self._crates()),
            self._ping_pos,
            self._ping_frames,
        )

    def _burn(self) -> bool:
        self._steps -= 1
        self._sync_ui()
        if self._steps <= 0:
            self.lose()
            return True
        return False

    def _nearest_pad(self) -> Sprite | None:
        px, py = self._player.x, self._player.y
        best: Sprite | None = None
        best_d = 10**9
        for p in self._pads():
            d = abs(p.x - px) + abs(p.y - py)
            if d < best_d:
                best_d = d
                best = p
        return best

    def step(self) -> None:
        if self._ping_frames > 0:
            self._ping_frames -= 1
            if self._ping_frames == 0:
                self._ping_pos = None
            self._sync_ui()

        aid = self.action.id

        if aid in (GameAction.ACTION1, GameAction.ACTION2, GameAction.ACTION3, GameAction.ACTION4):
            dx = dy = 0
            if aid == GameAction.ACTION1:
                dy = -1
            elif aid == GameAction.ACTION2:
                dy = 1
            elif aid == GameAction.ACTION3:
                dx = -1
            elif aid == GameAction.ACTION4:
                dx = 1
            nx, ny = self._player.x + dx, self._player.y + dy
            gw, gh = self.current_level.grid_size
            if 0 <= nx < gw and 0 <= ny < gh:
                sp = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
                if sp and "wall" in sp.tags:
                    pass
                elif not sp or not sp.is_collidable:
                    self._player.set_position(nx, ny)
                elif "crate" in sp.tags or "pad" in sp.tags:
                    self._player.set_position(nx, ny)
            self._sync_ui()
            if self._burn():
                self.complete_action()
                return
            self.complete_action()
            return

        if aid == GameAction.ACTION5:
            px, py = self._player.x, self._player.y
            here = self.current_level.get_sprite_at(px, py, ignore_collidable=True)
            if not self._holding and here and "crate" in here.tags:
                self.current_level.remove_sprite(here)
                self._holding = True
            elif self._holding and here and "pad" in here.tags:
                self._holding = False
            else:
                p = self._nearest_pad()
                if p:
                    self._ping_pos = self._grid_to_frame_pixel(p.x, p.y)
                    self._ping_frames = self.PING_FRAMES
            if len(self._crates()) == 0 and not self._holding:
                self.next_level()
            self._sync_ui()
            if self._burn():
                self.complete_action()
                return
            self.complete_action()
            return

        self.complete_action()
