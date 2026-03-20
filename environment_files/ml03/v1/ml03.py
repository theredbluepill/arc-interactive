"""Mirror laser (splitter): fire must illuminate **all** yellow receptors in one shot; beam passes through receptors. Mirrors reflect as in ml01."""

from __future__ import annotations

from arcengine import (
    ARCBaseGame,
    Camera,
    GameAction,
    Level,
    RenderableUserDisplay,
    Sprite,
)

BACKGROUND_COLOR = 5
PADDING_COLOR = 4
CAM_W = CAM_H = 24

WALL_C = 3
PLAYER_C = 9
HAZ_C = 8
EMIT_C = 12
GOAL_C = 11
MIR_SL = 15
MIR_BS = 7


class Ml03UI(RenderableUserDisplay):
    def __init__(self, inv: int, steps: int) -> None:
        self._inv = inv
        self._steps = steps

    def update(self, inv: int, steps: int) -> None:
        self._inv = inv
        self._steps = steps

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for i in range(min(self._inv, 10)):
            frame[h - 2, 1 + i] = 15
        for i in range(min(self._steps, 30)):
            frame[h - 1, 1 + i] = 10
        return frame


sprites = {
    "wall": Sprite(
        pixels=[[WALL_C]],
        name="wall",
        visible=True,
        collidable=True,
        tags=["wall"],
    ),
    "hazard": Sprite(
        pixels=[[HAZ_C]],
        name="hazard",
        visible=True,
        collidable=True,
        tags=["hazard"],
    ),
    "player": Sprite(
        pixels=[[PLAYER_C]],
        name="player",
        visible=True,
        collidable=True,
        tags=["player"],
    ),
    "emitter": Sprite(
        pixels=[[EMIT_C]],
        name="emitter",
        visible=True,
        collidable=False,
        tags=["emitter"],
    ),
    "receptor": Sprite(
        pixels=[[GOAL_C]],
        name="receptor",
        visible=True,
        collidable=False,
        tags=["receptor"],
    ),
    "m_slash": Sprite(
        pixels=[[MIR_SL]],
        name="m_slash",
        visible=True,
        collidable=True,
        tags=["mirror", "slash"],
    ),
    "m_bslash": Sprite(
        pixels=[[MIR_BS]],
        name="m_bslash",
        visible=True,
        collidable=True,
        tags=["mirror", "bslash"],
    ),
}


def mk(
    grid: tuple[int, int],
    walls: list[tuple[int, int]],
    hazards: list[tuple[int, int]],
    player: tuple[int, int],
    emitter: tuple[int, int],
    emit_dxdy: tuple[int, int],
    receptors: list[tuple[int, int]],
    preset_mirrors: list[tuple[int, int, str]],
    inv: int,
    max_steps: int,
    diff: int,
) -> Level:
    sl: list[Sprite] = []
    for wx, wy in walls:
        sl.append(sprites["wall"].clone().set_position(wx, wy))
    for hx, hy in hazards:
        sl.append(sprites["hazard"].clone().set_position(hx, hy))
    sl.append(sprites["player"].clone().set_position(player[0], player[1]))
    sl.append(sprites["emitter"].clone().set_position(emitter[0], emitter[1]))
    for rx, ry in receptors:
        sl.append(sprites["receptor"].clone().set_position(rx, ry))
    for mx, my, kind in preset_mirrors:
        sp = (
            sprites["m_slash"].clone()
            if kind == "/"
            else sprites["m_bslash"].clone()
        )
        sl.append(sp.set_position(mx, my))
    return Level(
        sprites=sl,
        grid_size=grid,
        data={
            "difficulty": diff,
            "emit_dx": emit_dxdy[0],
            "emit_dy": emit_dxdy[1],
            "mirror_inv": inv,
            "max_steps": max_steps,
        },
    )


levels = [
    mk(
        (24, 24),
        [(x, 12) for x in range(5, 20)],
        [],
        (2, 11),
        (2, 12),
        (1, 0),
        [(20, 12), (22, 12)],
        [],
        10,
        240,
        1,
    ),
    mk(
        (24, 24),
        [(x, 12) for x in range(6, 18)],
        [],
        (3, 12),
        (3, 12),
        (1, 0),
        [(19, 12), (22, 12)],
        [(18, 10, "\\"), (18, 14, "/")],
        6,
        220,
        2,
    ),
    mk(
        (24, 24),
        [(10, y) for y in range(24) if y != 11],
        [(15, 15)],
        (5, 11),
        (5, 11),
        (1, 0),
        [(18, 12), (22, 12)],
        [],
        8,
        280,
        3,
    ),
    mk(
        (24, 24),
        [],
        [(8, 8), (16, 16)],
        (1, 1),
        (1, 1),
        (0, 1),
        [(20, 1), (22, 1)],
        [(12, 6, "/"), (6, 12, "\\")],
        8,
        300,
        4,
    ),
    mk(
        (24, 24),
        [(x, x) for x in range(24) if x % 4 == 0 and x not in (0, 20)],
        [],
        (2, 22),
        (2, 22),
        (1, 0),
        [(18, 22), (21, 22)],
        [],
        10,
        350,
        5,
    ),
]


