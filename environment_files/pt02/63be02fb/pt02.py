import random

from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)

COLOR_TO_TYPE = {
    11: "arrow",
    14: "lshape",
    15: "tshape",
    12: "cross",
    10: "corner",
}

ARROW_0 = Sprite(
    pixels=[[0, 11, 0], [0, 11, 11], [0, 0, 0]],
    name="arrow_0",
    visible=True,
    collidable=False,
    tags=["rotatable", "type_arrow", "rot_0"],
)

ARROW_90 = Sprite(
    pixels=[[0, 0, 0], [0, 11, 0], [11, 11, 0]],
    name="arrow_90",
    visible=True,
    collidable=False,
    tags=["rotatable", "type_arrow", "rot_90"],
)

ARROW_180 = Sprite(
    pixels=[[0, 0, 0], [11, 11, 0], [0, 11, 0]],
    name="arrow_180",
    visible=True,
    collidable=False,
    tags=["rotatable", "type_arrow", "rot_180"],
)

ARROW_270 = Sprite(
    pixels=[[0, 11, 11], [0, 11, 0], [0, 0, 0]],
    name="arrow_270",
    visible=True,
    collidable=False,
    tags=["rotatable", "type_arrow", "rot_270"],
)

L_0 = Sprite(
    pixels=[[14, 0, 0], [14, 0, 0], [14, 14, 14]],
    name="l_0",
    visible=True,
    collidable=False,
    tags=["rotatable", "type_lshape", "rot_0"],
)

L_90 = Sprite(
    pixels=[[14, 14, 14], [14, 0, 0], [14, 0, 0]],
    name="l_90",
    visible=True,
    collidable=False,
    tags=["rotatable", "type_lshape", "rot_90"],
)

L_180 = Sprite(
    pixels=[[0, 0, 14], [0, 0, 14], [14, 14, 14]],
    name="l_180",
    visible=True,
    collidable=False,
    tags=["rotatable", "type_lshape", "rot_180"],
)

L_270 = Sprite(
    pixels=[[0, 0, 0], [0, 0, 14], [14, 14, 14]],
    name="l_270",
    visible=True,
    collidable=False,
    tags=["rotatable", "type_lshape", "rot_270"],
)

T_0 = Sprite(
    pixels=[[0, 15, 0], [15, 15, 15], [0, 0, 0]],
    name="t_0",
    visible=True,
    collidable=False,
    tags=["rotatable", "type_tshape", "rot_0"],
)

T_90 = Sprite(
    pixels=[[0, 15, 0], [15, 15, 0], [0, 15, 0]],
    name="t_90",
    visible=True,
    collidable=False,
    tags=["rotatable", "type_tshape", "rot_90"],
)

T_180 = Sprite(
    pixels=[[0, 0, 0], [15, 15, 15], [0, 15, 0]],
    name="t_180",
    visible=True,
    collidable=False,
    tags=["rotatable", "type_tshape", "rot_180"],
)

T_270 = Sprite(
    pixels=[[0, 15, 0], [0, 15, 15], [0, 15, 0]],
    name="t_270",
    visible=True,
    collidable=False,
    tags=["rotatable", "type_tshape", "rot_270"],
)

CROSS_0 = Sprite(
    pixels=[[0, 12, 0], [12, 12, 0], [0, 12, 0]],
    name="cross_0",
    visible=True,
    collidable=False,
    tags=["rotatable", "type_cross", "rot_0"],
)

CROSS_90 = Sprite(
    pixels=[[0, 12, 0], [0, 12, 12], [0, 12, 0]],
    name="cross_90",
    visible=True,
    collidable=False,
    tags=["rotatable", "type_cross", "rot_90"],
)

CROSS_180 = Sprite(
    pixels=[[0, 12, 0], [0, 12, 12], [0, 0, 0]],
    name="cross_180",
    visible=True,
    collidable=False,
    tags=["rotatable", "type_cross", "rot_180"],
)

CROSS_270 = Sprite(
    pixels=[[0, 0, 0], [12, 12, 12], [0, 12, 0]],
    name="cross_270",
    visible=True,
    collidable=False,
    tags=["rotatable", "type_cross", "rot_270"],
)

C_0 = Sprite(
    pixels=[[10, 0, 0], [10, 0, 0], [10, 10, 10]],
    name="c_0",
    visible=True,
    collidable=False,
    tags=["rotatable", "type_corner", "rot_0"],
)

C_90 = Sprite(
    pixels=[[0, 0, 10], [0, 0, 10], [10, 10, 10]],
    name="c_90",
    visible=True,
    collidable=False,
    tags=["rotatable", "type_corner", "rot_90"],
)

