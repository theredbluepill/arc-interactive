from arcengine import (
    ARCBaseGame,
    Camera,
    GameAction,
    Level,
    RenderableUserDisplay,
    Sprite,
)
import random


class Wm03UI(RenderableUserDisplay):
    def __init__(
        self, lives: int, score: int, checkpoint_score: int, checkpoint_total: int
    ) -> None:
        self._lives = lives
        self._score = score
        self._checkpoint_score = checkpoint_score
        self._checkpoint_total = checkpoint_total
        self._click_pos = None
        self._click_frames = 0
        self._level = 1
        self._mole_appeared = 0

    def update(
        self,
        lives: int,
        score: int,
        checkpoint_score: int,
        checkpoint_total: int,
        level: int = 1,
    ) -> None:
        self._lives = lives
        self._score = score
        self._checkpoint_score = checkpoint_score
        self._checkpoint_total = checkpoint_total
        self._level = level

    def set_click(self, x: int, y: int) -> None:
        """Record a click position to display in UI."""
        self._click_pos = (x, y)
        self._click_frames = 8  # Show click for 8 frames

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape

        # Brief click marker — small yellow + (not green; avoids "flare" vs checkpoint dots)
        if self._click_pos and self._click_frames > 0:
            cx, cy = self._click_pos
            if 0 <= cx < w and 0 <= cy < h:
                hit = 11  # yellow
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

        # Level indicator - show current level (1-5)
        frame[2, 2] = 9  # Blue = level marker
        # Use 3 cells to show level number
        level_colors = [9, 10, 14, 11, 15]  # Blue, Light Blue, Green, Yellow, Purple
        frame[2, 3] = level_colors[(self._level - 1) % 5]

        # Score - yellow dot, size indicates score
        if self._score > 0:
            frame[2, w - 3] = 11  # Yellow = score
            if self._score > 3:
                frame[2, w - 4] = 11
            if self._score > 6:
                frame[2, w - 5] = 11

        # Lives - red dots on right side (5 = full)
        for i in range(5):
            if i < self._lives:
                frame[h - 3, w - 4 - i] = 8  # Red = alive
            else:
                frame[h - 3, w - 4 - i] = 3  # Gray = lost

        # Checkpoint progress - show as dots that change color:
        # Each checkpoint needs 3 mole appearances
        # Green = whacked, Red = missed/escaped
        if self._checkpoint_total > 0:
            for i in range(3):  # 3 appearances per checkpoint
                if i < self._checkpoint_score:
                    frame[h - 3, 2 + i] = 14  # Green = whacked
                elif i < self._mole_appeared % 3 or self._checkpoint_score == 0:
                    frame[h - 3, 2 + i] = 8  # Red = waiting/missed
                else:
                    frame[h - 3, 2 + i] = 3  # Gray = not yet

        return frame


sprites = {
    "hole": Sprite(
        pixels=[
            [4, 4, 4],
            [4, 5, 4],
            [4, 4, 4],
        ],
        name="hole",
        visible=True,
        collidable=False,
        tags=["hole"],
    ),
    "mole": Sprite(
        pixels=[
            [5, 12, 12, 12, 5],
            [12, 12, 12, 12, 12],
            [12, 12, 8, 12, 12],
            [12, 12, 12, 12, 12],
            [5, 12, 12, 12, 5],
        ],
        name="mole",
        visible=True,
        collidable=False,
        tags=["mole"],
    ),
    "whacked": Sprite(
        pixels=[
            [11, 11, 11],
            [11, 8, 11],
            [11, 11, 11],
        ],
        name="whacked",
        visible=True,
        collidable=False,
        tags=["whacked"],
    ),
    "decoy": Sprite(
        pixels=[
            [5, 2, 2, 2, 5],
            [2, 2, 2, 2, 2],
            [2, 2, 8, 2, 2],
            [2, 2, 2, 2, 2],
            [5, 2, 2, 2, 5],
        ],
        name="decoy",
        visible=True,
        collidable=False,
        tags=["mole", "mole_decoy"],
    ),
}


