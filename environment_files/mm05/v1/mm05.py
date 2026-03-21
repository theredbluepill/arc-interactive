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

from __future__ import annotations

from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)

BACKGROUND_COLOR = 5
PADDING_COLOR = 5
HIDDEN_COLOR = 3

CAMERA_SIZE = 64
MAX_STEPS = 60

# Hardcoded (no procedural randomness) color layouts.
# Each level uses num_tiles = num_pairs*2 tiles in row-major order.
LEVEL_LAYOUTS: list[list[int]] = [
    # Level 1: 2 pairs (4 tiles) -> 2x2
    [8, 9, 9, 8],
    # Level 2: 3 pairs (6 tiles) -> 2x3
    [8, 11, 9, 9, 11, 8],
    # Level 3: 4 pairs (8 tiles) -> 2x4
    [8, 12, 9, 11, 11, 9, 12, 8],
    # Level 4: 5 pairs (10 tiles) -> 2x5
    [8, 14, 9, 12, 11, 11, 12, 9, 14, 8],
    # Level 5: 6 pairs (12 tiles) -> 3x4
    [8, 15, 9, 14, 11, 12, 12, 11, 14, 9, 15, 8],
    # Level 6: 7 pairs (14 tiles) -> 2x7
    [8, 10, 9, 15, 11, 14, 12, 12, 14, 11, 15, 9, 10, 8],
    # Level 7: 8 pairs (16 tiles) -> 4x4
    [8, 6, 9, 10, 11, 15, 12, 14, 14, 12, 15, 11, 10, 9, 6, 8],
]

# For each level, choose exact rows/cols (no ghost tiles).
LEVEL_DIMS: list[tuple[int, int]] = [
    (2, 2),  # 4
    (2, 3),  # 6
    (2, 4),  # 8
    (2, 5),  # 10
    (3, 4),  # 12
    (2, 7),  # 14
    (4, 4),  # 16
]


