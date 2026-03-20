# MIT License
#
# Copyright (c) 2026 ARC Prize Foundation
#
# SPDX-License-Identifier: MIT

"""sq05: FIFO sequence with double-tap lock — each block needs two consecutive correct taps."""

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

SEQUENCE_COLORS = {
    "red": 8,
    "blue": 9,
    "green": 14,
    "yellow": 11,
    "orange": 12,
    "purple": 15,
    "cyan": 10,
    "magenta": 6,
}


class Sq05UI(RenderableUserDisplay):
    CLICK_ANIM_FRAMES = 20

    def __init__(self, sequence: list[str], progress: int, lives: int, streak: int) -> None:
        self._sequence = sequence
        self._progress = progress
        self._lives = lives
        self._streak = streak
        self._click_pos: tuple[int, int] | None = None
        self._click_frames = 0
        self._flash_color: int | None = None
        self._flash_frames = 0

    def update(
        self, sequence: list[str], progress: int, lives: int, streak: int
    ) -> None:
        self._sequence = sequence
        self._progress = progress
        self._lives = lives
        self._streak = streak

    def flash(self, color: int, frames: int = 10) -> None:
        self._flash_color = color
        self._flash_frames = frames

    def set_click(self, frame_x: int, frame_y: int) -> None:
        self._click_pos = (frame_x, frame_y)
        self._click_frames = Sq05UI.CLICK_ANIM_FRAMES

    @staticmethod
    def _plot_px(frame, h: int, w: int, px: int, py: int, color: int) -> None:
        if 0 <= px < w and 0 <= py < h:
            frame[py, px] = color

    @classmethod
    def _chebyshev_ring(
        cls, frame, h: int, w: int, cx: int, cy: int, r: int, color: int
    ) -> None:
        if r <= 0:
            return
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if max(abs(dx), abs(dy)) == r:
                    cls._plot_px(frame, h, w, cx + dx, cy + dy, color)

    @classmethod
    def _draw_plus(cls, frame, h: int, w: int, cx: int, cy: int, arm: int, color: int) -> None:
        cls._plot_px(frame, h, w, cx, cy, color)
        for a in range(1, arm + 1):
            cls._plot_px(frame, h, w, cx - a, cy, color)
            cls._plot_px(frame, h, w, cx + a, cy, color)
            cls._plot_px(frame, h, w, cx, cy - a, color)
            cls._plot_px(frame, h, w, cx, cy + a, color)

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame

        h, w = frame.shape

        if self._flash_frames > 0 and self._flash_color is not None:
            c = self._flash_color
            for dy in range(2):
                for dx in range(2):
                    px, py = w - 2 + dx, dy
                    if 0 <= px < w and 0 <= py < h:
                        frame[py, px] = c
            self._flash_frames -= 1
        else:
            self._flash_color = None

        for i in range(3):
            heart_color = 8 if i < self._lives else 3
            base_x, base_y = 1 + i * 3, 1
            for dy in range(2):
                for dx in range(2):
                    px, py = base_x + dx, base_y + dy
                    if 0 <= px < w and 0 <= py < h:
                        frame[py, px] = heart_color

        token_w, token_h, token_gap = 2, 2, 1
        start_x = 1 + 3 * 3 + 2
        row_y = 1

        for i, color_name in enumerate(self._sequence):
            color = SEQUENCE_COLORS.get(color_name, 11)
            x0 = start_x + i * (token_w + token_gap)
            y0 = row_y

            if i < self._progress:
                fill = color
                for dy in range(token_h):
                    for dx in range(token_w):
                        px, py = x0 + dx, y0 + dy
                        if 0 <= px < w and 0 <= py < h:
                            frame[py, px] = fill
            elif i == self._progress:
                for dy in range(token_h):
                    for dx in range(token_w):
                        px, py = x0 + dx, y0 + dy
                        if 0 <= px < w and 0 <= py < h:
                            frame[py, px] = color
                border = 0
                for dx in range(-1, token_w + 1):
                    for dy in (-1, token_h):
                        px, py = x0 + dx, y0 + dy
                        if 0 <= px < w and 0 <= py < h:
                            frame[py, px] = border
                for dy in range(0, token_h):
                    for dx in (-1, token_w):
                        px, py = x0 + dx, y0 + dy
                        if 0 <= px < w and 0 <= py < h:
                            frame[py, px] = border
            else:
                for dy in range(token_h):
                    for dx in range(token_w):
                        px, py = x0 + dx, y0 + dy
                        if 0 <= px < w and 0 <= py < h:
                            frame[py, px] = 3
                if 0 <= x0 < w and 0 <= y0 < h:
                    frame[y0, x0] = color

        # Double-tap progress dots (bottom-left)
        for t in range(2):
            col = 11 if t < self._streak else 3
            px, py = 58 + t * 3, h - 3
            if 0 <= px < w and 0 <= py < h:
                frame[py, px] = col

        if self._click_pos and self._click_frames > 0:
            cx, cy = self._click_pos
            phase = Sq05UI.CLICK_ANIM_FRAMES - self._click_frames
            if phase < 8:
                ring_r = phase + 1 if phase < 4 else 8 - phase
                if ring_r > 0:
                    ring_col = 0 if ring_r >= 4 else (11 if ring_r == 3 else 12)
                    self._chebyshev_ring(frame, h, w, cx, cy, ring_r, ring_col)
            arm = 2 if phase < 14 else 1
            plus_col = 0 if phase < 2 else 12
            self._draw_plus(frame, h, w, cx, cy, arm, plus_col)
            self._click_frames -= 1
        else:
            self._click_pos = None

        return frame


