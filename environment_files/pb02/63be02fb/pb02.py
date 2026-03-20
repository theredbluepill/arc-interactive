from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Pb02UI(RenderableUserDisplay):
    def __init__(self, remaining: int) -> None:
        self._remaining = remaining

    def update(self, remaining: int) -> None:
        self._remaining = remaining

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        color = 14 if self._remaining == 0 else 15
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
}


def mk(
    grid_size,
    player_pos,
    block_positions,
    target_positions,
    wall_coords,
    difficulty,
):
    sl = [sprites["player"].clone().set_position(*player_pos)]
    for bp in block_positions:
        sl.append(sprites["block"].clone().set_position(*bp))
    for tp in target_positions:
        sl.append(sprites["target"].clone().set_position(*tp))
    for wp in wall_coords:
        sl.append(sprites["wall"].clone().set_position(*wp))
    return Level(
        sprites=sl,
        grid_size=grid_size,
        data={"difficulty": difficulty, "step_limit": 80 + difficulty * 20},
    )


levels = [
    mk((8, 8), (1, 1), [(2, 3), (4, 2)], [(5, 5), (6, 4)], [], 1),
    mk((8, 8), (0, 0), [(1, 2), (3, 1)], [(6, 6), (7, 2)], [(2, 2), (4, 4)], 2),
    mk((8, 8), (1, 4), [(2, 2), (5, 3)], [(6, 6), (1, 1)], [(3, y) for y in range(8) if y != 4], 3),
    mk((10, 8), (1, 1), [(2, 3), (4, 4)], [(2, 6), (8, 2)], [(6, y) for y in range(8) if y != 3], 4),
    mk((8, 8), (0, 0), [(1, 1), (2, 2)], [(5, 5), (6, 6)], [(4, y) for y in range(8) if y != 3], 5),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Pb02(ARCBaseGame):
    """Two crates and two goals; push both onto yellow pads."""

    def __init__(self) -> None:
        self._ui = Pb02UI(2)
        super().__init__(
            "pb02",
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
        self._sync_ui()

    def _block_on_target(self, block) -> bool:
        for t in self._targets:
            if block.x == t.x and block.y == t.y:
                return True
        return False

    def _sync_ui(self) -> None:
        rem = sum(1 for b in self._blocks if not self._block_on_target(b))
        for b in self._blocks:
            on = self._block_on_target(b)
            if on and "done" not in b.tags:
                b.color_remap(15, 14)
                b.tags.append("done")
            elif not on and "done" in b.tags:
                b.color_remap(14, 15)
                b.tags.remove("done")
        self._ui.update(rem)

    def step(self) -> None:
        dx = 0
        dy = 0
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
            block_new_x = new_x + dx
            block_new_y = new_y + dy
            if not (0 <= block_new_x < grid_w and 0 <= block_new_y < grid_h):
                self.complete_action()
                return
            block_behind = self.current_level.get_sprite_at(
                block_new_x, block_new_y, ignore_collidable=True
            )
            if block_behind and (
                "block" in block_behind.tags or "wall" in block_behind.tags
            ):
                self.complete_action()
                return
            sprite.set_position(block_new_x, block_new_y)
            self._player.set_position(new_x, new_y)
        elif not sprite or not sprite.is_collidable:
            self._player.set_position(new_x, new_y)

        self._steps += 1
        self._sync_ui()

        if all(self._block_on_target(b) for b in self._blocks):
            self.next_level()
        elif self._steps >= self._step_limit:
            self.lose()

        self.complete_action()
