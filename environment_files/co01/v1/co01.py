import random
from arcengine import (
    ActionInput,
    ARCBaseGame,
    Camera,
    GameAction,
    Level,
    Sprite,
)

# Sprite definitions
sprites = {
    "player": Sprite(
        pixels=[[9]],  # Blue player
        name="player",
        visible=True,
        collidable=True,
        tags=["player"],
    ),
    "target": Sprite(
        pixels=[[4]],  # Yellow target
        name="target",
        visible=True,
        collidable=False,
        tags=["target"],
    ),
    "wall": Sprite(
        pixels=[[5]],  # Gray wall
        name="wall",
        visible=True,
        collidable=True,
        tags=["wall"],
    ),
    "hazard": Sprite(
        pixels=[[2]],  # Red hazard
        name="hazard",
        visible=True,
        collidable=True,
        tags=["hazard"],
    ),
}

# Base level structure - content generated procedurally
levels = [
    Level(sprites=[], grid_size=(8, 8), data={"difficulty": 1}),
    Level(sprites=[], grid_size=(16, 16), data={"difficulty": 2}),
    Level(sprites=[], grid_size=(24, 24), data={"difficulty": 3}),
]

BACKGROUND_COLOR = 0
PADDING_COLOR = 4


class Co01(ARCBaseGame):
    """Meta-learning collection game with PCG.

    Features:
    - State randomization: Grid size, entity placement
    - Action randomization: Movement directions scrambled per episode
    - Sparse rewards: Checkpoints for reaching targets
    - Physics: Collision detection, collection mechanics
    """

    def __init__(self, seed: int = 0) -> None:
        self._rng = random.Random(seed)
        self._player_pos = (0, 0)
        self._player_sprite = None
        self._targets = []
        self._checkpoints = []
        self._checkpoint_rewards = []
        self._steps_survived = 0

        # Scramble action mapping for this episode
        self._scramble_actions()

        # Create camera
        camera = Camera(
            background=BACKGROUND_COLOR,
            letter_box=PADDING_COLOR,
            width=8,
            height=8,
        )

        super().__init__(
            game_id="co01",
            levels=levels,
            camera=camera,
        )

    def _scramble_actions(self):
        """Randomize action meanings for meta-learning.

        Each episode, the 4 movement directions are scrambled.
        The agent must explore to discover the mapping.
        """
        directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]  # up, down, left, right
        self._rng.shuffle(directions)

        self._action_map = {
            GameAction.ACTION1: directions[0],  # Randomly mapped
            GameAction.ACTION2: directions[1],  # Randomly mapped
            GameAction.ACTION3: directions[2],  # Randomly mapped
            GameAction.ACTION4: directions[3],  # Randomly mapped
        }

    def on_set_level(self, level: Level) -> None:
        """Generate procedural content when level loads."""
        self._generate_level_content()

    def _generate_level_content(self):
        """Generate randomized level content.

        State Randomization:
        - Random entity positions
        - Random target/hazard counts
        - Random checkpoint locations
        """
        difficulty = self.current_level._data.get("difficulty", 1)
        grid_w, grid_h = self.current_level.grid_size

        # Clear existing sprites
        self.current_level._sprites = []

        # Place player at random position
        self._player_pos = (
            self._rng.randint(0, grid_w - 1),
            self._rng.randint(0, grid_h - 1),
        )
        self._player_sprite = sprites["player"].clone().set_position(*self._player_pos)
        self.current_level.add_sprite(self._player_sprite)

        # Generate targets (3-5 based on difficulty)
        target_count = min(3 + difficulty, 5)
        self._targets = []
        for _ in range(target_count):
            pos = self._random_empty_position(grid_w, grid_h)
            if pos:
                target = sprites["target"].clone().set_position(*pos)
                self.current_level.add_sprite(target)
                self._targets.append(pos)

        # Generate walls (obstacles)
        wall_count = self._rng.randint(2, 4 + difficulty * 2)
        for _ in range(wall_count):
            pos = self._random_empty_position(grid_w, grid_h)
            if pos:
                wall = sprites["wall"].clone().set_position(*pos)
                self.current_level.add_sprite(wall)

        # Generate hazards (for survival checkpoints)
        hazard_count = self._rng.randint(1, 1 + difficulty)
        for _ in range(hazard_count):
            pos = self._random_empty_position(grid_w, grid_h)
            if pos:
                hazard = sprites["hazard"].clone().set_position(*pos)
                self.current_level.add_sprite(hazard)

        # Setup sparse checkpoints
        self._checkpoints = []
        self._checkpoint_rewards = []

        # Spatial checkpoint: reach a specific target
        if self._targets:
            self._checkpoints.append({"type": "spatial", "pos": self._targets[0]})

        # Collection checkpoint: collect half the targets
        self._checkpoints.append({"type": "collection", "count": target_count // 2 + 1})

        # Survival checkpoint: avoid hazards for N steps
        self._checkpoints.append({"type": "survival", "steps": 10 + difficulty * 5})

        self._steps_survived = 0

    def _random_empty_position(self, grid_w, grid_h):
        """Find a random empty position on the grid."""
        max_attempts = 100
        for _ in range(max_attempts):
            x = self._rng.randint(0, grid_w - 1)
            y = self._rng.randint(0, grid_h - 1)
            if not self.current_level.get_sprite_at(x, y):
                return (x, y)
        return None

    def step(self) -> None:
        """Process game logic with scrambled action mapping."""
        action = self.action

        # Handle movement actions
        if action.id in self._action_map:
            dx, dy = self._action_map[action.id]
            new_x = self._player_pos[0] + dx
            new_y = self._player_pos[1] + dy

            # Check bounds
            grid_w, grid_h = self.current_level.grid_size
            if 0 <= new_x < grid_w and 0 <= new_y < grid_h:
                # Check collision
                sprite = self.current_level.get_sprite_at(new_x, new_y)

                if not sprite or not sprite.collidable:
                    # Move player
                    self._player_pos = (new_x, new_y)
                    if self._player_sprite:
                        self._player_sprite.set_position(new_x, new_y)
                elif sprite and "target" in sprite.tags:
                    # Collect target
                    self.current_level.remove_sprite(sprite)
                    self._targets = [t for t in self._targets if t != (new_x, new_y)]
                    # Move to target position
                    self._player_pos = (new_x, new_y)
                    if self._player_sprite:
                        self._player_sprite.set_position(new_x, new_y)

        # Update survival counter
        self._steps_survived += 1

        # Check checkpoints (sparse rewards)
        self._evaluate_checkpoints()

        # Check win condition
        if self._check_win():
            self.next_level()

        self.complete_action()

    def _evaluate_checkpoints(self):
        """Check and reward milestone achievements (sparse rewards)."""
        for i, checkpoint in enumerate(self._checkpoints):
            if i in self._checkpoint_rewards:
                continue  # Already rewarded

            achieved = False
            if checkpoint["type"] == "spatial":
                if self._player_pos == checkpoint["pos"]:
                    achieved = True
            elif checkpoint["type"] == "collection":
                targets_remaining = len(self._targets)
                targets_total = checkpoint["count"]
                if targets_remaining <= targets_total:
                    achieved = True
            elif checkpoint["type"] == "survival":
                if self._steps_survived >= checkpoint["steps"]:
                    achieved = True

            if achieved:
                self._checkpoint_rewards.append(i)
                # In actual DreamerV3 integration, this would emit reward

    def _check_win(self) -> bool:
        """Check if all targets have been collected."""
        return len(self._targets) == 0

    def reset(self, seed=None):
        """Reset episode with new scrambled actions."""
        if seed is not None:
            self._rng = random.Random(seed)
        self._scramble_actions()
        return super().reset(seed=seed)
