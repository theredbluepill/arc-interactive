"""Weight plate: orthogonal weight from you (1) and crates (2) must reach W on the yellow plate to open the win tile."""

from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Wp01UI(RenderableUserDisplay):
    def __init__(self, n_levels: int) -> None:
        self._ok = False
        self._sum = 0
        self._need = 3
        self._n_levels = n_levels
        self._li = 0

    def update(
        self,
        ok: bool,
        weight_sum: int,
        need: int,
        level_index: int | None = None,
    ) -> None:
        self._ok = ok
        self._sum = weight_sum
        self._need = need
        if level_index is not None:
            self._li = level_index

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for i in range(min(self._n_levels, 14)):
            cx = 1 + i * 2
            if cx >= w:
                break
            c = 14 if i < self._li else (11 if i == self._li else 3)
            frame[0, cx] = c
        frame[h - 2, 2] = 14 if self._ok else 11
        for i in range(min(self._sum, 10)):
            frame[h - 3, 1 + i] = 10
        for i in range(min(self._need, 10)):
            frame[h - 4, 1 + i] = 11
        return frame


sprites = {
    "player": Sprite(
        pixels=[[9]],
        name="player",
        visible=True,
        collidable=True,
        tags=["player"],
    ),
    "block": Sprite(
        pixels=[[15]],
        name="block",
        visible=True,
        collidable=True,
        tags=["block"],
    ),
    "plate": Sprite(
        pixels=[[11]],
        name="plate",
        visible=True,
        collidable=False,
        tags=["plate"],
    ),
    "goal": Sprite(
        pixels=[[14]],
        name="goal",
        visible=True,
        collidable=True,
        tags=["goal", "locked"],
    ),
    "wall": Sprite(
        pixels=[[3]],
        name="wall",
        visible=True,
        collidable=True,
        tags=["wall"],
    ),
}


def mk(sl: list, d: int, need: int) -> Level:
    return Level(sprites=sl, grid_size=(10, 10), data={"difficulty": d, "weight_need": need})


levels = [
    mk(
        [
            sprites["player"].clone().set_position(5, 4),
            sprites["block"].clone().set_position(5, 6),
            sprites["plate"].clone().set_position(5, 5),
            sprites["goal"].clone().set_position(8, 5),
        ],
        1,
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 5),
            sprites["block"].clone().set_position(3, 5),
            sprites["block"].clone().set_position(7, 5),
            sprites["plate"].clone().set_position(5, 5),
            sprites["goal"].clone().set_position(9, 5),
        ],
        2,
        4,
    ),
    mk(
        [
            sprites["player"].clone().set_position(2, 2),
            sprites["block"].clone().set_position(4, 5),
            sprites["plate"].clone().set_position(5, 5),
            sprites["goal"].clone().set_position(8, 8),
        ],
        3,
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(5, 2),
            sprites["block"].clone().set_position(5, 4),
            sprites["plate"].clone().set_position(5, 5),
            sprites["goal"].clone().set_position(5, 8),
        ],
        4,
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["block"].clone().set_position(3, 5),
            sprites["block"].clone().set_position(7, 5),
            sprites["plate"].clone().set_position(5, 5),
            sprites["goal"].clone().set_position(8, 8),
        ],
        5,
        4,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Wp01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Wp01UI(len(levels))
        super().__init__(
            "wp01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._goal = self.current_level.get_sprites_by_tag("goal")[0]
        self._plate = self.current_level.get_sprites_by_tag("plate")[0]
        self._need = int(level.get_data("weight_need") or 3)
        self._blocks = list(self.current_level.get_sprites_by_tag("block"))
        self._sync_goal()

    def _weight_on_plate(self) -> int:
        px, py = self._plate.x, self._plate.y
        w = 0
        for dx, dy in ((0, 0), (0, -1), (0, 1), (-1, 0), (1, 0)):
            cx, cy = px + dx, py + dy
            if self._player.x == cx and self._player.y == cy:
                w += 1
            for b in self._blocks:
                if b.x == cx and b.y == cy:
                    w += 2
                    break
        return w

    def _sync_goal(self) -> None:
        wsum = self._weight_on_plate()
        ok = wsum >= self._need
        self._goal.set_collidable(not ok)
        self._ui.update(ok, wsum, self._need, self.level_index)

    def step(self) -> None:
        dx = dy = 0
        if self.action.id.value == 1:
            dy = -1
        elif self.action.id.value == 2:
            dy = 1
        elif self.action.id.value == 3:
            dx = -1
        elif self.action.id.value == 4:
            dx = 1

        if dx == 0 and dy == 0:
            self.complete_action()
            return

        nx = self._player.x + dx
        ny = self._player.y + dy
        gw, gh = self.current_level.grid_size
        if not (0 <= nx < gw and 0 <= ny < gh):
            self.complete_action()
            return

        sp = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
        if sp and "wall" in sp.tags:
            self.complete_action()
            return
        if sp and "goal" in sp.tags and sp.is_collidable:
            self.complete_action()
            return

        if sp and "block" in sp.tags:
            bx, by = nx + dx, ny + dy
            if not (0 <= bx < gw and 0 <= by < gh):
                self.complete_action()
                return
            behind = self.current_level.get_sprite_at(bx, by, ignore_collidable=True)
            if behind and ("block" in behind.tags or "wall" in behind.tags):
                self.complete_action()
                return
            if behind and "goal" in behind.tags and behind.is_collidable:
                self.complete_action()
                return
            sp.set_position(bx, by)
            self._player.set_position(nx, ny)
        elif not sp or not sp.is_collidable:
            self._player.set_position(nx, ny)

        self._sync_goal()

        if self._player.x == self._goal.x and self._player.y == self._goal.y:
            self.next_level()

        self.complete_action()
