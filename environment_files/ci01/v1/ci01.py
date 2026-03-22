"""Crate ice sokoban: player moves one cell; pushed crates slide until wall, another crate, or mud.

Spec:
- Tags: ``player``, ``block``, ``target`` (non-collidable), ``wall`` (collidable), ``mud`` (non-collidable stop for sliding only).
- ``level.data``: ``difficulty``, ``step_limit`` (same spirit as sk01/sk02).
- Actions: 1–4 orthogonal move / push.
- Win: every block on a target. Lose: step limit.
- Camera: 16×16; grids 8×8 and 8×12.
"""

from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Ci01UI(RenderableUserDisplay):
    def __init__(self, n_levels: int) -> None:
        self._remaining = 0
        self._n_levels = n_levels
        self._li = 0

    def update(self, remaining: int, level_index: int | None = None) -> None:
        self._remaining = remaining
        if level_index is not None:
            self._li = level_index

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for i in range(min(self._n_levels, 14)):
            cx = 1 + i * 2
            if cx >= w:
                break
            c = 14 if i < self._li else (11 if i == self._li else 3)
            frame[0, cx] = c
        color = 11 if self._remaining == 0 else 14
        for dy in range(4):
            for dx in range(4):
                frame[h - 4 + dy, w - 4 + dx] = color
        return frame


sprites = {
    "player": Sprite(
        pixels=[[9]],
        name="player",
        visible=True,
        collidable=True,
        tags=["player"],
    ),
    "block": Sprite(
        pixels=[[15]],
        name="block",
        visible=True,
        collidable=True,
        tags=["block"],
    ),
    "target": Sprite(
        pixels=[[11]],
        name="target",
        visible=True,
        collidable=False,
        tags=["target"],
    ),
    "wall": Sprite(
        pixels=[[3]],
        name="wall",
        visible=True,
        collidable=True,
        tags=["wall"],
    ),
    "mud": Sprite(
        pixels=[[12]],
        name="mud",
        visible=True,
        collidable=False,
        tags=["mud"],
    ),
}


def make_level(
    grid_size: tuple[int, int],
    player_pos: tuple[int, int],
    block_positions: list[tuple[int, int]],
    target_positions: list[tuple[int, int]],
    wall_coords: list[tuple[int, int]],
    mud_coords: list[tuple[int, int]],
    difficulty: int,
) -> Level:
    sl: list[Sprite] = [sprites["player"].clone().set_position(*player_pos)]
    for bp in block_positions:
        sl.append(sprites["block"].clone().set_position(*bp))
    for tp in target_positions:
        sl.append(sprites["target"].clone().set_position(*tp))
    for wp in wall_coords:
        sl.append(sprites["wall"].clone().set_position(*wp))
    for mx, my in mud_coords:
        sl.append(sprites["mud"].clone().set_position(mx, my))
    return Level(
        sprites=sl,
        grid_size=grid_size,
        data={"difficulty": difficulty, "step_limit": 55 + difficulty * 18},
    )


levels = [
    make_level(
        (8, 8),
        (1, 1),
        [(3, 3)],
        [(6, 6)],
        [],
        [(5, 3), (5, 4), (5, 5)],
        1,
    ),
    make_level(
        (8, 12),
        (1, 1),
        [(2, 5)],
        [(5, 9)],
        [(4, y) for y in range(12) if y not in (4, 5, 6)],
        [(3, 4), (3, 5), (3, 6), (5, 4), (5, 5), (5, 6)],
        2,
    ),
    make_level(
        (8, 12),
        (0, 6),
        [(2, 6), (4, 6)],
        [(6, 10), (7, 10)],
        [(1, y) for y in range(12) if y != 6] + [(3, 5), (3, 7)],
        [(6, 6), (7, 6)],
        3,
    ),
    make_level(
        (8, 8),
        (1, 3),
        [(2, 3)],
        [(6, 3)],
        [(x, 2) for x in range(8) if x != 1] + [(x, 4) for x in range(8) if x != 6],
        [(4, 3)],
        4,
    ),
    make_level(
        (8, 12),
        (1, 2),
        [(2, 2), (3, 2)],
        [(6, 9), (6, 10)],
        [(5, y) for y in range(12) if y not in (2, 3, 4)]
        + [(2, 5), (3, 5), (4, 5)],
        [(4, 2), (4, 3), (4, 4)],
        5,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Ci01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Ci01UI(len(levels))
        super().__init__(
            "ci01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._blocks = self.current_level.get_sprites_by_tag("block")
        self._targets = self.current_level.get_sprites_by_tag("target")
        self._step_limit = level.get_data("step_limit")
        self._steps = 0
        self._ui.update(
            sum(1 for b in self._blocks if "done" not in b.tags),
            self.level_index,
        )

    def _block_on_target(self, block: Sprite) -> bool:
        for t in self._targets:
            if block.x == t.x and block.y == t.y:
                return True
        return False

    def _sync_block_color(self, block: Sprite) -> None:
        if self._block_on_target(block):
            block.color_remap(15, 14)
            if "done" not in block.tags:
                block.tags.append("done")
        else:
            if "done" in block.tags:
                block.color_remap(14, 15)
                block.tags.remove("done")

    def _slide_crate(self, sprite: Sprite, dx: int, dy: int) -> None:
        grid_w, grid_h = self.current_level.grid_size
        cx, cy = sprite.x, sprite.y
        while True:
            nx, ny = cx + dx, cy + dy
            if not (0 <= nx < grid_w and 0 <= ny < grid_h):
                break
            cell = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
            if cell and "mud" in cell.tags:
                break
            if cell and "wall" in cell.tags:
                break
            if cell and "block" in cell.tags and cell is not sprite:
                break
            cx, cy = nx, ny
        sprite.set_position(cx, cy)

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
            self.complete_action()
            return

        new_x = self._player.x + dx
        new_y = self._player.y + dy
        grid_w, grid_h = self.current_level.grid_size
        if not (0 <= new_x < grid_w and 0 <= new_y < grid_h):
            self.complete_action()
            return

        sprite = self.current_level.get_sprite_at(new_x, new_y, ignore_collidable=True)

        if sprite and "wall" in sprite.tags:
            self.complete_action()
            return

        if sprite and "block" in sprite.tags:
            bx, by = new_x + dx, new_y + dy
            if not (0 <= bx < grid_w and 0 <= by < grid_h):
                self.complete_action()
                return
            behind = self.current_level.get_sprite_at(bx, by, ignore_collidable=True)
            if behind and "block" in behind.tags:
                self.complete_action()
                return
            if behind and "wall" in behind.tags:
                self.complete_action()
                return
            sprite.set_position(bx, by)
            self._slide_crate(sprite, dx, dy)
            self._sync_block_color(sprite)
            self._player.set_position(new_x, new_y)
        elif not sprite or not sprite.is_collidable:
            self._player.set_position(new_x, new_y)

        self._steps += 1
        remaining = sum(1 for b in self._blocks if "done" not in b.tags)
        self._ui.update(remaining, self.level_index)

        if remaining == 0:
            self.next_level()
        elif self._steps >= self._step_limit:
            self.lose()

        self.complete_action()