def _reflect(dx: int, dy: int, slash: bool) -> tuple[int, int]:
    if slash:
        return (-dy, -dx)
    return (dy, dx)


class Ml03(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Ml03UI(0, 0)
        super().__init__(
            "ml03",
            levels,
            Camera(0, 0, CAM_W, CAM_H, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 5, 6],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        em = self.current_level.get_sprites_by_tag("emitter")[0]
        self._emit = (em.x, em.y)
        self._receptors = {
            (s.x, s.y) for s in self.current_level.get_sprites_by_tag("receptor")
        }
        self._edx = int(self.current_level.get_data("emit_dx") or 1)
        self._edy = int(self.current_level.get_data("emit_dy") or 0)
        self._inv = int(self.current_level.get_data("mirror_inv") or 6)
        self._steps = int(self.current_level.get_data("max_steps") or 250)
        self._sync_ui()

    def _sync_ui(self) -> None:
        self._ui.update(self._inv, self._steps)

    def _burn(self) -> bool:
        self._steps -= 1
        self._sync_ui()
        if self._steps <= 0:
            self.lose()
            return True
        return False

    def _mirror_at(self, x: int, y: int):
        sp = self.current_level.get_sprite_at(x, y, ignore_collidable=True)
        if sp and "mirror" in sp.tags:
            return sp
        return None

    def _fire_laser(self) -> None:
        x, y = self._emit[0] + self._edx, self._emit[1] + self._edy
        dx, dy = self._edx, self._edy
        gw, gh = self.current_level.grid_size
        hit: set[tuple[int, int]] = set()
        for _ in range(gw * gh + 10):
            if not (0 <= x < gw and 0 <= y < gh):
                return
            sp = self.current_level.get_sprite_at(x, y, ignore_collidable=True)
            if sp and "receptor" in sp.tags:
                hit.add((x, y))
                x += dx
                y += dy
                continue
            if sp and "wall" in sp.tags:
                return
            if sp and "hazard" in sp.tags:
                return
            if sp and "mirror" in sp.tags:
                slash = "slash" in sp.tags
                dx, dy = _reflect(dx, dy, slash)
                x += dx
                y += dy
                continue
            if sp and "emitter" in sp.tags:
                x += dx
                y += dy
                continue
            if sp and "player" in sp.tags:
                x += dx
                y += dy
                continue
            x += dx
            y += dy
        if self._receptors and hit >= self._receptors:
            self.next_level()

    def step(self) -> None:
        aid = self.action.id

        if aid in (GameAction.ACTION1, GameAction.ACTION2, GameAction.ACTION3, GameAction.ACTION4):
            dx = dy = 0
            if aid == GameAction.ACTION1:
                dy = -1
            elif aid == GameAction.ACTION2:
                dy = 1
            elif aid == GameAction.ACTION3:
                dx = -1
            elif aid == GameAction.ACTION4:
                dx = 1
            nx, ny = self._player.x + dx, self._player.y + dy
            gw, gh = self.current_level.grid_size
            if 0 <= nx < gw and 0 <= ny < gh:
                sp = self.current_level.get_sprite_at(nx, ny, ignore_collidable=True)
                if sp and ("wall" in sp.tags or "mirror" in sp.tags):
                    pass
                elif sp and "hazard" in sp.tags:
                    self.lose()
                    self.complete_action()
                    return
                elif not sp or not sp.is_collidable:
                    self._player.set_position(nx, ny)
                elif "emitter" in sp.tags or "receptor" in sp.tags:
                    self._player.set_position(nx, ny)
            if self._burn():
                return
            self.complete_action()
            return

        if aid == GameAction.ACTION5:
            self._fire_laser()
            if self._burn():
                return
            self.complete_action()
            return

        if aid != GameAction.ACTION6:
            self.complete_action()
            return

        px = self.action.data.get("x", 0)
        py = self.action.data.get("y", 0)
        coords = self.camera.display_to_grid(px, py)
        if coords is None:
            if self._burn():
                return
            self.complete_action()
            return
        gx, gy = coords
        if abs(gx - self._player.x) + abs(gy - self._player.y) != 1:
            if self._burn():
                return
            self.complete_action()
            return
        gw, gh = self.current_level.grid_size
        if not (0 <= gx < gw and 0 <= gy < gh):
            if self._burn():
                return
            self.complete_action()
            return

        existing = self.current_level.get_sprite_at(gx, gy, ignore_collidable=True)
        if existing and "mirror" in existing.tags:
            slash = "slash" in existing.tags
            self.current_level.remove_sprite(existing)
            new_sp = (
                sprites["m_bslash"].clone().set_position(gx, gy)
                if slash
                else sprites["m_slash"].clone().set_position(gx, gy)
            )
            self.current_level.add_sprite(new_sp)
            if self._burn():
                return
            self.complete_action()
            return

        if existing and (
            "wall" in existing.tags
            or "hazard" in existing.tags
            or "emitter" in existing.tags
            or "receptor" in existing.tags
        ):
            if self._burn():
                return
            self.complete_action()
            return

        if self._inv <= 0:
            if self._burn():
                return
            self.complete_action()
            return

        self.current_level.add_sprite(sprites["m_slash"].clone().set_position(gx, gy))
        self._inv -= 1
        self._sync_ui()
        if self._burn():
            return
        self.complete_action()
