"""Master key: collect both silver keys so the gold master key appears; gold opens both doors."""

from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Ul03UI(RenderableUserDisplay):
    def __init__(self, a: bool, b: bool, g: bool) -> None:
        self._a = a
        self._b = b
        self._g = g

    def update(self, a: bool, b: bool, g: bool) -> None:
        self._a = a
        self._b = b
        self._g = g

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for dy in range(2):
            for dx in range(2):
                frame[h - 3 + dy, w - 6 + dx] = 11 if self._a else 5
                frame[h - 3 + dy, w - 4 + dx] = 11 if self._b else 5
                frame[h - 3 + dy, w - 2 + dx] = 14 if self._g else 5
        return frame


sprites = {
    "player": Sprite(
        pixels=[[9]],
        name="player",
        visible=True,
        collidable=True,
        tags=["player"],
    ),
    "key_a": Sprite(
        pixels=[[11]],
        name="key_a",
        visible=True,
        collidable=False,
        tags=["key_a"],
    ),
    "key_b": Sprite(
        pixels=[[7]],
        name="key_b",
        visible=True,
        collidable=False,
        tags=["key_b"],
    ),
    "door_a": Sprite(
        pixels=[[3]],
        name="door_a",
        visible=True,
        collidable=True,
        tags=["door_a"],
    ),
    "door_b": Sprite(
        pixels=[[2]],
        name="door_b",
        visible=True,
        collidable=True,
        tags=["door_b"],
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
    "key_gold": Sprite(
        pixels=[[14]],
        name="key_gold",
        visible=False,
        collidable=False,
        tags=["key_gold"],
    ),
}


def mk(sl, gw=10, gh=10, d=1):
    return Level(sprites=sl, grid_size=(gw, gh), data={"difficulty": d})


levels = [
    mk(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["key_a"].clone().set_position(2, 1),
            sprites["door_a"].clone().set_position(4, 1),
            sprites["key_b"].clone().set_position(5, 3),
            sprites["door_b"].clone().set_position(7, 3),
            sprites["goal"].clone().set_position(8, 3),
            sprites["key_gold"].clone().set_position(6, 5),
        ],
        10,
        10,
        1,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["key_a"].clone().set_position(1, 2),
            sprites["door_a"].clone().set_position(3, 2),
            sprites["key_b"].clone().set_position(4, 0),
            sprites["door_b"].clone().set_position(6, 0),
            sprites["goal"].clone().set_position(9, 0),
            sprites["key_gold"].clone().set_position(7, 2),
        ],
        10,
        10,
        2,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["key_a"].clone().set_position(3, 1),
            sprites["door_a"].clone().set_position(5, 1),
            sprites["key_b"].clone().set_position(7, 1),
            sprites["door_b"].clone().set_position(8, 3),
            sprites["goal"].clone().set_position(8, 8),
            sprites["key_gold"].clone().set_position(4, 8),
        ]
        + [sprites["wall"].clone().set_position(6, y) for y in range(10) if y not in (1, 2)],
        10,
        10,
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["key_a"].clone().set_position(0, 3),
            sprites["door_a"].clone().set_position(0, 5),
            sprites["key_b"].clone().set_position(5, 5),
            sprites["door_b"].clone().set_position(8, 5),
            sprites["goal"].clone().set_position(9, 9),
            sprites["key_gold"].clone().set_position(3, 7),
        ],
        10,
        10,
        4,
    ),
    mk(
        [
            sprites["player"].clone().set_position(9, 9),
            sprites["key_a"].clone().set_position(7, 9),
            sprites["door_a"].clone().set_position(5, 9),
            sprites["key_b"].clone().set_position(5, 7),
            sprites["door_b"].clone().set_position(5, 5),
            sprites["goal"].clone().set_position(1, 1),
            sprites["key_gold"].clone().set_position(3, 3),
        ],
        10,
        10,
        5,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Ul03(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Ul03UI(False, False, False)
        super().__init__(
            "ul03",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._has_a = False
        self._has_b = False
        self._has_gold = False
        for kg in self.current_level.get_sprites_by_tag("key_gold"):
            kg.set_visible(False)
        self._ui.update(False, False, False)

    def _maybe_reveal_gold(self) -> None:
        if self._has_a and self._has_b:
            for kg in self.current_level.get_sprites_by_tag("key_gold"):
                kg.set_visible(True)

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
        else:
            self.complete_action()
            return

        nx, ny = self._player.x + dx, self._player.y + dy
        gw, gh = self.current_level.grid_size
        if not (0 <= nx < gw and 0 <= ny < gh):
            self.complete_action()
            return

        sp = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
        if sp and "door_a" in sp.tags:
            if not self._has_gold:
                self.lose()
                self.complete_action()
                return
            self.current_level.remove_sprite(sp)
            self._player.set_position(nx, ny)
            self.complete_action()
            return
        if sp and "door_b" in sp.tags:
            if not self._has_gold:
                self.lose()
                self.complete_action()
                return
            self.current_level.remove_sprite(sp)
            self._player.set_position(nx, ny)
            self.complete_action()
            return
        if sp and "key_a" in sp.tags:
            self.current_level.remove_sprite(sp)
            self._has_a = True
            self._player.set_position(nx, ny)
            self._maybe_reveal_gold()
            self._ui.update(self._has_a, self._has_b, self._has_gold)
        elif sp and "key_b" in sp.tags:
            self.current_level.remove_sprite(sp)
            self._has_b = True
            self._player.set_position(nx, ny)
            self._maybe_reveal_gold()
            self._ui.update(self._has_a, self._has_b, self._has_gold)
        elif sp and "key_gold" in sp.tags and getattr(sp, "is_visible", True):
            self.current_level.remove_sprite(sp)
            self._has_gold = True
            self._player.set_position(nx, ny)
            self._ui.update(self._has_a, self._has_b, self._has_gold)
        elif sp and "wall" in sp.tags:
            self.complete_action()
            return
        elif not sp or not sp.is_collidable:
            self._player.set_position(nx, ny)

        gl = self.current_level.get_sprites_by_tag("goal")
        if gl and self._player.x == gl[0].x and self._player.y == gl[0].y:
            self.next_level()

        self.complete_action()