C_180 = Sprite(
    pixels=[[10, 10, 10], [10, 0, 0], [10, 0, 0]],
    name="c_180",
    visible=True,
    collidable=False,
    tags=["rotatable", "type_corner", "rot_180"],
)

C_270 = Sprite(
    pixels=[[10, 10, 10], [0, 0, 10], [0, 0, 10]],
    name="c_270",
    visible=True,
    collidable=False,
    tags=["rotatable", "type_corner", "rot_270"],
)

ARROW_SPRITES = {0: ARROW_0, 90: ARROW_90, 180: ARROW_180, 270: ARROW_270}
L_SPRITES = {0: L_0, 90: L_90, 180: L_180, 270: L_270}
T_SPRITES = {0: T_0, 90: T_90, 180: T_180, 270: T_270}
CROSS_SPRITES = {0: CROSS_0, 90: CROSS_90, 180: CROSS_180, 270: CROSS_270}
CORNER_SPRITES = {0: C_0, 90: C_90, 180: C_180, 270: C_270}


def get_sprite_type(sprite):
    for tag in sprite.tags:
        if tag.startswith("type_"):
            return tag[5:]
    return "arrow"


def get_sprite_rotation(sprite):
    for tag in sprite.tags:
        if tag.startswith("rot_"):
            return int(tag[4:])
    return 0


def create_rotatable(sprite_type: str, rotation: int, x: int, y: int):
    if sprite_type == "arrow":
        sprite = ARROW_SPRITES[rotation].clone().set_position(x, y)
    elif sprite_type == "lshape":
        sprite = L_SPRITES[rotation].clone().set_position(x, y)
    elif sprite_type == "tshape":
        sprite = T_SPRITES[rotation].clone().set_position(x, y)
    elif sprite_type == "cross":
        sprite = CROSS_SPRITES[rotation].clone().set_position(x, y)
    elif sprite_type == "corner":
        sprite = CORNER_SPRITES[rotation].clone().set_position(x, y)
    else:
        sprite = ARROW_SPRITES[0].clone().set_position(x, y)
    sprite.color_remap(0, 5)
    return sprite


# Playfield stays left of the hint column (separator ~44); tiles are 3×3.
_PLAYFIELD_MAX_X = 43


def _wrong_rotation(target_rot: int, rng: random.Random) -> int:
    """1–3 quarter-turns clockwise from target so the piece never starts solved."""
    return (target_rot + 90 * rng.randint(1, 3)) % 360


