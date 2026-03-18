from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Sv01UI(RenderableUserDisplay):
    def __init__(self) -> None:
        self._hunger = 100
        self._warmth = 100
        self._level = 1
        self._steps_remaining = 60

    def update(
        self,
        hunger: int,
        warmth: int,
        level: int,
        steps_remaining: int = 60,
    ) -> None:
        self._hunger = hunger
        self._warmth = warmth
        self._level = level
        self._steps_remaining = steps_remaining

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape

        bar_width = max(0, min(20, self._hunger * 20 // 100))
        for i in range(bar_width):
            frame[1, 2 + i] = 3

        bar_width = max(0, min(20, self._warmth * 20 // 100))
        for i in range(bar_width):
            frame[2, 2 + i] = 6

        bar_width = max(0, min(20, self._steps_remaining * 20 // 60))
        for i in range(bar_width):
            frame[3, 2 + i] = 7

        frame[1, w - 3] = 9
        frame[1, w - 4] = 3 + (self._level - 1)

        return frame


sprites = {
    "player": Sprite(
        pixels=[[9]],
        name="player",
        visible=True,
        collidable=True,
        tags=["player"],
        layer=1,
    ),
    "food": Sprite(
        pixels=[[4]],
        name="food",
        visible=True,
        collidable=False,
        tags=["food"],
        layer=0,
    ),
    "warm_zone": Sprite(
        pixels=[[2]],
        name="warm_zone",
        visible=True,
        collidable=False,
        tags=["warm_zone"],
        layer=-1,
    ),
}


WARM_ZONE_CENTERS_PER_LEVEL = {
    1: [(4, 4), (1, 1), (6, 6)],
    2: [(6, 6), (2, 6), (6, 2), (10, 6), (6, 10)],
    3: [(8, 8), (2, 2), (2, 13), (13, 2), (13, 13)],
    4: [(10, 10), (2, 10), (10, 2), (17, 10), (10, 17)],
    5: [
        (12, 12),
        (2, 2),
        (2, 21),
        (21, 2),
        (21, 21),
        (12, 2),
        (12, 21),
        (2, 12),
        (21, 12),
    ],
}

FOOD_POSITIONS_PER_LEVEL = {
    1: [(0, 4), (4, 0), (4, 7), (7, 4), (2, 2), (5, 5)],
    2: [(0, 0), (0, 11), (11, 0), (11, 11), (3, 5), (8, 3), (5, 9)],
    3: [(0, 4), (0, 11), (4, 0), (11, 0), (7, 7), (2, 10), (13, 5), (10, 13)],
    4: [(0, 5), (0, 15), (5, 0), (15, 0), (10, 5), (5, 15), (15, 10), (8, 8)],
    5: [
        (0, 6),
        (0, 18),
        (6, 0),
        (18, 0),
        (12, 6),
        (6, 12),
        (18, 12),
        (12, 18),
        (4, 4),
        (19, 19),
    ],
}

PLAYER_POSITIONS_PER_LEVEL = {
    1: (0, 4),
    2: (0, 0),
    3: (0, 4),
    4: (0, 5),
    5: (0, 6),
}


def expand_warm_zone(center_x, center_y, grid_size, radius=2):
    positions = []
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            if dx * dx + dy * dy <= radius * radius:
                x, y = center_x + dx, center_y + dy
                if 0 <= x < grid_size and 0 <= y < grid_size:
                    positions.append((x, y))
    return positions


def create_level(level_num: int):
    grid_sizes = {1: 8, 2: 12, 3: 16, 4: 20, 5: 24}
    grid_size = grid_sizes[level_num]

    player_pos = PLAYER_POSITIONS_PER_LEVEL[level_num]
    warm_centers = WARM_ZONE_CENTERS_PER_LEVEL[level_num]
    food_pos = FOOD_POSITIONS_PER_LEVEL[level_num]

    level_sprites = [sprites["player"].clone().set_position(*player_pos)]

    for cx, cy in warm_centers:
        for x, y in expand_warm_zone(cx, cy, grid_size, radius=2):
            level_sprites.append(sprites["warm_zone"].clone().set_position(x, y))

    for x, y in food_pos:
        if 0 <= x < grid_size and 0 <= y < grid_size:
            level_sprites.append(sprites["food"].clone().set_position(x, y))

    return Level(
        sprites=level_sprites,
        grid_size=(grid_size, grid_size),
        data={"level": level_num, "survive_steps": 60},
    )


levels = [create_level(i) for i in range(1, 6)]

BACKGROUND_COLOR = 0
PADDING_COLOR = 0


class Sv01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Sv01UI()
        max_grid = 24
        super().__init__(
            "sv01",
            levels,
            Camera(
                0, 0, max_grid, max_grid, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]
            ),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._foods = self.current_level.get_sprites_by_tag("food")
        self._hunger = 100
        self._warmth = 100
        self._steps_survived = 0
        self._level_num = self.current_level.get_data("level")
        self._ui.update(
            self._hunger,
            self._warmth,
            self._level_num,
            60 - self._steps_survived,
        )

    def step(self) -> None:
        dx = 0
        dy = 0

        if self.action.id.value == 1:
            dy = -1
        elif self.action.id.value == 2:
            dy = 1
        elif self.action.id.value == 3:
            dx = -1
        elif self.action.id.value == 4:
            dx = 1

        new_x = self._player.x + dx
        new_y = self._player.y + dy

        grid_w, grid_h = self.current_level.grid_size
        if 0 <= new_x < grid_w and 0 <= new_y < grid_h:
            sprite = self.current_level.get_sprite_at(
                new_x, new_y, ignore_collidable=True
            )

            if sprite and "food" in sprite.tags:
                self._hunger = min(100, self._hunger + 20)
                self.current_level.remove_sprite(sprite)
                self._foods.remove(sprite)
                self._player.set_position(new_x, new_y)
            elif not sprite or not sprite.is_collidable:
                self._player.set_position(new_x, new_y)

        self._decay()
        self._check_survival()

        self.complete_action()

    def _decay(self):
        self._hunger = max(0, self._hunger - 2)

        player_in_warm_zone = False
        for sprite in self.current_level._sprites:
            if sprite and "warm_zone" in sprite.tags:
                if sprite.x == self._player.x and sprite.y == self._player.y:
                    player_in_warm_zone = True
                    break

        if not player_in_warm_zone:
            self._warmth = max(0, self._warmth - 2)

        self._steps_survived += 1
        self._ui.update(
            self._hunger,
            self._warmth,
            self._level_num,
            60 - self._steps_survived,
        )

    def _check_survival(self):
        if self._hunger <= 0 or self._warmth <= 0:
            self.lose()
            return

        if self._steps_survived >= 60:
            self.next_level()