sprites = {
    color: Sprite(
        pixels=[[color_val, color_val], [color_val, color_val]],
        name=f"{color}_block",
        visible=True,
        collidable=False,
        tags=["sequence_item", f"color_{color}"],
    )
    for color, color_val in SEQUENCE_COLORS.items()
}


def make_sequence_level(
    grid_size: tuple,
    sequence: list,
    block_positions: dict,
    difficulty: int,
):
    sprite_list = []
    for color_name in sequence:
        pos = block_positions.get(color_name)
        if pos and color_name in sprites:
            sprite_list.append(
                sprites[color_name].clone().set_position(pos[0], pos[1])
            )

    step_limit = 30 + len(sequence) * 14

    return Level(
        sprites=sprite_list,
        grid_size=grid_size,
        data={
            "sequence": sequence,
            "block_positions": block_positions,
            "difficulty": difficulty,
            "step_limit": step_limit,
        },
        name=f"Level {difficulty}",
    )


levels = [
    make_sequence_level(
        (12, 12),
        ["red", "blue"],
        {"red": (2, 6), "blue": (8, 5)},
        1,
    ),
    make_sequence_level(
        (12, 12),
        ["red", "blue", "green"],
        {"red": (2, 5), "blue": (9, 6), "green": (5, 9)},
        2,
    ),
    make_sequence_level(
        (12, 12),
        ["red", "blue", "green", "yellow"],
        {"red": (2, 4), "blue": (9, 4), "green": (3, 9), "yellow": (8, 9)},
        3,
    ),
    make_sequence_level(
        (12, 12),
        ["red", "blue", "green", "yellow", "purple"],
        {
            "red": (2, 4),
            "blue": (9, 4),
            "green": (5, 7),
            "yellow": (2, 9),
            "purple": (9, 9),
        },
        4,
    ),
    make_sequence_level(
        (12, 12),
        ["red", "blue", "green", "yellow", "purple", "cyan"],
        {
            "red": (2, 4),
            "blue": (9, 4),
            "green": (5, 6),
            "yellow": (2, 9),
            "purple": (9, 9),
            "cyan": (5, 10),
        },
        5,
    ),
    make_sequence_level(
        (12, 12),
        ["red", "blue", "green", "yellow", "purple", "cyan", "orange"],
        {
            "red": (2, 5),
            "blue": (9, 5),
            "green": (4, 8),
            "yellow": (7, 8),
            "purple": (2, 10),
            "cyan": (9, 10),
            "orange": (5, 6),
        },
        6,
    ),
    make_sequence_level(
        (12, 12),
        ["red", "blue", "green", "yellow", "purple", "cyan", "orange", "magenta"],
        {
            "red": (2, 4),
            "blue": (9, 4),
            "green": (5, 5),
            "yellow": (2, 7),
            "purple": (9, 7),
            "cyan": (5, 9),
            "orange": (3, 10),
            "magenta": (8, 10),
        },
        7,
    ),
]


