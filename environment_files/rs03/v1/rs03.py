"""Rule switcher with a forbidden HUD stripe color: that color never becomes collectible, even after all pairs have cycled."""

from arcengine import (
    ARCBaseGame,
    Camera,
    GameAction,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Rs03UI(RenderableUserDisplay):
    """HUD: dual safe colors + forbidden stripe + pair index + targets."""

    HUD_ROWS = 5

    def __init__(self) -> None:
        self._safe_a = 8
        self._safe_b = 14
        self._forbidden = 12
        self._pair_index = 0
        self._num_pairs = 1
        self._all_cycled = False
        self._targets_left = 0
        self._difficulty = 1
        self._win_holding = False

    def update(
        self,
        safe_a: int,
        _legacy_colors: tuple[int, ...],
        pair_index: int,
        all_cycled: bool,
        targets_left: int,
        difficulty: int,
        win_holding: bool = False,
        *,
        safe_b: int = 14,
        num_pairs: int = 1,
        forbidden: int = 12,
    ) -> None:
        self._safe_a = safe_a
        self._safe_b = safe_b
        self._forbidden = forbidden
        self._pair_index = pair_index
        self._num_pairs = max(1, num_pairs)
        self._all_cycled = all_cycled
        self._targets_left = targets_left
        self._difficulty = difficulty
        self._win_holding = win_holding

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        hr = min(Rs03UI.HUD_ROWS, h)

        for y in range(hr):
            for x in range(w):
                frame[y, x] = 5

        lvl_colors = [9, 10, 11, 12, 14]
        lc = lvl_colors[(self._difficulty - 1) % len(lvl_colors)]
        for dy in range(2):
            for dx in range(2):
                px, py = 1 + dx, 1 + dy
                if px < w and py < hr:
                    frame[py, px] = lc

        for dx in range(3):
            if 6 + dx < w and 1 < hr:
                frame[1, 6 + dx] = self._safe_a
            if 10 + dx < w and 1 < hr:
                frame[1, 10 + dx] = self._safe_b

        for dx in range(3):
            if 14 + dx < w and 1 < hr:
                frame[1, 14 + dx] = self._forbidden

        for i in range(min(self._num_pairs, 6)):
            px = 16 + i * 2
            if px < w and 3 < hr:
                frame[3, px] = 0 if i == self._pair_index else 3

        if self._all_cycled and 0 < hr:
            frame[0, w - 4] = 14
            frame[0, w - 3] = 14

        cap = min(14, self._targets_left)
        for i in range(cap):
            px = w - 2 - i
            if px > 0 and 2 < hr:
                frame[2, px] = 11

        if self._win_holding and 4 < hr:
            pulse = 14 if (self._difficulty + self._targets_left) % 2 == 0 else 11
            for px in range(4, min(w - 4, 40)):
                frame[4, px] = pulse

        return frame


sprites = {
    "player": Sprite(
        pixels=[[9]],
        name="player",
        visible=True,
        collidable=True,
        tags=["player"],
    ),
    "wall": Sprite(
        pixels=[[3]],
        name="wall",
        visible=True,
        collidable=True,
        tags=["wall"],
    ),
    8: Sprite(
        pixels=[[8]],
        name="target_red",
        visible=True,
        collidable=False,
        tags=["target"],
    ),
    11: Sprite(
        pixels=[[11]],
        name="target_yellow",
        visible=True,
        collidable=False,
        tags=["target"],
    ),
    14: Sprite(
        pixels=[[14]],
        name="target_green",
        visible=True,
        collidable=False,
        tags=["target"],
    ),
    15: Sprite(
        pixels=[[15]],
        name="target_purple",
        visible=True,
        collidable=False,
        tags=["target"],
    ),
    12: Sprite(
        pixels=[[12]],
        name="target_forbidden",
        visible=True,
        collidable=False,
        tags=["target"],
    ),
}


def make_signpost_level(
    grid_size,
    player_pos,
    target_positions_colors,
    wall_coords,
    dual_pairs: list[list[int]],
    cycle_interval,
    difficulty,
    forbidden_color: int = 12,
):
    sprite_list = [
        sprites["player"].clone().set_position(*player_pos),
    ]
    for pos, color in target_positions_colors:
        sprite_list.append(sprites[color].clone().set_position(*pos))
    for wp in wall_coords:
        sprite_list.append(sprites["wall"].clone().set_position(*wp))
    return Level(
        sprites=sprite_list,
        grid_size=grid_size,
        data={
            "dual_pairs": dual_pairs,
            "cycle_interval": cycle_interval,
            "difficulty": difficulty,
            "forbidden_color": forbidden_color,
        },
    )


levels = [
    make_signpost_level(
        (8, 8),
        (1, 1),
        [((3, 3), 8), ((5, 5), 8), ((3, 5), 14), ((5, 3), 14)],
        [],
        [[8, 14], [11, 15]],
        15,
        1,
    ),
    make_signpost_level(
        (8, 8),
        (1, 1),
        [
            ((3, 3), 8),
            ((5, 5), 8),
            ((3, 5), 14),
            ((5, 3), 14),
            ((2, 4), 11),
            ((4, 2), 11),
        ],
        [],
        [[8, 14], [11, 15], [8, 11]],
        12,
        2,
    ),
    make_signpost_level(
        (12, 12),
        (2, 2),
        [
            ((5, 5), 8),
            ((7, 7), 8),
            ((9, 5), 8),
            ((5, 9), 14),
            ((7, 5), 14),
            ((9, 7), 14),
            ((3, 6), 11),
            ((6, 3), 11),
            ((10, 10), 11),
            ((0, 11), 12),
        ],
        [],
        [[8, 14], [11, 8], [14, 11]],
        10,
        3,
    ),
    make_signpost_level(
        (16, 16),
        (2, 2),
        [
            ((5, 5), 8),
            ((10, 10), 8),
            ((7, 7), 14),
            ((12, 12), 14),
            ((5, 10), 11),
            ((10, 5), 11),
            ((7, 13), 15),
            ((13, 7), 15),
            ((15, 0), 12),
        ],
        [(4, 4), (6, 4), (4, 6), (8, 8), (9, 8), (8, 9), (11, 11)],
        [[8, 14], [11, 15]],
        10,
        4,
    ),
    make_signpost_level(
        (16, 16),
        (2, 2),
        [
            ((5, 5), 8),
            ((7, 7), 8),
            ((10, 10), 8),
            ((6, 6), 14),
            ((8, 8), 14),
            ((11, 11), 14),
            ((5, 11), 11),
            ((11, 5), 11),
            ((7, 12), 11),
            ((12, 7), 15),
            ((13, 8), 15),
            ((8, 13), 15),
        ],
        [
            (4, 4),
            (5, 4),
            (6, 5),
            (7, 6),
            (8, 7),
            (9, 8),
            (10, 9),
            (11, 10),
            (4, 10),
            (10, 4),
        ],
        [[8, 11], [14, 15], [8, 14], [11, 15]],
        8,
        5,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Rs03(ARCBaseGame):
    """Dual safe colors plus a forbidden stripe color that never becomes collectible."""

    WIN_HOLD_FRAMES = 14  # pause before next_level so GIFs show level clear

    def __init__(self) -> None:
        self._ui = Rs03UI()
        self._win_hold = 0
        super().__init__(
            "rs03",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._targets = list(self.current_level.get_sprites_by_tag("target"))
        self._dual_pairs: list[list[int]] = level.get_data("dual_pairs")
        self._cycle_interval = level.get_data("cycle_interval")
        self._pair_index = 0
        self._safe_a, self._safe_b = self._dual_pairs[0]
        self._safe_colors = tuple(
            c for pair in self._dual_pairs for c in pair
        ) or (self._safe_a, self._safe_b)
        self._cycle_index = 0
        self._all_cycled = False
        self._steps = 0
        self._win_hold = 0
        self._forbidden = int(level.get_data("forbidden_color") or 12)
        self._sync_ui()

    def _sync_ui(self) -> None:
        self._ui.update(
            self._safe_a,
            tuple(self._safe_colors),
            self._pair_index,
            self._all_cycled,
            len(self._targets),
            self.current_level.get_data("difficulty"),
            self._win_hold > 0,
            safe_b=self._safe_b,
            num_pairs=len(self._dual_pairs),
            forbidden=self._forbidden,
        )

    def _cycle_signpost(self) -> None:
        self._pair_index = (self._pair_index + 1) % len(self._dual_pairs)
        self._safe_a, self._safe_b = self._dual_pairs[self._pair_index]
        self._cycle_index = self._pair_index
        if self._pair_index == 0:
            self._all_cycled = True

    def step(self) -> None:
        if self._win_hold > 0:
            self._win_hold -= 1
            if self._win_hold == 0:
                self.next_level()
            self._sync_ui()
            self.complete_action()
            return

        dx = 0
        dy = 0

        if self.action.id == GameAction.ACTION1:
            dy = -1
        elif self.action.id == GameAction.ACTION2:
            dy = 1
        elif self.action.id == GameAction.ACTION3:
            dx = -1
        elif self.action.id == GameAction.ACTION4:
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

        if sprite and "target" in sprite.tags:
            target_color = sprite.pixels[0][0]
            if target_color == self._forbidden:
                self.lose()
                self.complete_action()
                return
            if target_color in (self._safe_a, self._safe_b):
                self.current_level.remove_sprite(sprite)
                self._targets.remove(sprite)
                self._player.set_position(new_x, new_y)
            elif self._all_cycled:
                self.current_level.remove_sprite(sprite)
                self._targets.remove(sprite)
                self._player.set_position(new_x, new_y)
            else:
                self.lose()
                self.complete_action()
                return
        elif not sprite or not sprite.is_collidable:
            self._player.set_position(new_x, new_y)

        self._steps += 1
        if self._steps % self._cycle_interval == 0:
            self._cycle_signpost()

        def _cleared() -> bool:
            return len(self._targets) == 0 or all(
                t.pixels[0][0] == self._forbidden for t in self._targets
            )

        if _cleared():
            self._win_hold = Rs03.WIN_HOLD_FRAMES

        self._sync_ui()
        self.complete_action()
