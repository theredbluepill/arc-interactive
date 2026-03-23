"""Number fuse: pick up numbered tokens in strictly descending order (highest first); wrong order loses."""

from arcengine import (
    ARCBaseGame,
    Camera,
    GameAction,
    Level,
    RenderableUserDisplay,
    Sprite,
)


# Distinct token colors (match token_sprite) so HUD dots map to board tokens.
TOKEN_COLOR = {3: 11, 2: 12, 1: 10}


class Nu01UI(RenderableUserDisplay):
    def __init__(self, need: int) -> None:
        self._need = need

    def update(self, need: int) -> None:
        self._need = need

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for i in range(3):
            val = 3 - i
            if self._need == 0:
                c = 14
            elif val == self._need:
                c = TOKEN_COLOR[val]
            elif val > self._need:
                c = 3
            else:
                c = 2
            frame[h - 2, 2 + i] = c
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
}


def token_sprite(n: int) -> Sprite:
    c = TOKEN_COLOR.get(n, 10)
    return Sprite(
        pixels=[[c]],
        name=f"tok{n}",
        visible=True,
        collidable=False,
        tags=["token", f"n{n}"],
    )


def mk(sl, d: int):
    return Level(sprites=sl, grid_size=(10, 10), data={"difficulty": d})


levels = [
    mk(
        [
            sprites["player"].clone().set_position(1, 5),
            token_sprite(3).clone().set_position(3, 5),
            token_sprite(2).clone().set_position(5, 5),
            token_sprite(1).clone().set_position(7, 5),
            sprites["goal"].clone().set_position(9, 5),
        ],
        1,
    ),
    mk(
        [
            sprites["player"].clone().set_position(2, 2),
            token_sprite(1).clone().set_position(4, 2),
            token_sprite(3).clone().set_position(6, 4),
            token_sprite(2).clone().set_position(3, 6),
            sprites["goal"].clone().set_position(8, 8),
        ],
        2,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            token_sprite(3).clone().set_position(2, 1),
            token_sprite(2).clone().set_position(4, 3),
            token_sprite(1).clone().set_position(6, 5),
            sprites["goal"].clone().set_position(9, 9),
        ],
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(5, 5),
            token_sprite(3).clone().set_position(5, 2),
            token_sprite(2).clone().set_position(8, 5),
            token_sprite(1).clone().set_position(5, 8),
            sprites["goal"].clone().set_position(1, 5),
        ],
        4,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 1),
            token_sprite(3).clone().set_position(7, 1),
            token_sprite(2).clone().set_position(1, 7),
            token_sprite(1).clone().set_position(7, 7),
            sprites["goal"].clone().set_position(4, 4),
        ]
        + [sprites["wall"].clone().set_position(4, y) for y in (0, 1, 8, 9)],
        5,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


def _token_value(sp: Sprite) -> int | None:
    for t in sp.tags:
        if t.startswith("n") and t[1:].isdigit():
            return int(t[1:])
    return None


class Nu01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Nu01UI(3)
        super().__init__(
            "nu01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._goal = self.current_level.get_sprites_by_tag("goal")[0]
        self._tokens = list(self.current_level.get_sprites_by_tag("token"))
        self._next_val = 3
        self._ui.update(self._next_val)

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

        if sp and "token" in sp.tags:
            v = _token_value(sp)
            if v is None or v != self._next_val:
                self.lose()
                self.complete_action()
                return
            self.current_level.remove_sprite(sp)
            if sp in self._tokens:
                self._tokens.remove(sp)
            self._next_val -= 1
            self._ui.update(self._next_val)

        self._player.set_position(nx, ny)

        if self._next_val == 0 and self._player.x == self._goal.x and self._player.y == self._goal.y:
            self.next_level()

        self.complete_action()
