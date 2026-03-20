from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


PATTERN_SPRITE = Sprite(
    pixels=[[9]],
    name="pattern",
    visible=True,
    collidable=False,
    tags=["pattern"],
)

PLAYER_SPRITE = Sprite(
    pixels=[[14]],
    name="player_block",
    visible=True,
    collidable=False,
    tags=["player_block"],
)

DIVIDER_SPRITE = Sprite(
    pixels=[[3]],
    name="divider",
    visible=True,
    collidable=False,
    tags=["divider"],
)


class Sy01UI(RenderableUserDisplay):
    """HUD + place/remove flash + expanding click ring (64×64 frame space)."""

    CLICK_ANIM_FRAMES = 18

    def __init__(
        self, moves_remaining: int, placed_count: int, target_count: int
    ) -> None:
        self._moves_remaining = moves_remaining
        self._placed_count = placed_count
        self._target_count = target_count
        self._placed_pos = None
        self._placed_frames = 0
        self._click_pos: tuple[int, int] | None = None
        self._click_frames = 0

    def update(
        self, moves_remaining: int, placed_count: int, target_count: int
    ) -> None:
        self._moves_remaining = moves_remaining
        self._placed_count = placed_count
        self._target_count = target_count

    def set_click(self, frame_x: int, frame_y: int) -> None:
        """Ripple + crosshair at tap (inverse of display_to_grid); see create-arc-game SKILL."""
        self._click_pos = (frame_x, frame_y)
        self._click_frames = Sy01UI.CLICK_ANIM_FRAMES

    def set_placed(self, frame_x: int, frame_y: int) -> None:
        """Highlight last place/remove in final 64×64 frame pixel coordinates."""
        self._placed_pos = (frame_x, frame_y)
        self._placed_frames = 5

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
    def _draw_plus(
        cls, frame, h: int, w: int, cx: int, cy: int, arm: int, color: int
    ) -> None:
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

        if self._placed_pos and self._placed_frames > 0:
            cx, cy = self._placed_pos
            if 0 <= cx < w and 0 <= cy < h:
                for ox, oy in [
                    (-1, 0),
                    (1, 0),
                    (0, -1),
                    (0, 1),
                    (-1, -1),
                    (-1, 1),
                    (1, -1),
                    (1, 1),
                ]:
                    px, py = cx + ox, cy + oy
                    if 0 <= px < w and 0 <= py < h:
                        frame[py, px] = 11
                frame[cy, cx] = 11
            self._placed_frames -= 1
        else:
            self._placed_pos = None

        if self._click_pos and self._click_frames > 0:
            cx, cy = self._click_pos
            phase = Sy01UI.CLICK_ANIM_FRAMES - self._click_frames
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

        progress_y = h - 2
        progress_x = 2
        progress_width = min(self._target_count, 8)
        filled = (
            int((self._placed_count / self._target_count) * progress_width)
            if self._target_count > 0
            else 0
        )

        for i in range(progress_width):
            color = 14 if i < filled else 4
            frame[progress_y, progress_x + i] = color

        moves_text_x = w - 10
        moves_color = (
            8
            if self._moves_remaining < 10
            else (11 if self._moves_remaining < 20 else 14)
        )
        for i, digit in enumerate(str(self._moves_remaining).zfill(3)):
            if digit.isdigit():
                frame[1, moves_text_x + i] = moves_color

        return frame


BACKGROUND_COLOR = 5
PADDING_COLOR = 4
PATTERN_COLOR = 9
PLAYER_COLOR = 14
CURSOR_COLOR = 8
CENTER_X = 5
GRID_WIDTH = 11
MAX_MOVES = 50


def make_level(pattern_positions: list, difficulty: int):
    sprites = []

    sprites.append(DIVIDER_SPRITE.clone().set_position(CENTER_X, 0))
    sprites.append(DIVIDER_SPRITE.clone().set_position(CENTER_X, 1))
    sprites.append(DIVIDER_SPRITE.clone().set_position(CENTER_X, 2))
    sprites.append(DIVIDER_SPRITE.clone().set_position(CENTER_X, 3))
    sprites.append(DIVIDER_SPRITE.clone().set_position(CENTER_X, 4))
    sprites.append(DIVIDER_SPRITE.clone().set_position(CENTER_X, 5))
    sprites.append(DIVIDER_SPRITE.clone().set_position(CENTER_X, 6))
    sprites.append(DIVIDER_SPRITE.clone().set_position(CENTER_X, 7))
    sprites.append(DIVIDER_SPRITE.clone().set_position(CENTER_X, 8))
    sprites.append(DIVIDER_SPRITE.clone().set_position(CENTER_X, 9))
    sprites.append(DIVIDER_SPRITE.clone().set_position(CENTER_X, 10))

    for pos in pattern_positions:
        sprites.append(PATTERN_SPRITE.clone().set_position(pos[0], pos[1]))

    return Level(
        sprites=sprites,
        grid_size=(GRID_WIDTH, GRID_WIDTH),
        data={
            "pattern_positions": pattern_positions,
            "target_count": len(pattern_positions),
            "max_moves": MAX_MOVES + difficulty * 10,
            "difficulty": difficulty,
        },
        name=f"Level {difficulty}",
    )


