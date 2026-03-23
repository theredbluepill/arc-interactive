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


class Sq03UI(RenderableUserDisplay):
    # Long enough for a clear “tap” read in GIFs and terminal previews
    CLICK_ANIM_FRAMES = 20

    def __init__(self, sequence: list[str], progress: int, lives: int) -> None:
        self._sequence = sequence
        self._progress = progress
        self._lives = lives
        self._steps_used = 0
        self._step_limit = 1

        self._click_pos: tuple[int, int] | None = None
        self._click_frames = 0

        # Brief HUD flash feedback
        self._flash_color: int | None = None
        self._flash_frames = 0
        # Cold-start: blink pixels so display / tap is salient (only ACTION6 is legal).
        self._click_hint_frames = 0

    def start_click_hint(self, frames: int = 36) -> None:
        self._click_hint_frames = frames

    def update(
        self,
        sequence: list[str],
        progress: int,
        lives: int,
        *,
        steps_used: int = 0,
        step_limit: int = 1,
    ) -> None:
        self._sequence = sequence
        self._progress = progress
        self._lives = lives
        self._steps_used = steps_used
        self._step_limit = max(1, step_limit)

    def flash(self, color: int, frames: int = 10) -> None:
        self._flash_color = color
        self._flash_frames = frames

    def set_click(self, frame_x: int, frame_y: int) -> None:
        """Ripple + crosshair in final 64×64 frame coords (after camera scale/letterbox)."""
        self._click_pos = (frame_x, frame_y)
        self._click_frames = Sq03UI.CLICK_ANIM_FRAMES

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

        # --- Click feedback: expanding/contracting ring + cross (64×64 frame space) ---
        if self._click_pos and self._click_frames > 0:
            cx, cy = self._click_pos
            phase = Sq03UI.CLICK_ANIM_FRAMES - self._click_frames

            # Chebyshev ring: grows 1→4 then shrinks (one orbit)
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

        # Step budget (remaining steps before timeout lose).
        lim = self._step_limit
        rem = max(0, lim - self._steps_used)
        bar_w = max(0, min(24, rem * 24 // lim))
        row_s = h - 1
        for i in range(min(24, w - 2)):
            c = 10 if i < bar_w else 3
            self._plot_px(frame, h, w, 1 + i, row_s, c)

        if self._click_hint_frames > 0:
            c = 0 if (self._click_hint_frames // 3) % 2 == 0 else 10
            self._plot_px(frame, h, w, w - 3, h - 2, c)
            self._plot_px(frame, h, w, w - 2, h - 2, c)
            self._click_hint_frames -= 1

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


def make_dual_level(
    grid_size: tuple,
    sequence_a: list,
    sequence_b: list,
    block_positions: dict,
    difficulty: int,
):
    seen: set[str] = set()
    order: list[str] = []
    for c in sequence_a + sequence_b:
        if c not in seen:
            seen.add(c)
            order.append(c)
    sprite_list = []
    for color_name in order:
        pos = block_positions.get(color_name)
        if pos and color_name in sprites:
            sprite_list.append(
                sprites[color_name].clone().set_position(pos[0], pos[1])
            )

    step_limit = 24 + (len(sequence_a) + len(sequence_b)) * 10

    return Level(
        sprites=sprite_list,
        grid_size=grid_size,
        data={
            "sequence_a": sequence_a,
            "sequence_b": sequence_b,
            "block_positions": block_positions,
            "difficulty": difficulty,
            "step_limit": step_limit,
        },
        name=f"Level {difficulty}",
    )


levels = [
    make_dual_level(
        (12, 12),
        ["red", "blue"],
        ["green", "yellow"],
        {
            "red": (2, 6),
            "blue": (8, 5),
            "green": (5, 9),
            "yellow": (9, 8),
        },
        1,
    ),
    make_dual_level(
        (12, 12),
        ["red", "green"],
        ["blue", "yellow"],
        {
            "red": (2, 5),
            "green": (5, 9),
            "blue": (9, 6),
            "yellow": (3, 3),
        },
        2,
    ),
    make_dual_level(
        (12, 12),
        ["red", "yellow", "cyan"],
        ["blue", "green", "purple"],
        {
            "red": (2, 4),
            "yellow": (2, 9),
            "cyan": (5, 10),
            "blue": (9, 4),
            "green": (5, 6),
            "purple": (9, 9),
        },
        3,
    ),
    make_dual_level(
        (12, 12),
        ["red", "green", "purple"],
        ["blue", "yellow", "cyan"],
        {
            "red": (2, 4),
            "green": (5, 7),
            "purple": (9, 9),
            "blue": (9, 4),
            "yellow": (2, 9),
            "cyan": (5, 10),
        },
        4,
    ),
    make_dual_level(
        (12, 12),
        ["red", "yellow", "purple"],
        ["blue", "green", "cyan"],
        {
            "red": (2, 4),
            "yellow": (2, 9),
            "purple": (9, 9),
            "blue": (9, 4),
            "green": (5, 6),
            "cyan": (5, 10),
        },
        5,
    ),
]


class Sq03(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Sq03UI([], 0, 3)
        self._end_frames = 0
        self._pending_advance = False
        self._pending_lose = False
        self._ripple_tail = 0

        super().__init__(
            "sq03",
            levels,
            Camera(0, 0, 12, 12, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [6],
        )

    def on_set_level(self, level: Level) -> None:
        self._seq_a: list[str] = level.get_data("sequence_a")
        self._seq_b: list[str] = level.get_data("sequence_b")
        self._step_limit: int = level.get_data("step_limit")

        self._steps = 0
        self._pa = 0
        self._pb = 0
        self._lives = 3  # reset each level

        self._end_frames = 0
        self._pending_advance = False
        self._pending_lose = False
        self._ripple_tail = 0

        disp = self._seq_a + self._seq_b
        self._ui.update(
            disp,
            self._pa + self._pb,
            self._lives,
            steps_used=self._steps,
            step_limit=self._step_limit,
        )
        self._ui.start_click_hint(40)

        # Map colors to sprites currently in the level
        self._color_to_sprite: dict[str, Sprite] = {}
        for sprite in self.current_level.get_sprites_by_tag("sequence_item"):
            for tag in sprite.tags:
                if tag.startswith("color_"):
                    color_name = tag.replace("color_", "")
                    self._color_to_sprite[color_name] = sprite
                    break
        self._sync_visibility()

    def _sync_visibility(self) -> None:
        heads: set[str] = set()
        if self._pa < len(self._seq_a):
            heads.add(self._seq_a[self._pa])
        if self._pb < len(self._seq_b):
            heads.add(self._seq_b[self._pb])
        for color_name, sprite in self._color_to_sprite.items():
            sprite.set_visible(color_name in heads)

    def _grid_to_frame_pixel(self, gx: int, gy: int) -> tuple[int, int]:
        """Map level grid coords to pixels on the final 64×64 frame (inverse of display_to_grid)."""
        cam = self.camera
        cw, ch = cam.width, cam.height
        scale_x = int(64 / cw)
        scale_y = int(64 / ch)
        scale = min(scale_x, scale_y)
        x_pad = int((64 - (cw * scale)) / 2)
        y_pad = int((64 - (ch * scale)) / 2)
        px = gx * scale + scale // 2 + x_pad
        py = gy * scale + scale // 2 + y_pad
        return px, py

    def _reset_blocks(self) -> None:
        for s in list(self.current_level.get_sprites_by_tag("sequence_item")):
            self.current_level.remove_sprite(s)
        self._color_to_sprite.clear()
        pos_map = self.current_level.get_data("block_positions") or {}
        seen: set[str] = set()
        for color_name in self._seq_a + self._seq_b:
            if color_name in seen:
                continue
            seen.add(color_name)
            pos = pos_map.get(color_name)
            if not pos or color_name not in sprites:
                continue
            sp = sprites[color_name].clone().set_position(pos[0], pos[1])
            self.current_level.add_sprite(sp)
            self._color_to_sprite[color_name] = sp
        self._sync_visibility()

    def _handle_wrong_click(self) -> None:
        # Option A: lose a life AND reset progress
        self._lives -= 1
        self._pa = 0
        self._pb = 0
        self._reset_blocks()
        self._ui.flash(8, frames=12)
        disp = self._seq_a + self._seq_b
        self._ui.update(
            disp,
            self._pa + self._pb,
            self._lives,
            steps_used=self._steps,
            step_limit=self._step_limit,
        )

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

        # Let click ripple animate across inner frames (one env.step → many renders)
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
                self._ripple_tail = Sq03UI.CLICK_ANIM_FRAMES - 1
                return

            gx, gy = coords
            self._ui.set_click(*self._grid_to_frame_pixel(gx, gy))

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
                self._steps += 1
                self._check_step_limit()
                if self._pending_lose and self._end_frames > 0:
                    self.complete_action()
                    return
                self._ripple_tail = Sq03UI.CLICK_ANIM_FRAMES - 1
                return

            hit_a = (
                self._pa < len(self._seq_a)
                and clicked_color == self._seq_a[self._pa]
            )
            hit_b = (
                self._pb < len(self._seq_b)
                and clicked_color == self._seq_b[self._pb]
            )
            if hit_a and hit_b:
                self._handle_wrong_click()
                self._steps += 1
                self._check_step_limit()
                if self._pending_lose and self._end_frames > 0:
                    self.complete_action()
                    return
                self._ripple_tail = Sq03UI.CLICK_ANIM_FRAMES - 1
                return
            if hit_a:
                self._pa += 1
            elif hit_b:
                self._pb += 1
            else:
                self._handle_wrong_click()
                self._steps += 1
                self._check_step_limit()
                if self._pending_lose and self._end_frames > 0:
                    self.complete_action()
                    return
                self._ripple_tail = Sq03UI.CLICK_ANIM_FRAMES - 1
                return

            self.current_level.remove_sprite(clicked_sprite)
            del self._color_to_sprite[clicked_color]
            disp = self._seq_a + self._seq_b
            self._ui.update(
                disp,
                self._pa + self._pb,
                self._lives,
                steps_used=self._steps,
                step_limit=self._step_limit,
            )
            self._sync_visibility()

            if self._pa >= len(self._seq_a) and self._pb >= len(self._seq_b):
                self._pending_advance = True
                self._end_frames = 12
                self._ui.flash(14, frames=12)
                self._steps += 1
                self._check_step_limit()
                self.complete_action()
                return

            self._steps += 1
            self._check_step_limit()
            self._ripple_tail = Sq03UI.CLICK_ANIM_FRAMES - 1
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
