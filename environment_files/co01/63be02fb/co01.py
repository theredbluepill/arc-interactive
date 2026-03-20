"""Color gate: step on recolor pads to set the active hue; only doors matching the active color become walk-through."""

from arcengine import (
    ARCBaseGame,
    Camera,
    GameAction,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Co01UI(RenderableUserDisplay):
    def __init__(self, active: int) -> None:
        self._active = active

    def update(self, active: int) -> None:
        self._active = active

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for dy in range(3):
            for dx in range(3):
                frame[h - 3 + dy, 1 + dx] = self._active
        return frame


sprites = {
    "player": Sprite(
        pixels=[[9]],
        name="player",
        visible=True,
        collidable=True,
        tags=["player"],
    ),
    "goal": Sprite(
        pixels=[[14]],
        name="goal",
        visible=True,
        collidable=False,
        tags=["goal"],
    ),
    "wall": Sprite(
        pixels=[[3]],
        name="wall",
        visible=True,
        collidable=True,
        tags=["wall"],
    ),
    "pad_r": Sprite(
        pixels=[[8]],
        name="pad_r",
        visible=True,
        collidable=False,
        tags=["recolor", "c8"],
    ),
    "pad_y": Sprite(
        pixels=[[11]],
        name="pad_y",
        visible=True,
        collidable=False,
        tags=["recolor", "c11"],
    ),
    "door_r": Sprite(
        pixels=[[13]],
        name="door_r",
        visible=True,
        collidable=True,
        tags=["door", "need", "c8"],
    ),
    "door_y": Sprite(
        pixels=[[13]],
        name="door_y",
        visible=True,
        collidable=True,
        tags=["door", "need", "c11"],
    ),
}


def mk(sl, d: int):
    return Level(sprites=sl, grid_size=(10, 10), data={"difficulty": d})


levels = [
    mk(
        [
            sprites["player"].clone().set_position(1, 5),
            sprites["pad_r"].clone().set_position(3, 5),
            sprites["door_r"].clone().set_position(5, 5),
            sprites["goal"].clone().set_position(8, 5),
        ],
        1,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 3),
            sprites["pad_y"].clone().set_position(2, 3),
            sprites["door_y"].clone().set_position(5, 3),
            sprites["pad_r"].clone().set_position(2, 6),
            sprites["door_r"].clone().set_position(5, 6),
            sprites["goal"].clone().set_position(8, 4),
        ],
        2,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 5),
            sprites["pad_r"].clone().set_position(1, 2),
            sprites["door_r"].clone().set_position(4, 2),
            sprites["pad_y"].clone().set_position(1, 8),
            sprites["door_y"].clone().set_position(4, 8),
            sprites["wall"].clone().set_position(4, 4),
            sprites["wall"].clone().set_position(4, 5),
            sprites["wall"].clone().set_position(4, 6),
            sprites["goal"].clone().set_position(8, 5),
        ],
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(2, 2),
            sprites["pad_y"].clone().set_position(2, 4),
            sprites["door_y"].clone().set_position(5, 4),
            sprites["pad_r"].clone().set_position(6, 6),
            sprites["door_r"].clone().set_position(6, 3),
            sprites["goal"].clone().set_position(8, 8),
        ],
        4,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["pad_r"].clone().set_position(3, 1),
            sprites["door_r"].clone().set_position(5, 1),
            sprites["pad_y"].clone().set_position(3, 8),
            sprites["door_y"].clone().set_position(5, 8),
            sprites["goal"].clone().set_position(8, 4),
        ]
        + [sprites["wall"].clone().set_position(5, y) for y in range(2, 8)],
        5,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Co01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Co01UI(11)
        super().__init__(
            "co01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._goal = self.current_level.get_sprites_by_tag("goal")[0]
        self._doors = list(self.current_level.get_sprites_by_tag("door"))
        self._active = 11
        self._sync_doors()
        self._ui.update(self._active)

    def _sync_doors(self) -> None:
        for d in self._doors:
            need = 8 if "c8" in d.tags else 11
            open_ok = need == self._active
            d.set_collidable(not open_ok)

    def step(self) -> None:
        dx = dy = 0
        if self.action.id == GameAction.ACTION1:
            dy = -1
        elif self.action.id == GameAction.ACTION2:
            dy = 1
        elif self.action.id == GameAction.ACTION3:
            dx = -1
        elif self.action.id == GameAction.ACTION4:
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
        if sp and "door" in sp.tags and sp.is_collidable:
            self.complete_action()
            return

        if not sp or not sp.is_collidable:
            self._player.set_position(nx, ny)

        sp2 = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
        if sp2 and "recolor" in sp2.tags:
            if "c8" in sp2.tags:
                self._active = 8
            elif "c11" in sp2.tags:
                self._active = 11
            self._sync_doors()
            self._ui.update(self._active)

        if self._player.x == self._goal.x and self._player.y == self._goal.y:
            self.next_level()

        self.complete_action()
