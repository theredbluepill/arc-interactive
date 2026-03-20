"""Phase multiply: ACTION5 sets each non-wall cell to (self × Π max(1, orth neighbor phase)) mod 4."""

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
CAM_W = CAM_H = 24
WALL_C = 3
MARK_C = 2


class Ph03UI(RenderableUserDisplay):
    def __init__(self, rounds: int) -> None:
        self._rounds = rounds

    def update(self, rounds: int) -> None:
        self._rounds = rounds

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for i in range(min(self._rounds, 25)):
            frame[h - 2, 1 + i] = 10
        return frame


sprites = {
    "wall": Sprite(
        pixels=[[WALL_C]],
        name="wall",
        visible=True,
        collidable=True,
        tags=["wall"],
    ),
    "mark": Sprite(
        pixels=[[MARK_C]],
        name="mark",
        visible=True,
        collidable=False,
        tags=["mark"],
    ),
}


def _palette_sprite(phase: int) -> Sprite:
    colors = [0, 6, 9, 11]
    c = colors[phase % 4]
    return Sprite(
        pixels=[[c]],
        name=f"ph_{phase}",
        visible=True,
        collidable=False,
        tags=["phase_cell"],
    )


def mk(
    walls: list[tuple[int, int]],
    marks: list[tuple[int, int]],
    target: list[list[int]],
    max_blur: int,
    diff: int,
) -> Level:
    sl: list[Sprite] = []
    for wx, wy in walls:
        sl.append(sprites["wall"].clone().set_position(wx, wy))
    for mx, my in marks:
        sl.append(sprites["mark"].clone().set_position(mx, my))
    return Level(
        sprites=sl,
        grid_size=(CAM_W, CAM_H),
        data={
            "difficulty": diff,
            "target": target,
            "max_blur": max_blur,
        },
    )


levels = [
    mk([], [(10, 12), (11, 12)], [[10, 12, 0], [11, 12, 2]], 30, 1),
    mk([(12, y) for y in range(24) if y != 12], [(8, 12), (16, 12)], [[8, 12, 1], [16, 12, 3]], 40, 2),
    mk([], [(6, 6), (18, 18), (18, 6)], [[6, 6, 2], [18, 18, 2], [18, 6, 0]], 50, 3),
    mk([(x, 10) for x in range(6, 18)], [(9, 12), (15, 12)], [[9, 12, 0], [15, 12, 0]], 45, 4),
    mk([], [(5 + i, 12) for i in range(6)], [[5 + i, 12, (i % 4)] for i in range(6)], 60, 5),
]


class Ph03(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Ph03UI(0)
        super().__init__(
            "ph03",
            levels,
            Camera(0, 0, CAM_W, CAM_H, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 5, 6],
        )

    def on_set_level(self, level: Level) -> None:
        gw, gh = self.current_level.grid_size
        self._g = [[0 for _ in range(gh)] for _ in range(gw)]
        raw = self.current_level.get_data("target") or []
        self._target: dict[tuple[int, int], int] = {}
        for row in raw:
            x, y, v = int(row[0]), int(row[1]), int(row[2])
            self._target[(x, y)] = v
        self._blur_left = int(self.current_level.get_data("max_blur") or 40)
        self._sync_ui()
        self._refresh_phase_sprites()

    def _wall_at(self, x: int, y: int) -> bool:
        sp = self.current_level.get_sprite_at(x, y, ignore_collidable=True)
        return sp is not None and "wall" in sp.tags

    def _mark_at(self, x: int, y: int) -> bool:
        sp = self.current_level.get_sprite_at(x, y, ignore_collidable=True)
        return sp is not None and "mark" in sp.tags

    def _clear_phase_sprites(self) -> None:
        for s in list(self.current_level.get_sprites_by_tag("phase_cell")):
            self.current_level.remove_sprite(s)

    def _refresh_phase_sprites(self) -> None:
        self._clear_phase_sprites()
        gw, gh = self.current_level.grid_size
        for y in range(gh):
            for x in range(gw):
                if self._wall_at(x, y) or self._mark_at(x, y):
                    continue
                self.current_level.add_sprite(
                    _palette_sprite(self._g[x][y]).clone().set_position(x, y),
                )

    def _sync_ui(self) -> None:
        self._ui.update(self._blur_left)

    def _win(self) -> bool:
        for (x, y), v in self._target.items():
            if self._g[x][y] != v:
                return False
        return True

    def step(self) -> None:
        aid = self.action.id

        if aid in (
            GameAction.ACTION1,
            GameAction.ACTION2,
            GameAction.ACTION3,
            GameAction.ACTION4,
        ):
            self.complete_action()
            return

        if aid == GameAction.ACTION5:
            if self._blur_left <= 0:
                self.lose()
                self.complete_action()
                return
            self._blur_left -= 1
            gw, gh = self.current_level.grid_size
            new_g = [[0 for _ in range(gh)] for _ in range(gw)]
            for y in range(gh):
                for x in range(gw):
                    if self._wall_at(x, y):
                        new_g[x][y] = self._g[x][y]
                        continue
                    p = 1
                    for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < gw and 0 <= ny < gh:
                            p = (p * max(1, self._g[nx][ny])) % 4
                            if p == 0:
                                p = 1
                    new_g[x][y] = (self._g[x][y] * p) % 4
            self._g = new_g
            self._refresh_phase_sprites()
            self._sync_ui()
            if self._win():
                self.next_level()
            self.complete_action()
            return

        if aid != GameAction.ACTION6:
            self.complete_action()
            return

        px = self.action.data.get("x", 0)
        py = self.action.data.get("y", 0)
        coords = self.camera.display_to_grid(px, py)
        if coords is None:
            self.complete_action()
            return
        gx, gy = coords
        gw, gh = self.current_level.grid_size
        if not (0 <= gx < gw and 0 <= gy < gh):
            self.complete_action()
            return
        if self._wall_at(gx, gy):
            self.complete_action()
            return

        self._g[gx][gy] = (self._g[gx][gy] + 1) % 4
        self._refresh_phase_sprites()
        if self._win():
            self.next_level()
        self.complete_action()
