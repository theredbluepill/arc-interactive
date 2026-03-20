"""Firebreak: fire spreads orthogonally each step; ACTION5 places one permanent blue break cell that blocks spread into that tile."""

from arcengine import (
    ARCBaseGame,
    Camera,
    GameAction,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Fi01UI(RenderableUserDisplay):
    def __init__(self, breaks: int) -> None:
        self._breaks = breaks

    def update(self, breaks: int) -> None:
        self._breaks = breaks

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for i in range(min(self._breaks, 8)):
            frame[h - 2, 1 + i] = 10
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
    "fire": Sprite(
        pixels=[[8]],
        name="fire",
        visible=True,
        collidable=True,
        tags=["fire"],
    ),
    "break_tile": Sprite(
        pixels=[[10]],
        name="break_tile",
        visible=True,
        collidable=False,
        tags=["break_tile"],
    ),
}


def mk(sl, d: int, breaks: int):
    return Level(
        sprites=sl,
        grid_size=(14, 14),
        data={"difficulty": d, "break_budget": breaks},
    )


levels = [
    mk(
        [
            sprites["player"].clone().set_position(1, 7),
            sprites["goal"].clone().set_position(12, 7),
            sprites["fire"].clone().set_position(7, 7),
        ],
        1,
        2,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["goal"].clone().set_position(13, 13),
            sprites["fire"].clone().set_position(6, 6),
            sprites["fire"].clone().set_position(7, 6),
        ],
        2,
        2,
    ),
    mk(
        [
            sprites["player"].clone().set_position(2, 2),
            sprites["goal"].clone().set_position(11, 11),
            sprites["fire"].clone().set_position(7, 2),
            sprites["fire"].clone().set_position(2, 7),
        ],
        3,
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 13),
            sprites["goal"].clone().set_position(12, 0),
            sprites["fire"].clone().set_position(7, 7),
        ]
        + [sprites["wall"].clone().set_position(7, y) for y in range(14) if y != 7],
        4,
        2,
    ),
    mk(
        [
            sprites["player"].clone().set_position(7, 13),
            sprites["goal"].clone().set_position(7, 0),
            sprites["fire"].clone().set_position(7, 10),
            sprites["fire"].clone().set_position(6, 9),
            sprites["fire"].clone().set_position(8, 9),
        ],
        5,
        3,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Fi01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Fi01UI(0)
        super().__init__(
            "fi01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 5],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._goal = self.current_level.get_sprites_by_tag("goal")[0]
        self._left = int(self.current_level.get_data("break_budget") or 2)
        self._ui.update(self._left)

    def _spread(self) -> None:
        fires = list(self.current_level.get_sprites_by_tag("fire"))
        gw, gh = self.current_level.grid_size
        add = []
        for f in fires:
            for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                nx, ny = f.x + dx, f.y + dy
                if not (0 <= nx < gw and 0 <= ny < gh):
                    continue
                sp = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
                if sp and (
                    "wall" in sp.tags
                    or "fire" in sp.tags
                    or "break_tile" in sp.tags
                    or "goal" in sp.tags
                ):
                    continue
                add.append((nx, ny))
        for nx, ny in add:
            self.current_level.add_sprite(sprites["fire"].clone().set_position(nx, ny))

    def step(self) -> None:
        self._spread()
        here = self.current_level.get_sprite_at(
            self._player.x, self._player.y, ignore_collidable=True
        )
        if here and "fire" in here.tags:
            self.lose()
            self.complete_action()
            return

        if self.action.id == GameAction.ACTION5:
            if self._left <= 0:
                self.complete_action()
                return
            px, py = self._player.x, self._player.y
            placed = False
            for dx, dy in ((0, 0), (0, -1), (0, 1), (-1, 0), (1, 0)):
                nx, ny = px + dx, py + dy
                sp = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
                if sp and (
                    "wall" in sp.tags
                    or "fire" in sp.tags
                    or "break_tile" in sp.tags
                    or "goal" in sp.tags
                ):
                    continue
                self.current_level.add_sprite(
                    sprites["break_tile"].clone().set_position(nx, ny)
                )
                self._left -= 1
                placed = True
                break
            if placed:
                self._ui.update(self._left)
            self.complete_action()
            return

        dx = dy = 0
        if self.action.id == GameAction.ACTION1:
            dy = -1
        elif self.action.id == GameAction.ACTION2:
            dy = 1
        elif self.action.id == GameAction.ACTION3:
            dx = -1
        elif self.action.id == GameAction.ACTION4:
            dx = 1
        else:
            self.complete_action()
            return

        nx = self._player.x + dx
        ny = self._player.y + dy
        gw, gh = self.current_level.grid_size
        if 0 <= nx < gw and 0 <= ny < gh:
            sp = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
            if sp and "fire" in sp.tags:
                self.lose()
                self.complete_action()
                return
            if not sp or not sp.is_collidable:
                self._player.set_position(nx, ny)

        if self._player.x == self._goal.x and self._player.y == self._goal.y:
            self.next_level()

        self.complete_action()