def create_level(difficulty: int):
    # Generate holes based on level: 3x3, 4x4, 5x5, 6x6, 7x7
    grid_size = 2 + difficulty  # Level 1=3, Level 2=4, etc.

    # Moles are 5×5 and share the hole's top-left; keep y+4,x+4 ≤ 31 on 32×32 grid.
    margin = 2
    max_tl = 32 - 5  # 27 — top-left must leave room for mole footprint
    usable = max_tl - margin
    step = usable / (grid_size - 1) if grid_size > 1 else 0.0

    hole_positions = []
    for row in range(grid_size):
        for col in range(grid_size):
            x = int(round(margin + col * step))
            y = int(round(margin + row * step))
            x = max(margin, min(max_tl, x))
            y = max(margin, min(max_tl, y))
            hole_positions.append((x, y))

    level_sprites = []
    for x, y in hole_positions:
        level_sprites.append(sprites["hole"].clone().set_position(x, y))

    return Level(
        sprites=level_sprites,
        grid_size=(32, 32),
        data={
            "difficulty": difficulty,
            "mole_display_time": max(2, 6 - difficulty),
            "mole_interval": max(3, 9 - difficulty),
            "moles_per_checkpoint": 3,
        },
    )


levels = [create_level(i) for i in range(1, 6)]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Wm03(ARCBaseGame):
    """Lane moles plus gray decoys in wrong lanes — whacking a decoy costs a life."""

    def __init__(self) -> None:
        self._ui = Wm03UI(5, 0, 0, 3)
        self._ui._level = 1  # Initialize level
        super().__init__(
            "wm03",
            levels,
            Camera(0, 0, 64, 64, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [6],
        )

    def on_set_level(self, level: Level) -> None:
        self._holes = self.current_level.get_sprites_by_tag("hole")
        self._moles = []
        self._lives = 5
        self._score = 0
        self._checkpoint_count = 0
        self._checkpoint_score = 0
        self._mole_appeared = 0
        self._current_mole = None
        self._mole_timer = 0
        self._action_count = 0
        self._difficulty = self.current_level.get_data("difficulty")
        self._mole_display_time = self.current_level.get_data("mole_display_time")
        self._mole_interval = self.current_level.get_data("mole_interval")
        self._moles_per_checkpoint = self.current_level.get_data("moles_per_checkpoint")
        self._lane_cursor = 0
        self._n_lanes = 4
        self._update_ui()

    @staticmethod
    def _lane_of_hole(hole) -> int:
        return min(3, max(0, int(hole.x) // 8))

    def _spawn_mole(self):
        if self._current_mole is None and self._holes:
            available_holes = [h for h in self._holes if h not in self._moles]
            if available_holes:
                want = self._lane_cursor % self._n_lanes
                self._lane_cursor += 1
                lane_holes = [h for h in available_holes if self._lane_of_hole(h) == want]
                pool = lane_holes if lane_holes else available_holes
                hole = random.choice(pool)
                wrong = [h for h in available_holes if self._lane_of_hole(h) != want]
                if wrong and random.random() < 0.35:
                    dh = random.choice(wrong)
                    mole = sprites["decoy"].clone().set_position(dh.x, dh.y)
                else:
                    mole = sprites["mole"].clone().set_position(hole.x, hole.y)
                self.current_level.add_sprite(mole)
                self._moles.append(mole)
                self._current_mole = mole
                self._mole_appeared += 1
                self._mole_timer = 0

    def get_mole_position(self):
        """Returns (grid_x, grid_y) of current mole, or None"""
        if self._current_mole:
            return (self._current_mole.x, self._current_mole.y)
        return None

    def get_mole_timer(self):
        """Returns how many frames the mole has been visible"""
        return self._mole_timer

    @property
    def game(self):
        """Public access to game instance for demo/testing"""
        return self

    def _hide_mole(self):
        if self._current_mole:
            self.current_level.remove_sprite(self._current_mole)
            if self._current_mole in self._moles:
                self._moles.remove(self._current_mole)
            # Mole escaped - if no whack this appearance, lose a life
            self._moles.append(self._current_mole)  # Mark as escaped
            self._current_mole = None

    def _check_checkpoint(self):
        # After every 3 mole appearances, check if player passed
        if (
            self._mole_appeared > 0
            and self._mole_appeared % self._moles_per_checkpoint == 0
        ):
            # Following ls20 pattern: check pass condition first, then fail condition
            # Need ≥2 whacks out of 3 to pass checkpoint
            if self._checkpoint_score >= 2:
                # Passed checkpoint
                self._checkpoint_count += 1
                if self._checkpoint_count >= 2:
                    # 2 checkpoints = advance to next level
                    self.next_level()
                    self._checkpoint_count = 0
            else:
                # Failed checkpoint - lose a life (ls20 pattern)
                self._lives -= 1
                if self._lives <= 0:
                    self.lose()
            # Reset for next checkpoint
            self._checkpoint_score = 0
        return False

    def _update_ui(self):
        level_num = self._checkpoint_count + 1
        self._ui.update(
            self._lives,
            self._score,
            self._checkpoint_score,
            self._moles_per_checkpoint,
            level_num,
        )
        # Also update mole_appeared for checkpoint display
        self._ui._mole_appeared = self._mole_appeared

    def step(self) -> None:
        self._action_count += 1

        # Spawn mole periodically
        if self._current_mole is None:
            if self._action_count % self._mole_interval == 0:
                self._spawn_mole()
        else:
            self._mole_timer += 1
            if self._mole_timer >= self._mole_display_time:
                # Mole disappeared without being whacked - no penalty, just missed opportunity
                self._hide_mole()
                self._check_checkpoint()
                self._update_ui()

        # Handle ACTION6 - click to whack
        if self.action.id == GameAction.ACTION6:
            x = self.action.data.get("x", 0)
            y = self.action.data.get("y", 0)

            # Show click cursor in UI
            self._ui.set_click(x, y)

            # Convert display coords to grid coords
            grid_x = x // 2
            grid_y = y // 2
            click_lane = min(3, max(0, grid_x // 8))

            # Find mole AT or NEAR the clicked position (radius 2 tolerance)
            clicked_mole = None
            for s in self.current_level._sprites:
                if not s:
                    continue
                if "mole" not in s.tags and "mole_decoy" not in s.tags:
                    continue
                if abs(s.x - grid_x) <= 2 and abs(s.y - grid_y) <= 2:
                    clicked_mole = s
                    break

            if clicked_mole is not None and "mole_decoy" in clicked_mole.tags:
                self.current_level.remove_sprite(clicked_mole)
                if clicked_mole in self._moles:
                    self._moles.remove(clicked_mole)
                self._current_mole = None
                self._lives -= 1
                if self._lives <= 0:
                    self.lose()
                self._update_ui()
                self.complete_action()
                return

            if clicked_mole is None:
                if self._current_mole is not None:
                    mole_lane = self._lane_of_hole(self._current_mole)
                    if click_lane != mole_lane:
                        self._lives -= 1
                        if self._lives <= 0:
                            self.lose()
            else:
                # Whacked the mole!
                self.current_level.remove_sprite(clicked_mole)
                if clicked_mole in self._moles:
                    self._moles.remove(clicked_mole)

                whacked = (
                    sprites["whacked"]
                    .clone()
                    .set_position(clicked_mole.x, clicked_mole.y)
                )
                self.current_level.add_sprite(whacked)

                self._score += 1
                self._checkpoint_score += 1

                # Remove whacked marker after short delay
                self._current_mole = None

                self._check_checkpoint()
            # Clicked on empty hole - no penalty

            self._update_ui()

        self.complete_action()
