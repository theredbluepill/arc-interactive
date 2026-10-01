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
        self._door_flash = 0

    def update(self, active: int) -> None:
        self._active = active

    def reset(self, active: int) -> None:
        self._active = active
        self._door_flash = 0

    def flash_door_open(self, frames: int = 8) -> None:
        self._door_flash = frames

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for dy in range(3):
            for dx in range(3):
                frame[h - 3 + dy, 1 + dx] = self._active
        if self._door_flash > 0:
            c = 14 if (self._door_flash % 2) == 0 else 0
            for dx in range(4):
                self._plot_corner(frame, h, w, w - 4 + dx, h - 1, c)
            self._door_flash -= 1
        return frame

    @staticmethod
    def _plot_corner(frame, h: int, w: int, x: int, y: int, c: int) -> None:
        if 0 <= x < w and 0 <= y < h:
            frame[y, x] = c


sprites = {
    "player": Sprite(
        pixels=[[9]],
        name="player",
        visible=True,
        collidable=True,
        layer=1,
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


def walls(cells):
    return [sprites["wall"].clone().set_position(x, y) for x, y in cells]


def col(x: int, *gaps: int):
    return [(x, y) for y in range(10) if y not in gaps]


def row(y: int, x0: int, x1: int, *gaps: int):
    return [(x, y) for x in range(x0, x1 + 1) if x not in gaps]


# Every level is sealed by walls so the goal is only reachable through doors,
# which in turn need the matching pad (devtools BFS: no door-free / pad-free win).
levels = [
    # Red pad opens the single red door.
    mk(
        [
            sprites["player"].clone().set_position(1, 5),
            sprites["pad_r"].clone().set_position(3, 5),
            sprites["door_r"].clone().set_position(5, 5),
            sprites["goal"].clone().set_position(8, 5),
        ]
        + walls(col(5, 5)),
        1,
    ),
    # Two chambers in series: red, then yellow (stepping red closes yellow).
    mk(
        [
            sprites["player"].clone().set_position(1, 4),
            sprites["pad_r"].clone().set_position(1, 7),
            sprites["door_r"].clone().set_position(3, 4),
            sprites["pad_y"].clone().set_position(4, 1),
            sprites["door_y"].clone().set_position(6, 6),
            sprites["goal"].clone().set_position(8, 2),
        ]
        + walls(col(3, 4) + col(6, 6)),
        2,
    ),
    # The red pad sits beyond the (initially open) yellow door.
    mk(
        [
            sprites["player"].clone().set_position(1, 6),
            sprites["door_y"].clone().set_position(4, 2),
            sprites["pad_r"].clone().set_position(8, 1),
            sprites["door_r"].clone().set_position(7, 5),
            sprites["goal"].clone().set_position(7, 8),
        ]
        + walls(col(4, 2) + row(5, 5, 9, 7)),
        3,
    ),
    # Horizontal snake: red, yellow, red.
    mk(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["pad_r"].clone().set_position(4, 1),
            sprites["door_r"].clone().set_position(8, 3),
            sprites["pad_y"].clone().set_position(5, 4),
            sprites["door_y"].clone().set_position(1, 6),
            sprites["pad_r"].clone().set_position(2, 9),
            sprites["door_r"].clone().set_position(5, 8),
            sprites["goal"].clone().set_position(8, 8),
        ]
        + walls(row(3, 0, 9, 8) + row(6, 0, 9, 1) + [(5, 7), (5, 9)]),
        4,
    ),
    # Four doors, alternating hues, ending in a walled goal pocket.
    mk(
        [
            sprites["player"].clone().set_position(1, 0),
            sprites["pad_r"].clone().set_position(1, 2),
            sprites["door_r"].clone().set_position(3, 8),
            sprites["pad_y"].clone().set_position(4, 5),
            sprites["door_y"].clone().set_position(6, 1),
            sprites["pad_r"].clone().set_position(8, 0),
            sprites["door_r"].clone().set_position(9, 4),
            sprites["pad_y"].clone().set_position(7, 5),
            sprites["door_y"].clone().set_position(7, 7),
            sprites["goal"].clone().set_position(8, 9),
        ]
        + walls(col(3, 8) + col(6, 1) + row(4, 7, 9, 9) + row(7, 7, 9, 7)),
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
        self._ui.reset(self._active)

    def _sync_doors(self) -> bool:
        any_opened = False
        for d in self._doors:
            need = 8 if "c8" in d.tags else 11
            open_ok = need == self._active
            was_blocked = d.is_collidable
            d.set_collidable(not open_ok)
            if was_blocked and open_ok:
                any_opened = True
        return any_opened

    def _sync_doors_and_flash(self) -> None:
        if self._sync_doors():
            self._ui.flash_door_open()
        self._ui.update(self._active)

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

        sp2 = sp
        if sp2 and "recolor" in sp2.tags:
            if "c8" in sp2.tags:
                self._active = 8
            elif "c11" in sp2.tags:
                self._active = 11
            self._sync_doors_and_flash()

        if self._player.x == self._goal.x and self._player.y == self._goal.y:
            self.next_level()

        self.complete_action()
