"""One-push crate: each crate may be pushed at most once; a second push loses."""

from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Op01UI(RenderableUserDisplay):
    def __init__(self, ok: bool) -> None:
        self._ok = ok

    def update(self, ok: bool) -> None:
        self._ok = ok

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        c = 14 if self._ok else 15
        for dy in range(3):
            for dx in range(3):
                frame[h - 3 + dy, w - 3 + dx] = c
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
    "target": Sprite(
        pixels=[[11]],
        name="target",
        visible=True,
        collidable=False,
        tags=["target"],
    ),
    "wall": Sprite(
        pixels=[[3]],
        name="wall",
        visible=True,
        collidable=True,
        tags=["wall"],
    ),
}


def mk(
    grid: tuple[int, int],
    player: tuple[int, int],
    block: tuple[int, int],
    target: tuple[int, int],
    walls: list[tuple[int, int]],
    d: int,
) -> Level:
    sl: list[Sprite] = [
        sprites["player"].clone().set_position(*player),
        sprites["block"].clone().set_position(*block),
        sprites["target"].clone().set_position(*target),
    ]
    for wx, wy in walls:
        sl.append(sprites["wall"].clone().set_position(wx, wy))
    return Level(sprites=sl, grid_size=grid, data={"difficulty": d, "step_limit": 80})


levels = [
    mk((8, 8), (1, 1), (4, 2), (5, 2), [], 1),
    mk((8, 8), (1, 3), (5, 3), (6, 3), [(4, y) for y in range(8) if y != 3], 2),
    mk((10, 10), (2, 4), (6, 4), (7, 4), [(5, y) for y in range(10) if y not in (4, 5)], 3),
    mk((8, 8), (0, 2), (4, 2), (5, 2), [(4, y) for y in range(8) if y != 2], 4),
    mk((8, 8), (1, 1), (5, 4), (6, 4), [], 5),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Op01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Op01UI(False)
        super().__init__(
            "op01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._blocks = list(self.current_level.get_sprites_by_tag("block"))
        self._targets = self.current_level.get_sprites_by_tag("target")
        self._step_limit = int(level.get_data("step_limit") or 80)
        self._steps = 0
        self._pushed: set[int] = set()
        self._sync_ui()

    def _block_on_target(self) -> bool:
        for b in self._blocks:
            for t in self._targets:
                if b.x == t.x and b.y == t.y:
                    return True
        return False

    def _sync_ui(self) -> None:
        self._ui.update(self._block_on_target())

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

        new_x = self._player.x + dx
        new_y = self._player.y + dy
        gw, gh = self.current_level.grid_size
        if not (0 <= new_x < gw and 0 <= new_y < gh):
            self.complete_action()
            return

        sprite = self.current_level.get_sprite_at(new_x, new_y, ignore_collidable=True)

        if sprite and "wall" in sprite.tags:
            self.complete_action()
            return

        if sprite and "block" in sprite.tags:
            bid = id(sprite)
            if bid in self._pushed:
                self.lose()
                self.complete_action()
                return
            bx, by = new_x + dx, new_y + dy
            if not (0 <= bx < gw and 0 <= by < gh):
                self.complete_action()
                return
            behind = self.current_level.get_sprite_at(bx, by, ignore_collidable=True)
            if behind and ("block" in behind.tags or "wall" in behind.tags):
                self.complete_action()
                return
            self._pushed.add(bid)
            sprite.set_position(bx, by)
            self._player.set_position(new_x, new_y)
        elif not sprite or not sprite.is_collidable:
            self._player.set_position(new_x, new_y)

        self._steps += 1
        self._sync_ui()

        if self._block_on_target():
            self.next_level()
        elif self._steps >= self._step_limit:
            self.lose()

        self.complete_action()
