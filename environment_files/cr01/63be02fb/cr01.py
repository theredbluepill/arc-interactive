"""Creek crossing: water blocks movement; ACTION6 places a horizontal 2-cell plank (budget); planks removed when you leave those cells."""

from arcengine import (
    ARCBaseGame,
    Camera,
    GameAction,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Cr01UI(RenderableUserDisplay):
    def __init__(self, planks: int) -> None:
        self._planks = planks

    def update(self, planks: int) -> None:
        self._planks = planks

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for i in range(min(self._planks, 8)):
            frame[h - 2, 1 + i] = 11
        return frame


sprites = {
    "player": Sprite(
        pixels=[[9]],
        name="player",
        visible=True,
        collidable=True,
        tags=["player"],
    ),
    "water": Sprite(
        pixels=[[10]],
        name="water",
        visible=True,
        collidable=True,
        tags=["water"],
    ),
    "plank": Sprite(
        pixels=[[12]],
        name="plank",
        visible=True,
        collidable=False,
        tags=["plank"],
    ),
    "goal": Sprite(
        pixels=[[14]],
        name="goal",
        visible=True,
        collidable=False,
        tags=["goal"],
    ),
    "land": Sprite(
        pixels=[[5]],
        name="land",
        visible=False,
        collidable=False,
        tags=["land"],
    ),
}


def mk(sl, budget: int, d: int):
    return Level(
        sprites=sl,
        grid_size=(16, 16),
        data={"difficulty": d, "plank_budget": budget},
    )


levels = [
    mk(
        [
            sprites["player"].clone().set_position(1, 2),
            sprites["goal"].clone().set_position(14, 2),
        ]
        + [sprites["water"].clone().set_position(x, 2) for x in range(3, 14)],
        3,
        1,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 5),
            sprites["goal"].clone().set_position(15, 5),
        ]
        + [sprites["water"].clone().set_position(x, 5) for x in range(2, 14)],
        4,
        2,
    ),
    mk(
        [
            sprites["player"].clone().set_position(2, 8),
            sprites["goal"].clone().set_position(13, 8),
        ]
        + [sprites["water"].clone().set_position(x, 8) for x in range(4, 12)],
        2,
        3,
    ),
    mk(
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["goal"].clone().set_position(14, 14),
        ]
        + [sprites["water"].clone().set_position(x, 7) for x in range(1, 15)],
        5,
        4,
    ),
    mk(
        [
            sprites["player"].clone().set_position(0, 0),
            sprites["goal"].clone().set_position(15, 0),
        ]
        + [sprites["water"].clone().set_position(x, 0) for x in range(4, 12)],
        3,
        5,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Cr01(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Cr01UI(0)
        self._plank_cells: dict[tuple[int, int], Sprite] = {}
        super().__init__(
            "cr01",
            levels,
            Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 6],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._budget = int(self.current_level.get_data("plank_budget") or 3)
        self._plank_cells = {}
        self._ui.update(self._budget)

    def _remove_plank_at(self, x: int, y: int) -> None:
        k = (x, y)
        if k not in self._plank_cells:
            return
        pl = self._plank_cells.pop(k)
        self.current_level.remove_sprite(pl)
        self.current_level.add_sprite(sprites["water"].clone().set_position(x, y))

    def step(self) -> None:
        if self.action.id == GameAction.ACTION6:
            if self._budget <= 0:
                self.complete_action()
                return
            px, py = int(self.action.data.get("x", 0)), int(self.action.data.get("y", 0))
            hit = self.camera.display_to_grid(px, py)
            if hit is None:
                self.complete_action()
                return
            gx, gy = int(hit[0]), int(hit[1])
            if gx + 1 >= self.current_level.grid_size[0]:
                self.complete_action()
                return
            for ox in (gx, gx + 1):
                sp = self.current_level.get_sprite_at(ox, gy, ignore_collidable=True)
                if not sp or "water" not in sp.tags:
                    self.complete_action()
                    return
            for ox in (gx, gx + 1):
                w = self.current_level.get_sprite_at(ox, gy, ignore_collidable=True)
                if w:
                    self.current_level.remove_sprite(w)
                p = sprites["plank"].clone().set_position(ox, gy)
                self.current_level.add_sprite(p)
                self._plank_cells[(ox, gy)] = p
            self._budget -= 1
            self._ui.update(self._budget)
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

        ox, oy = self._player.x, self._player.y
        nx, ny = ox + dx, oy + dy
        gw, gh = self.current_level.grid_size
        if not (0 <= nx < gw and 0 <= ny < gh):
            self.complete_action()
            return

        sp = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
        if sp and sp.is_collidable and "water" in sp.tags:
            self.complete_action()
            return

        if not sp or not sp.is_collidable:
            self._player.set_position(nx, ny)

        if (ox, oy) in self._plank_cells:
            self._remove_plank_at(ox, oy)

        gl = self.current_level.get_sprites_by_tag("goal")
        if gl and self._player.x == gl[0].x and self._player.y == gl[0].y:
            self.next_level()

        self.complete_action()
