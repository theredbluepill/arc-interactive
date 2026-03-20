"""Conveyor layer: after each move the player is pushed one more step by the arrow at the **destination** cell (`arrows` in level data)."""

from __future__ import annotations

from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)

BACKGROUND_COLOR = 5
PADDING_COLOR = 4
CAM = 16


class Tc01UI(RenderableUserDisplay):
    def render_interface(self, frame):
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
    "arrow": Sprite(
        pixels=[[10]],
        name="arrow",
        visible=True,
        collidable=False,
        tags=["arrow"],
    ),
}


def mk(
    p: tuple[int, int],
    g: tuple[int, int],
    walls: list[tuple[int, int]],
    arrows: dict[str, tuple[int, int]],
    diff: int,
) -> Level:
    sl = [
        sprites["player"].clone().set_position(*p),
        sprites["goal"].clone().set_position(*g),
    ]
    for wx, wy in walls:
        sl.append(sprites["wall"].clone().set_position(wx, wy))
    for key, (ax, ay) in arrows.items():
        sl.append(sprites["arrow"].clone().set_position(ax, ay))
    ser = {k: list(v) for k, v in arrows.items()}
    return Level(
        sprites=sl,
        grid_size=(CAM, CAM),
        data={"difficulty": diff, "arrows": ser},
    )


def _key(x: int, y: int) -> str:
    return f"{x},{y}"


levels = [
    mk((2, 8), (14, 8), [], {_key(3, 8): (1, 0), _key(5, 8): (0, -1)}, 1),
    mk((1, 1), (14, 14), [(8, y) for y in range(16) if y != 8], {_key(2, 2): (1, 0)}, 2),
    mk((0, 8), (15, 8), [], {_key(x, 8): (1, 0) for x in range(1, 15)}, 3),
    mk((4, 4), (12, 12), [], {_key(5, 4): (0, 1), _key(5, 10): (1, 0)}, 4),
    mk((2, 2), (13, 13), [(6, y) for y in range(16)], {_key(7, 8): (1, 0)}, 5),
]


class Tc01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Tc01UI()
        super().__init__(
            "tc01",
            levels,
            Camera(0, 0, CAM, CAM, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        raw = self.current_level.get_data("arrows") or {}
        self._arrows: dict[str, tuple[int, int]] = {
            k: tuple(int(t) for t in v) for k, v in raw.items()
        }

    def _push_conveyor(self) -> None:
        x, y = self._player.x, self._player.y
        key = _key(x, y)
        if key not in self._arrows:
            return
        dx, dy = self._arrows[key]
        nx, ny = x + dx, y + dy
        gw, gh = self.current_level.grid_size
        if not (0 <= nx < gw and 0 <= ny < gh):
            return
        sp = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
        if sp and "wall" in sp.tags:
            return
        self._player.set_position(nx, ny)

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
        if 0 <= nx < gw and 0 <= ny < gh:
            sp = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
            if not sp or "wall" not in sp.tags:
                self._player.set_position(nx, ny)

        self._push_conveyor()

        gl = self.current_level.get_sprites_by_tag("goal")[0]
        if self._player.x == gl.x and self._player.y == gl.y:
            self.next_level()

        self.complete_action()
