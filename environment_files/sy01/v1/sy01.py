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
    def __init__(
        self, moves_remaining: int, placed_count: int, target_count: int
    ) -> None:
        self._moves_remaining = moves_remaining
        self._placed_count = placed_count
        self._target_count = target_count
        self._placed_pos = None
        self._placed_frames = 0

    def update(
        self, moves_remaining: int, placed_count: int, target_count: int
    ) -> None:
        self._moves_remaining = moves_remaining
        self._placed_count = placed_count
        self._target_count = target_count

    def set_placed(self, x: int, y: int) -> None:
        self._placed_pos = (x, y)
        self._placed_frames = 5

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


levels = [
    make_level([(2, 2), (2, 5), (3, 4)], 1),
    make_level([(1, 3), (2, 5), (3, 2), (4, 7), (2, 7)], 2),
    make_level([(1, 1), (2, 3), (3, 5), (4, 2), (1, 7), (4, 8), (2, 8)], 3),
    make_level(
        [(1, 1), (1, 4), (2, 2), (3, 6), (4, 3), (1, 8), (3, 8), (4, 6), (2, 7)], 4
    ),
    make_level(
        [
            (1, 1),
            (1, 5),
            (1, 8),
            (2, 2),
            (2, 6),
            (3, 3),
            (3, 7),
            (4, 1),
            (4, 4),
            (4, 7),
            (3, 9),
            (1, 3),
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
        elif x >= 6 and x < GRID_WIDTH:
            new_block = PLAYER_SPRITE.clone().set_position(x, y)
            self.current_level.add_sprite(new_block)
            self._placed_blocks.append(new_block)
            self._ui.set_placed(x, y)

    def step(self) -> None:
        self._moves_used += 1

        cx = self._action.data.get("x", 0)
        cy = self._action.data.get("y", 0)
        grid_x = cx // (64 // GRID_WIDTH)
        grid_y = cy // (64 // GRID_WIDTH)
        self._click_at(grid_x, grid_y)

        placed_count = self._get_placed_count()
        moves_remaining = self._max_moves - self._moves_used
        self._ui.update(moves_remaining, placed_count, self._target_count)

        if self._check_win():
            self.next_level()
        elif moves_remaining <= 0:
            self.lose()

        self.complete_action()
