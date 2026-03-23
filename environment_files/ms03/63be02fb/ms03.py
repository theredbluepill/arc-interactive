"""Chord sapper: revealed safe cells show mine counts in Chebyshev radius 2; ACTION6 flags mines (display click)."""

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
    "mine": Sprite(
        pixels=[[8]],
        name="mine",
        visible=False,
        collidable=False,
        tags=["mine"],
    ),
    "tile": Sprite(
        pixels=[[4]],
        name="tile",
        visible=True,
        collidable=False,
        tags=["tile"],
    ),
    "wall": Sprite(
        pixels=[[3]],
        name="wall",
        visible=True,
        collidable=True,
        tags=["wall"],
    ),
    "flag": Sprite(
        pixels=[[12]],
        name="flag",
        visible=True,
        collidable=False,
        tags=["flag"],
    ),
}


class Ms03UI(RenderableUserDisplay):
    def __init__(self, n: int) -> None:
        self._n = n
        self._bad_flag_frames = 0

    def update(self, n: int) -> None:
        self._n = n

    def flash_bad_flag(self) -> None:
        """Brief HUD signal: flags only work on hidden mines."""
        self._bad_flag_frames = 10

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for i in range(min(self._n, 15)):
            frame[h - 2, 1 + i] = 12
        if self._bad_flag_frames > 0:
            frame[h - 2, w - 2] = 8
            self._bad_flag_frames -= 1
        return frame


def make_level(grid_size, player_pos, goal_pos, mine_coords, wall_coords, difficulty):
    sprite_list = [
        sprites["player"].clone().set_position(*player_pos),
        sprites["goal"].clone().set_position(*goal_pos),
    ]
    for mc in mine_coords:
        sprite_list.append(sprites["mine"].clone().set_position(*mc))
    for wc in wall_coords:
        sprite_list.append(sprites["wall"].clone().set_position(*wc))
    for y in range(grid_size[1]):
        for x in range(grid_size[0]):
            if (x, y) in wall_coords or (x, y) == player_pos or (x, y) == goal_pos:
                continue
            if (x, y) in mine_coords:
                continue
            sprite_list.append(sprites["tile"].clone().set_position(x, y))
    return Level(
        sprites=sprite_list,
        grid_size=grid_size,
        data={"difficulty": difficulty},
    )


levels = [
    make_level((8, 8), (0, 0), (7, 7), [(2, 2), (3, 3), (4, 4)], [], 1),
    make_level((8, 8), (0, 3), (7, 3), [(3, 2), (3, 3), (3, 4), (4, 3)], [], 2),
    make_level((10, 10), (0, 0), (9, 9), [(2, 2), (2, 3), (3, 2), (5, 5), (5, 6)], [], 3),
    make_level((10, 10), (1, 1), (8, 8), [(4, y) for y in range(2, 8)], [], 4),
    make_level((12, 12), (0, 0), (11, 11), [(x, x) for x in range(2, 10)], [], 5),
]


class Ms03(ARCBaseGame):
    CAMERA_W = 16
    CAMERA_H = 16

    def __init__(self) -> None:
        self._ui = Ms03UI(0)
        super().__init__(
            "ms03",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 6],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._minefield: set[tuple[int, int]] = set()
        for m in self.current_level.get_sprites_by_tag("mine"):
            self._minefield.add((m.x, m.y))
        self._revealed: set[tuple[int, int]] = set()
        self._flags: set[tuple[int, int]] = set()
        gw, gh = self.current_level.grid_size
        self._mine_count = {}
        for y in range(gh):
            for x in range(gw):
                if (x, y) not in self._minefield:
                    c = 0
                    for dy in range(-2, 3):
                        for dx in range(-2, 3):
                            if dx == dy == 0:
                                continue
                            if max(abs(dx), abs(dy)) > 2:
                                continue  # Chebyshev ball radius 2
                            if (x + dx, y + dy) in self._minefield:
                                c += 1
                    self._mine_count[(x, y)] = c
        self._ui.update(0)

    def _grid_to_frame_pixel(self, gx: int, gy: int) -> tuple[int, int]:
        cw, ch = self.CAMERA_W, self.CAMERA_H
        scale = min(64 // cw, 64 // ch)
        x_pad = (64 - cw * scale) // 2
        y_pad = (64 - ch * scale) // 2
        return gx * scale + scale // 2 + x_pad, gy * scale + scale // 2 + y_pad

    def _get_clue_color(self, count: int) -> int:
        if count == 0:
            return 1
        if count == 1:
            return 8
        if count == 2:
            return 11
        if count == 3:
            return 14
        return 15

    def step(self) -> None:
        if self.action.id == GameAction.ACTION6:
            px = int(self.action.data.get("x", 0))
            py = int(self.action.data.get("y", 0))
            hit = self.camera.display_to_grid(px, py)
            if hit is None:
                self.complete_action()
                return
            gx, gy = int(hit[0]), int(hit[1])
            if (gx, gy) in self._revealed:
                self.complete_action()
                return
            if (gx, gy) in self._flags:
                for s in list(self.current_level.get_sprites_by_tag("flag")):
                    if s.x == gx and s.y == gy:
                        self.current_level.remove_sprite(s)
                        break
                self._flags.discard((gx, gy))
                self._ui.update(len(self._flags))
                self.complete_action()
                return
            if (gx, gy) not in self._minefield:
                self._ui.flash_bad_flag()
                self.complete_action()
                return
            self.current_level.add_sprite(sprites["flag"].clone().set_position(gx, gy))
            self._flags.add((gx, gy))
            self._ui.update(len(self._flags))
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
        if not (0 <= nx < gw and 0 <= ny < gh):
            self.complete_action()
            return
        sp = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
        if sp and "wall" in sp.tags:
            self.complete_action()
            return
        if (nx, ny) in self._minefield:
            self.lose()
            self.complete_action()
            return
        if (nx, ny) in self._flags:
            self.complete_action()
            return

        self._player.set_position(nx, ny)
        if (nx, ny) not in self._revealed:
            self._revealed.add((nx, ny))
            cnt = self._mine_count.get((nx, ny), 0)
            for s in self.current_level._sprites:
                if s.x == nx and s.y == ny and "tile" in s.tags:
                    s.color_remap(s.pixels[0][0], self._get_clue_color(cnt))
                    break

        if sp and "goal" in sp.tags:
            self.next_level()

        self.complete_action()
