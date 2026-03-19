# MIT License
#
# Copyright (c) 2026 ARC Prize Foundation
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

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


class Sq01UI(RenderableUserDisplay):
    def __init__(self, sequence: list[str], progress: int, lives: int) -> None:
        self._sequence = sequence
        self._progress = progress
        self._lives = lives

        self._click_pos: tuple[int, int] | None = None
        self._click_frames = 0

        # Brief HUD flash feedback
        self._flash_color: int | None = None
        self._flash_frames = 0

    def update(self, sequence: list[str], progress: int, lives: int) -> None:
        self._sequence = sequence
        self._progress = progress
        self._lives = lives

    def flash(self, color: int, frames: int = 10) -> None:
        self._flash_color = color
        self._flash_frames = frames

    def set_click(self, x: int, y: int) -> None:
        self._click_pos = (x, y)
        self._click_frames = 10

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame

        h, w = frame.shape

        # --- HUD flash border (top rows) ---
        # Flash feedback (no big borders; just a small indicator near top-right)
        if self._flash_frames > 0 and self._flash_color is not None:
            c = self._flash_color
            # small 2x2 indicator in the top-right corner
            for dy in range(2):
                for dx in range(2):
                    px = w - 2 + dx
                    py = 0 + dy
                    if 0 <= px < w and 0 <= py < h:
                        frame[py, px] = c
            self._flash_frames -= 1
        else:
            self._flash_color = None

        # --- Lives (hearts) ---
        # Represent hearts as 2x2 red blocks in top-left.
        for i in range(3):
            heart_color = 8 if i < self._lives else 3
            base_x = 1 + i * 3
            base_y = 1
            for dy in range(2):
                for dx in range(2):
                    px = base_x + dx
                    py = base_y + dy
                    if 0 <= px < w and 0 <= py < h:
                        frame[py, px] = heart_color

        # --- Sequence bar ---
        # Tokens start after hearts area.
        token_w = 2
        token_h = 2
        token_gap = 1
        start_x = 1 + 3 * 3 + 2  # hearts area (3 hearts * 3 cols) + padding
        row_y = 1

        for i, color_name in enumerate(self._sequence):
            color = SEQUENCE_COLORS.get(color_name, 11)
            x0 = start_x + i * (token_w + token_gap)
            y0 = row_y

            if i < self._progress:
                # Completed: filled
                fill = color
                for dy in range(token_h):
                    for dx in range(token_w):
                        px, py = x0 + dx, y0 + dy
                        if 0 <= px < w and 0 <= py < h:
                            frame[py, px] = fill
            elif i == self._progress:
                # Current: filled + bright border
                for dy in range(token_h):
                    for dx in range(token_w):
                        px, py = x0 + dx, y0 + dy
                        if 0 <= px < w and 0 <= py < h:
                            frame[py, px] = color
                # Border effect by setting surrounding pixels to white if available
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
                # Future: dim placeholder with colored center pixel
                for dy in range(token_h):
                    for dx in range(token_w):
                        px, py = x0 + dx, y0 + dy
                        if 0 <= px < w and 0 <= py < h:
                            frame[py, px] = 3
                cx, cy = x0, y0
                if 0 <= cx < w and 0 <= cy < h:
                    frame[cy, cx] = color

        # --- Click indicator (crosshair) ---
        if self._click_pos and self._click_frames > 0:
            cx, cy = self._click_pos
            cross_color = 12
            points = [
                (cx, cy),
                (cx - 1, cy),
                (cx + 1, cy),
                (cx, cy - 1),
                (cx, cy + 1),
            ]
            for px, py in points:
                if 0 <= px < w and 0 <= py < h:
                    frame[py, px] = cross_color
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
            sprite = sprites[color_name].clone().set_position(pos[0], pos[1])
            sprite_list.append(sprite)

    step_limit = 20 + len(sequence) * 10

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
        {
            "red": (2, 6),
            "blue": (8, 5),
        },
        1,
    ),
    make_sequence_level(
        (12, 12),
        ["red", "blue", "green"],
        {
            "red": (2, 5),
            "blue": (9, 6),
            "green": (5, 9),
        },
        2,
    ),
    make_sequence_level(
        (12, 12),
        ["red", "blue", "green", "yellow"],
        {
            "red": (2, 4),
            "blue": (9, 4),
            "green": (3, 9),
            "yellow": (8, 9),
        },
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
]


class Sq01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Sq01UI([], 0, 3)
        self._end_frames = 0
        self._pending_advance = False
        self._pending_lose = False

        super().__init__(
            "sq01",
            levels,
            Camera(0, 0, 12, 12, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [6],
        )

    def on_set_level(self, level: Level) -> None:
        self._sequence: list[str] = level.get_data("sequence")
        self._step_limit: int = level.get_data("step_limit")

        self._steps = 0
        self._progress = 0
        self._lives = 3  # reset each level

        self._end_frames = 0
        self._pending_advance = False
        self._pending_lose = False

        self._ui.update(self._sequence, self._progress, self._lives)

        # Map colors to sprites currently in the level
        self._color_to_sprite: dict[str, Sprite] = {}
        for sprite in self.current_level.get_sprites_by_tag("sequence_item"):
            for tag in sprite.tags:
                if tag.startswith("color_"):
                    color_name = tag.replace("color_", "")
                    self._color_to_sprite[color_name] = sprite
                    break

    def _handle_wrong_click(self) -> None:
        # Option A: lose a life AND reset progress
        self._lives -= 1
        self._progress = 0
        self._ui.flash(8, frames=12)
        self._ui.update(self._sequence, self._progress, self._lives)

        if self._lives <= 0:
            self._pending_lose = True
            self._end_frames = 12

    def step(self) -> None:
        # End-of-level pacing so win/lose is visible in GIF
        if self._end_frames > 0:
            self._end_frames -= 1
            if self._end_frames == 0:
                if self._pending_advance:
                    self.next_level()
                elif self._pending_lose:
                    self.lose()
            self.complete_action()
            return

        if self.action.id == GameAction.ACTION6:
            x = self.action.data.get("x", 0)
            y = self.action.data.get("y", 0)

            coords = self.camera.display_to_grid(x, y)
            if not coords:
                self._handle_wrong_click()
                self.complete_action()
                return

            gx, gy = coords
            self._ui.set_click(gx, gy)

            clicked_sprite = None
            clicked_color: str | None = None

            # 2x2 sprites; hit test in grid coords
            for color_name, sprite in self._color_to_sprite.items():
                sx, sy = sprite.x, sprite.y
                if sx <= gx < sx + 2 and sy <= gy < sy + 2:
                    clicked_sprite = sprite
                    clicked_color = color_name
                    break

            if not clicked_sprite or clicked_color is None:
                self._handle_wrong_click()
                self.complete_action()
                return

            # Correct?
            expected_color = self._sequence[self._progress]
            if clicked_color == expected_color:
                self.current_level.remove_sprite(clicked_sprite)
                del self._color_to_sprite[clicked_color]

                self._progress += 1
                self._ui.update(self._sequence, self._progress, self._lives)

                if self._progress >= len(self._sequence):
                    self._pending_advance = True
                    self._end_frames = 12
                    self._ui.flash(14, frames=12)
            else:
                self._handle_wrong_click()

        self._steps += 1
        if (
            self._steps >= self._step_limit
            and not self._pending_advance
            and not self._pending_lose
        ):
            self._pending_lose = True
            self._end_frames = 12
            self._ui.flash(8, frames=12)

        self.complete_action()
