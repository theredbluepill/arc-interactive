"""Slide sokoban with mud: extra slide stops on brown mud cells (walkable)."""

from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Sk03UI(RenderableUserDisplay):
    def __init__(self, remaining: int, step_limit: int) -> None:
        self._remaining = remaining
        self._steps_left = step_limit
        self._step_limit = max(1, step_limit)

    def update(self, remaining: int, steps_left: int, step_limit: int) -> None:
        self._remaining = remaining
        self._steps_left = max(0, steps_left)
        self._step_limit = max(1, step_limit)

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        color = 11 if self._remaining == 0 else 14
        for dy in range(4):
            for dx in range(4):
                frame[h - 4 + dy, w - 4 + dx] = color
        lim = self._step_limit
        bar_w = min(14, max(4, min(lim, 14)))
        for i in range(bar_w):
            thr = lim * (1.0 - (i + 0.5) / bar_w)
            low = self._steps_left <= max(3, lim // 6)
            c = 14 if self._steps_left >= thr else (8 if low else 3)
            frame[h - 1, 1 + i] = c
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
        pixels=[[13]],
        name="mud",
        visible=True,
        collidable=False,
        tags=["mud"],
    ),
}


def make_level(
    grid_size,
    player_pos,
    block_positions,
    target_positions,
    wall_coords,
    mud_coords,
    difficulty,
):
    sprite_list = [sprites["player"].clone().set_position(*player_pos)]
    for bp in block_positions:
        sprite_list.append(sprites["block"].clone().set_position(*bp))
    for tp in target_positions:
        sprite_list.append(sprites["target"].clone().set_position(*tp))
    for wp in wall_coords:
        sprite_list.append(sprites["wall"].clone().set_position(*wp))
    for mx, my in mud_coords:
        sprite_list.append(sprites["mud"].clone().set_position(mx, my))
    return Level(
        sprites=sprite_list,
        grid_size=grid_size,
        data={"difficulty": difficulty, "step_limit": 55 + difficulty * 22},
    )


levels = [
    make_level((8, 8), (1, 1), [(3, 3)], [(5, 5)], [], [(4, 3)], 1),
    make_level((8, 8), (1, 1), [(3, 3)], [(5, 5)], [(2, 2), (4, 2), (4, 4), (2, 4)], [(4, 3)], 2),
    make_level(
        (8, 8),
        (1, 1),
        [(2, 4), (5, 2)],
        [(6, 6), (6, 4)],
        [(4, 3), (4, 4), (4, 5), (3, 5), (5, 5)],
        [(5, 4)],
        3,
    ),
    make_level(
        (12, 12),
        (1, 1),
        [(3, 4), (4, 3)],
        [(9, 9), (10, 8)],
        [(6, y) for y in range(12) if y != 5],
        [(7, 5), (8, 5)],
        4,
    ),
    make_level(
        (8, 8),
        (0, 0),
        [(1, 1), (2, 2), (3, 1)],
        [(5, 5), (6, 6), (5, 6)],
        [(4, y) for y in range(8) if y != 3],
        [(3, 3), (5, 3)],
        5,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Sk03(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Sk03UI(0, 99)
        super().__init__(
            "sk03",
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
        sl = int(self._step_limit) if self._step_limit is not None else 99
        self._ui.update(len(self._blocks), sl, sl)

    def _block_on_target(self, block, targets):
        for t in targets:
            if block.x == t.x and block.y == t.y:
                return True
        return False

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
            block_new_x = new_x + dx
            block_new_y = new_y + dy
            if not (0 <= block_new_x < grid_w and 0 <= block_new_y < grid_h):
                self.complete_action()
                return
            block_behind = self.current_level.get_sprite_at(
                block_new_x, block_new_y, ignore_collidable=True
            )
            if block_behind and "block" in block_behind.tags:
                self.complete_action()
                return
            if block_behind and "wall" in block_behind.tags:
                self.complete_action()
                return
            sprite.set_position(block_new_x, block_new_y)
            slide_x = block_new_x + dx
            slide_y = block_new_y + dy
            if 0 <= slide_x < grid_w and 0 <= slide_y < grid_h:
                slide_cell = self.current_level.get_sprite_at(
                    slide_x, slide_y, ignore_collidable=True
                )
                mud_stop = slide_cell and "mud" in slide_cell.tags
                blocked = (
                    slide_cell
                    and (
                        "wall" in slide_cell.tags
                        or (
                            "block" in slide_cell.tags
                            and slide_cell is not sprite
                        )
                    )
                )
                if not blocked and not mud_stop:
                    sprite.set_position(slide_x, slide_y)
            if self._block_on_target(sprite, self._targets):
                sprite.color_remap(15, 14)
                if "done" not in sprite.tags:
                    sprite.tags.append("done")
            else:
                if "done" in sprite.tags:
                    sprite.color_remap(14, 15)
                    sprite.tags.remove("done")
            self._player.set_position(new_x, new_y)
        elif not sprite or not sprite.is_collidable:
            self._player.set_position(new_x, new_y)

        self._steps += 1
        remaining = sum(1 for b in self._blocks if "done" not in b.tags)
        lim = int(self._step_limit) if self._step_limit is not None else 999
        steps_left = max(0, lim - self._steps)
        self._ui.update(remaining, steps_left, lim)

        if remaining == 0:
            self.next_level()
        elif self._steps >= self._step_limit:
            self.lose()

        self.complete_action()