# Patterns live in columns 0–4 only (divider at x=5); mirrors fall in 6–10.
levels = [
    make_level([(2, 3), (3, 5), (4, 4)], 1),
    make_level([(1, 2), (2, 5), (3, 3), (4, 6), (2, 8)], 2),
    make_level([(1, 1), (2, 4), (3, 6), (4, 2), (1, 7), (3, 8), (2, 9)], 3),
    make_level(
        [(1, 2), (1, 5), (2, 3), (3, 7), (4, 4), (1, 8), (3, 8), (4, 6), (2, 6)], 4
    ),
    make_level(
        [
            (1, 1),
            (1, 5),
            (1, 9),
            (2, 3),
            (2, 7),
            (3, 2),
            (3, 6),
            (4, 1),
            (4, 4),
            (4, 8),
            (3, 9),
            (2, 1),
        ],
        5,
    ),
]


class Sy01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Sy01UI(MAX_MOVES, 0, 0)
        self._placed_blocks = []
        self._pattern_positions = []
        self._target_mirror_positions = []
        self._moves_used = 0
        self._max_moves = MAX_MOVES
        self._end_frames = 0
        self._pending_advance = False
        super().__init__(
            "sy01",
            levels,
            Camera(
                0,
                0,
                GRID_WIDTH,
                GRID_WIDTH,
                BACKGROUND_COLOR,
                PADDING_COLOR,
                [self._ui],
            ),
            False,
            1,
            [6],
        )

    def _get_mirror_position(self, x: int, y: int) -> tuple:
        mirrored_x = GRID_WIDTH - 1 - x
        return (mirrored_x, y)

    def on_set_level(self, level: Level) -> None:
        self._pattern_positions = level.get_data("pattern_positions")
        self._target_count = level.get_data("target_count")
        self._max_moves = level.get_data("max_moves")
        self._moves_used = 0
        self._placed_blocks = []

        self._target_mirror_positions = set()
        for px, py in self._pattern_positions:
            mx, my = self._get_mirror_position(px, py)
            self._target_mirror_positions.add((mx, my))

        self._ui.update(self._max_moves - self._moves_used, 0, self._target_count)
        self._end_frames = 0
        self._pending_advance = False

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

    def _get_placed_count(self) -> int:
        count = 0
        for block in self._placed_blocks:
            if (block.x, block.y) in self._target_mirror_positions:
                count += 1
        return count

    def _check_win(self) -> bool:
        placed_set = set((b.x, b.y) for b in self._placed_blocks)
        return placed_set == self._target_mirror_positions

    def _click_at(self, x: int, y: int) -> None:
        existing = self.current_level.get_sprite_at(x, y, ignore_collidable=True)
        if existing and "player_block" in existing.tags:
            self.current_level.remove_sprite(existing)
            self._placed_blocks.remove(existing)
            self._ui.set_placed(*self._grid_to_frame_pixel(x, y))
        elif x >= 6 and x < GRID_WIDTH:
            new_block = PLAYER_SPRITE.clone().set_position(x, y)
            self.current_level.add_sprite(new_block)
            self._placed_blocks.append(new_block)
            self._ui.set_placed(*self._grid_to_frame_pixel(x, y))

    def step(self) -> None:
        if self._end_frames > 0:
            self._end_frames -= 1
            placed_count = self._get_placed_count()
            moves_remaining = self._max_moves - self._moves_used
            self._ui.update(moves_remaining, placed_count, self._target_count)
            if self._end_frames == 0 and self._pending_advance:
                self.next_level()
                self._pending_advance = False
            self.complete_action()
            return

        self._moves_used += 1

        cx = self.action.data.get("x", 0)
        cy = self.action.data.get("y", 0)
        coords = self.camera.display_to_grid(cx, cy)
        if coords is not None:
            gx, gy = int(coords[0]), int(coords[1])
            self._ui.set_click(*self._grid_to_frame_pixel(gx, gy))
            self._click_at(gx, gy)

        placed_count = self._get_placed_count()
        moves_remaining = self._max_moves - self._moves_used
        self._ui.update(moves_remaining, placed_count, self._target_count)

        if self._check_win():
            self._pending_advance = True
            self._end_frames = 12
        elif moves_remaining <= 0:
            self.lose()

        self.complete_action()