def _layout_centered(n_tiles: int, ncols: int, stride: int) -> list[tuple[int, int]]:
    nrows = (n_tiles + ncols - 1) // ncols
    board_w = (ncols - 1) * stride + 3
    board_h = (nrows - 1) * stride + 3
    ox = max(2, (_PLAYFIELD_MAX_X - board_w) // 2)
    oy = max(7, (58 - board_h) // 2)
    out: list[tuple[int, int]] = []
    for i in range(n_tiles):
        col, row = i % ncols, i // ncols
        out.append((ox + col * stride, oy + row * stride))
    return out


def create_level_1():
    target_pattern = {
        "rotations_by_color": {11: 90},
    }
    rng = random.Random(7101)
    positions = _layout_centered(4, 2, stride=14)
    sprites = []
    for x, y in positions:
        start_rot = _wrong_rotation(90, rng)
        sprites.append(create_rotatable("arrow", start_rot, x, y))

    return Level(
        sprites=sprites,
        grid_size=(64, 64),
        data={
            "level_num": 1,
            "target_pattern": target_pattern,
            "rotatable_count": len(positions),
        },
    )


def create_level_2():
    target_pattern = {
        "rotations_by_color": {11: 90, 14: 180},
    }
    rng = random.Random(7102)
    positions = _layout_centered(6, 3, stride=12)
    sprites = []
    for i, (x, y) in enumerate(positions):
        if i < 4:
            sprite_type = "arrow"
            tgt = 90
        else:
            sprite_type = "lshape"
            tgt = 180
        sprites.append(create_rotatable(sprite_type, _wrong_rotation(tgt, rng), x, y))

    return Level(
        sprites=sprites,
        grid_size=(64, 64),
        data={
            "level_num": 2,
            "target_pattern": target_pattern,
            "rotatable_count": len(positions),
        },
    )


def create_level_3():
    target_pattern = {
        "rotations_by_color": {11: 90, 14: 180, 15: 0},
    }
    rng = random.Random(7103)
    positions = _layout_centered(10, 5, stride=8)
    sprites = []
    for i, (x, y) in enumerate(positions):
        if i < 4:
            sprite_type, tgt = "arrow", 90
        elif i < 8:
            sprite_type, tgt = "lshape", 180
        else:
            sprite_type, tgt = "tshape", 0
        sprites.append(create_rotatable(sprite_type, _wrong_rotation(tgt, rng), x, y))

    return Level(
        sprites=sprites,
        grid_size=(64, 64),
        data={
            "level_num": 3,
            "target_pattern": target_pattern,
            "rotatable_count": len(positions),
        },
    )


def create_level_4():
    target_pattern = {
        "rotations_by_color": {11: 90, 14: 180, 15: 0, 12: 270},
    }
    rng = random.Random(7104)
    positions = _layout_centered(16, 4, stride=10)
    sprites = []
    for i, (x, y) in enumerate(positions):
        if i < 4:
            sprite_type, tgt = "arrow", 90
        elif i < 8:
            sprite_type, tgt = "lshape", 180
        elif i < 12:
            sprite_type, tgt = "tshape", 0
        else:
            sprite_type, tgt = "cross", 270
        sprites.append(create_rotatable(sprite_type, _wrong_rotation(tgt, rng), x, y))

    return Level(
        sprites=sprites,
        grid_size=(64, 64),
        data={
            "level_num": 4,
            "target_pattern": target_pattern,
            "rotatable_count": len(positions),
        },
    )


def create_level_5():
    target_pattern = {
        "rotations_by_color": {11: 90, 14: 180, 15: 0, 12: 270, 10: 90},
    }
    rng = random.Random(7105)
    positions = _layout_centered(16, 4, stride=10)
    sprites = []
    for i, (x, y) in enumerate(positions):
        if i < 4:
            sprite_type, tgt = "arrow", 90
        elif i < 8:
            sprite_type, tgt = "lshape", 180
        elif i < 12:
            sprite_type, tgt = "tshape", 0
        elif i < 14:
            sprite_type, tgt = "cross", 270
        else:
            sprite_type, tgt = "corner", 90
        sprites.append(create_rotatable(sprite_type, _wrong_rotation(tgt, rng), x, y))

    return Level(
        sprites=sprites,
        grid_size=(64, 64),
        data={
            "level_num": 5,
            "target_pattern": target_pattern,
            "rotatable_count": len(positions),
        },
    )


levels = [
    create_level_1(),
    create_level_2(),
    create_level_3(),
    create_level_4(),
    create_level_5(),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Pt02UI(RenderableUserDisplay):
    def __init__(
        self,
        level: int,
        checkpoints: int,
        target_checkpoints: int,
        rotatable_count: int,
    ) -> None:
        self._level = level
        self._checkpoints = checkpoints
        self._target_checkpoints = target_checkpoints
        self._rotatable_count = rotatable_count
        self._click_pos = None
        self._click_frames = 0
        self._matched_count = 0
        self._show_success = 0
        self._colors = []
        self._rotations_by_color = {}
        self._rotatables = []

    def update(
        self,
        level: int,
        checkpoints: int,
        target_checkpoints: int,
        rotatable_count: int,
        matched_count: int = 0,
    ) -> None:
        self._level = level
        self._checkpoints = checkpoints
        self._target_checkpoints = target_checkpoints
        self._rotatable_count = rotatable_count
        self._matched_count = matched_count

    def set_target_pattern(self, pattern_type: str, colors: list) -> None:
        self._colors = colors

    def set_target_rotations(self, rotations_by_color: dict) -> None:
        self._rotations_by_color = rotations_by_color

    def set_rotatables(self, rotatables: list) -> None:
        self._rotatables = rotatables

    def set_click(self, x: int, y: int) -> None:
        self._click_pos = (x, y)
        self._click_frames = 8

    def set_success(self) -> None:
        self._show_success = 15

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape

        if self._click_pos and self._click_frames > 0:
            cx, cy = self._click_pos
            if 0 <= cx < w and 0 <= cy < h:
                for r in [3, 5]:
                    for ox, oy in [
                        (0, -r),
                        (0, r),
                        (-r, 0),
                        (r, 0),
                        (-r, -r),
                        (-r, r),
                        (r, -r),
                        (r, r),
                    ]:
                        px, py = cx + ox, cy + oy
                        if 0 <= px < w and 0 <= py < h:
                            frame[py, px] = 12
                frame[cy, cx] = 12
            self._click_frames -= 1
        else:
            self._click_pos = None

        if self._rotations_by_color and self._rotatables:
            scale = 2
            hint_x = 46
            separator_x = 44
            hint_spacing = 10

            current_y = 5
            for color in self._colors:
                target_rot = self._rotations_by_color.get(color, 0)
                sprite_type = COLOR_TO_TYPE.get(color, "arrow")
                temp_sprite = create_rotatable(sprite_type, target_rot, 0, 0)
                rendered = temp_sprite.render()

                for py, row in enumerate(rendered):
                    for px, val in enumerate(row):
                        if val != 0:
                            for dy in range(scale):
                                for dx in range(scale):
                                    fy = current_y + py * scale + dy
                                    fx = hint_x + px * scale + dx
                                    if 0 <= fx < w and 0 <= fy < h:
                                        frame[fy, fx] = val

                current_y += hint_spacing

            for y in range(h):
                frame[y, separator_x] = 2

        if self._rotatable_count > 0:
            progress = self._matched_count
            bar_y = h - 3
            bar_x = 2
            bar_width = min(self._rotatable_count, 20)
            filled = (
                int((progress / self._rotatable_count) * bar_width)
                if self._rotatable_count > 0
                else 0
            )

            for i in range(bar_width):
                color = 11 if i < filled else 4
                frame[bar_y, bar_x + i] = color

        return frame


class Pt02(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Pt02UI(1, 0, 2, 0)
        super().__init__(
            "pt02",
            levels,
            Camera(0, 0, 64, 64, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [6],
        )

    def on_set_level(self, level: Level) -> None:
        self._rotatables = self.current_level.get_sprites_by_tag("rotatable")
        self._level_num = self.current_level.get_data("level_num")
        self._target_pattern = self.current_level.get_data("target_pattern")
        self._rotatable_count = self.current_level.get_data("rotatable_count")
        self._matched_count = 0
        self._action_count = 0
        self._max_actions = self._rotatable_count * 6 + 20

        rotations_by_color = self._target_pattern["rotations_by_color"]
        self._ui.set_target_pattern("mixed", list(rotations_by_color.keys()))
        self._ui.set_target_rotations(rotations_by_color)
        self._ui.set_rotatables(self._rotatables)
        self._update_ui()

    def _get_target_rotation_for_sprite(self, sprite) -> int:
        sprite_type = get_sprite_type(sprite)
        for color, rot in self._target_pattern["rotations_by_color"].items():
            if COLOR_TO_TYPE.get(color) == sprite_type:
                return rot
        return 0

    def _check_match(self) -> bool:
        matched = 0
        for sprite in self._rotatables:
            if get_sprite_rotation(sprite) == self._get_target_rotation_for_sprite(
                sprite
            ):
                matched += 1
        self._matched_count = matched
        return matched == self._rotatable_count

    def _rotate_sprite(self, sprite) -> None:
        current_rot = get_sprite_rotation(sprite)
        new_rot = (current_rot + 90) % 360
        sprite_type = get_sprite_type(sprite)
        x, y = sprite.x, sprite.y
        self.current_level.remove_sprite(sprite)
        new_sprite = create_rotatable(sprite_type, new_rot, x, y)
        self.current_level.add_sprite(new_sprite)
        idx = self._rotatables.index(sprite)
        self._rotatables[idx] = new_sprite
        self._ui.set_rotatables(self._rotatables)

    def _update_ui(self) -> None:
        self._ui.update(
            self._level_num,
            0,
            1,
            self._rotatable_count,
            self._matched_count,
        )

    def step(self) -> None:
        self._action_count += 1

        if self._action_count > self._max_actions:
            self.lose()
            self.complete_action()
            return

        if self.action.id.value == 6:
            x = self.action.data.get("x", 0)
            y = self.action.data.get("y", 0)

            self._ui.set_click(x, y)

            coords = self.camera.display_to_grid(x, y)
            if coords is None:
                self.complete_action()
                return

            grid_x, grid_y = int(coords[0]), int(coords[1])
            if grid_x >= 44:
                self.complete_action()
                return

            row_ys = sorted({s.y for s in self._rotatables})
            col_xs = sorted({s.x for s in self._rotatables})
            if not row_ys or not col_xs:
                self.complete_action()
                return

            def nearest_anchor(val: int, anchors: list[int]) -> int:
                best_a = anchors[0]
                best_d = abs(val - (best_a + 1))
                for a in anchors:
                    d = abs(val - (a + 1))
                    if d < best_d:
                        best_d = d
                        best_a = a
                return best_a

            ry = nearest_anchor(grid_y, row_ys)
            cxn = nearest_anchor(grid_x, col_xs)
            d_row = abs(grid_y - (ry + 1))
            d_col = abs(grid_x - (cxn + 1))
            if d_row <= d_col:
                targets = [s for s in self._rotatables if s.y == ry]
            else:
                targets = [s for s in self._rotatables if s.x == cxn]

            for sp in targets:
                self._rotate_sprite(sp)

            if self._check_match():
                self._ui.set_success()
                self.next_level()

            self._update_ui()

        self.complete_action()
