from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Pb03UI(RenderableUserDisplay):
    def __init__(self, ok: bool) -> None:
        self._ok = ok

    def update(self, ok: bool) -> None:
        self._ok = ok

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        color = 14 if self._ok else 13
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
    "decoy": Sprite(
        pixels=[[12]],
        name="decoy",
        visible=True,
        collidable=False,
        tags=["decoy"],
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
    block_pos,
    target_pos,
    decoy_pos,
    wall_coords,
    difficulty,
):
    sl = [
        sprites["player"].clone().set_position(*player_pos),
        sprites["block"].clone().set_position(*block_pos),
        sprites["target"].clone().set_position(*target_pos),
        sprites["decoy"].clone().set_position(*decoy_pos),
    ]
    for wp in wall_coords:
        sl.append(sprites["wall"].clone().set_position(*wp))
    return Level(
        sprites=sl,
        grid_size=grid_size,
        data={"difficulty": difficulty, "step_limit": 70 + difficulty * 15},
    )


levels = [
    mk((8, 8), (1, 1), (3, 3), (6, 6), (5, 5), [], 1),
    mk((8, 8), (0, 0), (2, 2), (7, 0), (6, 1), [], 2),
    mk((8, 8), (1, 6), (2, 4), (6, 1), (5, 2), [(3, 3), (4, 3)], 3),
    mk((10, 8), (1, 1), (3, 3), (8, 6), (7, 5), [(5, y) for y in range(10) if y != 4], 4),
    mk((8, 8), (0, 7), (1, 1), (6, 0), (5, 1), [(3, y) for y in range(8) if y not in (2, 3)], 5),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Pb03(ARCBaseGame):
    """Push the crate onto the real yellow goal. Orange decoy pad is instant loss."""

    def __init__(self) -> None:
        self._ui = Pb03UI(False)
        super().__init__(
            "pb03",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._block = self.current_level.get_sprites_by_tag("block")[0]
        self._targets = self.current_level.get_sprites_by_tag("target")
        self._decoys = self.current_level.get_sprites_by_tag("decoy")
        self._step_limit = level.get_data("step_limit")
        self._steps = 0
        self._sync_ui()

    def _on_real_goal(self) -> bool:
        for t in self._targets:
            if self._block.x == t.x and self._block.y == t.y:
                return True
        return False

    def _sync_ui(self) -> None:
        on = self._on_real_goal()
        if on and "done" not in self._block.tags:
            self._block.color_remap(15, 14)
            self._block.tags.append("done")
        elif not on and "done" in self._block.tags:
            self._block.color_remap(14, 15)
            self._block.tags.remove("done")
        self._ui.update(on)

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
            if block_behind and "decoy" in block_behind.tags:
                self.lose()
                self.complete_action()
                return
            sprite.set_position(block_new_x, block_new_y)
            self._player.set_position(new_x, new_y)
        elif not sprite or not sprite.is_collidable:
            self._player.set_position(new_x, new_y)

        self._steps += 1
        self._sync_ui()

        if self._on_real_goal():
            self.next_level()
        elif self._steps >= self._step_limit:
            self.lose()

        self.complete_action()