class Sq05(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Sq05UI([], 0, 3, 0)
        self._end_frames = 0
        self._pending_advance = False
        self._pending_lose = False
        self._ripple_tail = 0

        super().__init__(
            "sq05",
            levels,
            Camera(0, 0, 12, 12, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [6],
        )

    def on_set_level(self, level: Level) -> None:
        self._sequence = level.get_data("sequence")
        self._step_limit = level.get_data("step_limit")
        self._steps = 0
        self._progress = 0
        self._streak = 0
        self._lives = 3
        self._end_frames = 0
        self._pending_advance = False
        self._pending_lose = False
        self._ripple_tail = 0
        self._ui.update(self._sequence, self._progress, self._lives, self._streak)

        self._color_to_sprite: dict[str, Sprite] = {}
        for sprite in self.current_level.get_sprites_by_tag("sequence_item"):
            for tag in sprite.tags:
                if tag.startswith("color_"):
                    self._color_to_sprite[tag.replace("color_", "")] = sprite
                    break

    def _grid_to_frame_pixel(self, gx: int, gy: int) -> tuple[int, int]:
        cam = self.camera
        cw, ch = cam.width, cam.height
        scale = min(int(64 / cw), int(64 / ch))
        x_pad = int((64 - (cw * scale)) / 2)
        y_pad = int((64 - (ch * scale)) / 2)
        return (
            gx * scale + scale // 2 + x_pad,
            gy * scale + scale // 2 + y_pad,
        )

    def _handle_wrong_click(self) -> None:
        self._lives -= 1
        self._progress = 0
        self._streak = 0
        self._ui.flash(8, frames=12)
        self._ui.update(self._sequence, self._progress, self._lives, self._streak)
        if self._lives <= 0:
            self._pending_lose = True
            self._end_frames = 12

    def step(self) -> None:
        if self._end_frames > 0:
            self._end_frames -= 1
            if self._end_frames == 0:
                if self._pending_advance:
                    self.next_level()
                elif self._pending_lose:
                    self.lose()
            self.complete_action()
            return

        if self._ripple_tail > 0:
            self._ripple_tail -= 1
            if self._ripple_tail == 0:
                self.complete_action()
            return

        if self.action.id == GameAction.ACTION6:
            x = self.action.data.get("x", 0)
            y = self.action.data.get("y", 0)
            coords = self.camera.display_to_grid(x, y)
            if not coords:
                cx = max(0, min(63, int(x)))
                cy = max(0, min(63, int(y)))
                self._ui.set_click(cx, cy)
                self._handle_wrong_click()
                self._steps += 1
                self._check_step_limit()
                if self._pending_lose and self._end_frames > 0:
                    self.complete_action()
                    return
                self._ripple_tail = Sq05UI.CLICK_ANIM_FRAMES - 1
                return

            gx, gy = coords
            self._ui.set_click(*self._grid_to_frame_pixel(gx, gy))

            clicked_color: str | None = None
            for color_name, sprite in self._color_to_sprite.items():
                sx, sy = sprite.x, sprite.y
                if sx <= gx < sx + 2 and sy <= gy < sy + 2:
                    clicked_color = color_name
                    break

            if clicked_color is None:
                self._handle_wrong_click()
                self._steps += 1
                self._check_step_limit()
                if self._pending_lose and self._end_frames > 0:
                    self.complete_action()
                    return
                self._ripple_tail = Sq05UI.CLICK_ANIM_FRAMES - 1
                return

            expected_color = self._sequence[self._progress]
            if clicked_color != expected_color:
                self._handle_wrong_click()
                self._steps += 1
                self._check_step_limit()
                if self._pending_lose and self._end_frames > 0:
                    self.complete_action()
                    return
                self._ripple_tail = Sq05UI.CLICK_ANIM_FRAMES - 1
                return

            self._streak += 1
            self._ui.update(self._sequence, self._progress, self._lives, self._streak)

            if self._streak >= 2:
                sp = self._color_to_sprite[clicked_color]
                self.current_level.remove_sprite(sp)
                del self._color_to_sprite[clicked_color]
                self._progress += 1
                self._streak = 0
                self._ui.update(
                    self._sequence, self._progress, self._lives, self._streak
                )
                if self._progress >= len(self._sequence):
                    self._pending_advance = True
                    self._end_frames = 12
                    self._ui.flash(14, frames=12)
                    self._steps += 1
                    self._check_step_limit()
                    self.complete_action()
                    return

            self._steps += 1
            self._check_step_limit()
            self._ripple_tail = Sq05UI.CLICK_ANIM_FRAMES - 1
            return

        self._steps += 1
        self._check_step_limit()
        self.complete_action()

    def _check_step_limit(self) -> None:
        if (
            self._steps >= self._step_limit
            and not self._pending_advance
            and not self._pending_lose
        ):
            self._pending_lose = True
            self._end_frames = 12
            self._ui.flash(8, frames=12)
