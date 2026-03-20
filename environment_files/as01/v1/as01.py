"""Assembly fetch: pick up colored parts (ACTION5) and deliver to workstations in authored order."""

from arcengine import (
    ARCBaseGame,
    Camera,
    GameAction,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class As01UI(RenderableUserDisplay):
    def __init__(self, idx: int, carry: str) -> None:
        self._idx = idx
        self._carry = carry

    def update(self, idx: int, carry: str) -> None:
        self._idx = idx
        self._carry = carry

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        frame[h - 2, 2] = 11 if self._carry == "a" else (7 if self._carry == "b" else 5)
        frame[h - 2, 4] = 3 + min(self._idx, 5)
        return frame


sprites = {
    "player": Sprite(
        pixels=[[9]],
        name="player",
        visible=True,
        collidable=True,
        tags=["player"],
    ),
    "part_a": Sprite(
        pixels=[[11]],
        name="part_a",
        visible=True,
        collidable=False,
        tags=["part", "kind_a"],
    ),
    "part_b": Sprite(
        pixels=[[7]],
        name="part_b",
        visible=True,
        collidable=False,
        tags=["part", "kind_b"],
    ),
    "ws": Sprite(
        pixels=[[2]],
        name="ws",
        visible=True,
        collidable=False,
        tags=["workstation", "ws"],
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


def mk(sl, order: list[str], d: int):
    return Level(
        sprites=sl,
        grid_size=(12, 12),
        data={"difficulty": d, "delivery_order": order},
    )


levels = [
    mk(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["part_a"].clone().set_position(3, 1),
            sprites["ws"].clone().set_position(8, 1),
            sprites["goal"].clone().set_position(10, 10),
        ],
        ["a"],
        1,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["part_a"].clone().set_position(2, 2),
            sprites["part_b"].clone().set_position(2, 4),
            sprites["ws"].clone().set_position(6, 2),
            sprites["ws"].clone().set_position(6, 4),
            sprites["goal"].clone().set_position(11, 11),
        ],
        ["a", "b"],
        2,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 5),
            sprites["part_b"].clone().set_position(1, 1),
            sprites["part_a"].clone().set_position(10, 1),
            sprites["ws"].clone().set_position(5, 5),
            sprites["ws"].clone().set_position(7, 5),
            sprites["goal"].clone().set_position(10, 10),
        ],
        ["b", "a"],
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["part_a"].clone().set_position(4, 0),
            sprites["part_b"].clone().set_position(0, 4),
            sprites["ws"].clone().set_position(8, 2),
            sprites["ws"].clone().set_position(8, 6),
            sprites["goal"].clone().set_position(11, 11),
        ]
        + [sprites["wall"].clone().set_position(6, y) for y in range(12) if y != 5],
        ["a", "b"],
        4,
    ),
    mk(
        [
            sprites["player"].clone().set_position(5, 5),
            sprites["part_a"].clone().set_position(2, 5),
            sprites["part_b"].clone().set_position(8, 5),
            sprites["ws"].clone().set_position(2, 2),
            sprites["ws"].clone().set_position(9, 9),
            sprites["goal"].clone().set_position(5, 10),
        ],
        ["a", "b"],
        5,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class As01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = As01UI(0, "")
        super().__init__(
            "as01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 5],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._order = list(self.current_level.get_data("delivery_order") or ["a"])
        self._ws_queue = list(self.current_level.get_sprites_by_tag("ws"))
        self._next = 0
        self._carry = ""
        self._ui.update(0, "")

    def _need_kind(self) -> str | None:
        if self._next >= len(self._order):
            return None
        return self._order[self._next]

    def step(self) -> None:
        if self.action.id == GameAction.ACTION5:
            px, py = self._player.x, self._player.y
            sp = self.current_level.get_sprite_at(px, py, ignore_collidable=True)
            if self._carry == "":
                if sp and "part" in sp.tags:
                    if "kind_a" in sp.tags:
                        self._carry = "a"
                    else:
                        self._carry = "b"
                    self.current_level.remove_sprite(sp)
            else:
                if sp and "ws" in sp.tags:
                    need = self._need_kind()
                    if need and self._carry == need:
                        self._next += 1
                        self._carry = ""
            self._ui.update(self._next, self._carry)
            self.complete_action()
            return

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
        if 0 <= nx < gw and 0 <= ny < gh:
            t = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
            if not t or not t.is_collidable:
                self._player.set_position(nx, ny)

        gl = self.current_level.get_sprites_by_tag("goal")
        if (
            gl
            and self._player.x == gl[0].x
            and self._player.y == gl[0].y
            and self._next >= len(self._order)
        ):
            self.next_level()

        self.complete_action()