def _compute_tile_size_and_offsets(rows: int, cols: int) -> tuple[int, int, int]:
    # Use most of the 64x64 canvas.
    # Leave a small margin so the top time bar doesn't feel cramped.
    target = 56
    tile_size = max(2, target // max(rows, cols))
    grid_w = cols * tile_size
    grid_h = rows * tile_size
    offset_x = (CAMERA_SIZE - grid_w) // 2
    offset_y = (CAMERA_SIZE - grid_h) // 2
    return tile_size, offset_x, offset_y


def make_hidden_sprite(slot_index: int, tile_size: int) -> Sprite:
    pixels = [[HIDDEN_COLOR] * tile_size for _ in range(tile_size)]
    return Sprite(
        pixels=pixels,
        name=f"hidden_{slot_index}",
        visible=True,
        collidable=False,
        tags=["hidden", f"slot_{slot_index}"],
    )


class Mm05UI(RenderableUserDisplay):
    def __init__(self, pairs_remaining: int) -> None:
        self._pairs_remaining = pairs_remaining
        self._steps_remaining = MAX_STEPS
        self._level = 1
        self._click_pos: tuple[int, int] | None = None
        self._click_frames = 0

    def update(self, pairs_remaining: int, steps_remaining: int, level: int = 1) -> None:
        self._pairs_remaining = pairs_remaining
        self._steps_remaining = steps_remaining
        self._level = level

    def set_click(self, x: int, y: int) -> None:
        """Tap marker in final 64×64 frame space (same coords as ACTION6)."""
        self._click_pos = (x, y)
        self._click_frames = 8

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape

        bar_width = max(0, min(20, self._steps_remaining * 20 // MAX_STEPS))
        for i in range(bar_width):
            frame[3, 2 + i] = 3

        # Level marker (blue + accent) — does not overlap the 2×2/L2+ tile grids
        frame[1, 2] = 9
        level_colors = [10, 11, 12, 14, 15, 6, 7]
        frame[1, 3] = level_colors[(self._level - 1) % len(level_colors)]

        if self._click_pos and self._click_frames > 0:
            cx, cy = self._click_pos
            if 0 <= cx < w and 0 <= cy < h:
                hit = 11
                for px, py in (
                    (cx, cy),
                    (cx - 1, cy),
                    (cx + 1, cy),
                    (cx, cy - 1),
                    (cx, cy + 1),
                ):
                    if 0 <= px < w and 0 <= py < h:
                        frame[py, px] = hit
            self._click_frames -= 1
        else:
            self._click_pos = None

        return frame


def create_level(level_index: int) -> Level:
    slot_colors = LEVEL_LAYOUTS[level_index]
    rows, cols = LEVEL_DIMS[level_index]

    tile_size, offset_x, offset_y = _compute_tile_size_and_offsets(rows, cols)

    sprites = []
    for slot_idx in range(len(slot_colors)):
        row = slot_idx // cols
        col = slot_idx % cols
        x = offset_x + col * tile_size
        y = offset_y + row * tile_size

        hidden = make_hidden_sprite(slot_idx, tile_size)
        hidden.set_position(x, y)
        sprites.append(hidden)

    return Level(
        sprites=sprites,
        grid_size=(CAMERA_SIZE, CAMERA_SIZE),
        data={
            "slot_colors": slot_colors,
            "num_pairs": len(slot_colors) // 2,
            "rows": rows,
            "cols": cols,
            "tile_size": tile_size,
            "offset_x": offset_x,
            "offset_y": offset_y,
            "level_index": level_index,
        },
        name=f"Level {level_index + 1}",
    )


class Mm05(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Mm05UI(2)
        self._display_level = 1
        super().__init__(
            "mm05",
            [create_level(i) for i in range(7)],
            Camera(
                0,
                0,
                CAMERA_SIZE,
                CAMERA_SIZE,
                BACKGROUND_COLOR,
                PADDING_COLOR,
                [self._ui],
            ),
            False,
            1,
            [6],
        )

    def on_set_level(self, level: Level) -> None:
        self._slot_colors = level.get_data("slot_colors")
        self._num_pairs = level.get_data("num_pairs")
        self._rows = level.get_data("rows")
        self._cols = level.get_data("cols")
        self._tile_size = level.get_data("tile_size")
        self._offset_x = level.get_data("offset_x")
        self._offset_y = level.get_data("offset_y")

        num_tiles = len(self._slot_colors)
        self._slots: list[Sprite | None] = [None] * num_tiles
        self._matched = [False] * num_tiles
        self._flipped = []
        self._pairs_remaining = self._num_pairs
        self._steps_remaining = MAX_STEPS
        self._waiting_for_flip_back = False
        self._flip_back_timer = 0

        for sprite in self.current_level.get_sprites_by_tag("hidden"):
            for tag in sprite.tags:
                if tag.startswith("slot_"):
                    slot_idx = int(tag.split("_")[1])
                    self._slots[slot_idx] = sprite

        self._display_level = level.get_data("level_index") + 1
        self._ui.update(self._pairs_remaining, self._steps_remaining, self._display_level)

    def _get_slot_from_click(self, click_x: int, click_y: int):
        col = (click_x - self._offset_x) // self._tile_size
        row = (click_y - self._offset_y) // self._tile_size

        if 0 <= row < self._rows and 0 <= col < self._cols:
            slot_idx = row * self._cols + col
            if 0 <= slot_idx < len(self._slot_colors):
                return row, col, slot_idx
        return None, None, None

    def _flip_slot(self, row: int, col: int) -> bool:
        slot_idx = row * self._cols + col
        if self._matched[slot_idx]:
            return False

        for tile in self._flipped:
            if tile[0] == row and tile[1] == col:
                return False

        # Sticky only for an **edge-aligned** matched pair (Manhattan distance 1):
        # block flips on cells that are orthogonal neighbors of **both** endpoints.
        # Diagonal (or distant) pairs do not create a shared neighbor on the grid.
        by_color: dict[int, list[int]] = {}
        for i, cl in enumerate(self._slot_colors):
            if self._matched[i]:
                by_color.setdefault(cl, []).append(i)
        for slots in by_color.values():
            if len(slots) != 2:
                continue
            a, b = slots
            ra, ca = a // self._cols, a % self._cols
            rb, cb = b // self._cols, b % self._cols
            if abs(ra - rb) + abs(ca - cb) != 1:
                continue

            def orth_neighbors(rr: int, cc: int) -> set[tuple[int, int]]:
                out: set[tuple[int, int]] = set()
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < self._rows and 0 <= nc < self._cols:
                        out.add((nr, nc))
                return out

            if (row, col) in (orth_neighbors(ra, ca) & orth_neighbors(rb, cb)):
                return False

        return True

    def _get_tile_color(self, slot_idx: int) -> int:
        return self._slot_colors[slot_idx]

    def _create_revealed_sprite(self, color: int, slot_idx: int) -> Sprite:
        pixels = [[color] * self._tile_size for _ in range(self._tile_size)]
        return Sprite(
            pixels=pixels,
            name=f"revealed_{slot_idx}",
            visible=True,
            collidable=False,
            tags=["revealed", f"slot_{slot_idx}"],
        )

    def step(self) -> None:
        self._steps_remaining -= 1
        self._ui.update(self._pairs_remaining, self._steps_remaining, self._display_level)

        if self._steps_remaining <= 0:
            self.lose()
            self.complete_action()
            return

        if self._waiting_for_flip_back:
            self._flip_back_timer -= 1
            if self._flip_back_timer <= 0:
                self._do_flip_back()
                self._waiting_for_flip_back = False
            self.complete_action()
            return

        if self.action.id.value == 6:
            x = self.action.data.get("x", 0)
            y = self.action.data.get("y", 0)
            if 0 <= int(x) < CAMERA_SIZE and 0 <= int(y) < CAMERA_SIZE:
                self._ui.set_click(int(x), int(y))

            row, col, slot_idx = self._get_slot_from_click(x, y)
            if row is None:
                self.complete_action()
                return

            if self._matched[slot_idx]:
                self.complete_action()
                return

            if not self._flip_slot(row, col):
                self.complete_action()
                return

            color = self._get_tile_color(slot_idx)
            sprite = self._slots[slot_idx]
            if sprite is None:
                self.complete_action()
                return

            revealed = self._create_revealed_sprite(color, slot_idx)
            revealed.set_position(sprite.x, sprite.y)
            self.current_level.add_sprite(revealed)
            sprite.set_visible(False)

            self._flipped.append((row, col, slot_idx, color))

            if len(self._flipped) == 2:
                first = self._flipped[0]
                second = self._flipped[1]

                if first[3] == second[3]:
                    self._matched[first[2]] = True
                    self._matched[second[2]] = True
                    self._pairs_remaining -= 1
                    self._flipped = []
                    self._ui.update(
                        self._pairs_remaining, self._steps_remaining, self._display_level
                    )

                    if self._pairs_remaining == 0:
                        self.next_level()
                else:
                    self._waiting_for_flip_back = True
                    self._flip_back_timer = 2

        self.complete_action()

    def _do_flip_back(self) -> None:
        for row, col, slot_idx, color in self._flipped:
            sprite = self._slots[slot_idx]
            if sprite:
                sprite.set_visible(True)

            for s in list(self.current_level._sprites):
                if f"slot_{slot_idx}" in s.tags and "revealed" in s.tags:
                    self.current_level.remove_sprite(s)

        self._flipped = []
