"""Mirror laser puzzle (ml01).

**Goal:** Hit the yellow **receptor** with the laser.

**Pieces:** Orange **emitter** — the beam *starts* in the emitter's facing direction from
the cell *next to* the emitter (see level ``emit_dx`` / ``emit_dy``, usually east).
Purple cells are **mirrors**; ``/`` and ``\\`` reflect the beam (standard 90° turns).
There is **no** separate avatar — only emitter, receptor, walls, and mirrors.

**Color key (terminal palette):** **Orange** = emitter, **yellow** = receptor, **purple** (**15**)
= ``/`` mirror + mirror-inventory HUD ticks, **light magenta** (**7**) = ``\\`` mirror — each
**ACTION6** on a mirror **swaps** hue as it toggles ``/`` ↔ ``\\``. **Magenta** (**6**) = last
laser trace (not a mirror).

**Level ramp (vs other ``ml*`` games):** **ml01** = **global** clicks (any valid cell).
**ml02**/**ml03** add a **blue technician** you **move**; mirrors only on **orthogonal
neighbors** of that cell. **ml04** = smaller grid, **stepped** laser bolt, **cycle** fixed
slots (``/`` / ``\\`` / empty) — no placement inventory.

1. Horizontal wall — **three** mirrors (up / across / down).
2. Same wall + **preset** corner — **two** placements.
3. Longer wall; receptor **one row up** — three mirrors.
4. **South** emitter, hazards, preset mirrors — different aim.
5. **Diagonal** wall posts — open maze; needs routing.

**Actions:**
- **ACTION5 — Fire:** Shoot once from the emitter along the ray; each shot costs one step.
  The ray walks cell-by-cell, reflects off mirrors, stops on walls/hazards, and **clears the
  level** when it enters the receptor cell. A short **magenta** trace is drawn after each shot.
- **ACTION6 — Click:** Send display ``x,y`` (64×64 frame, cell centers work best). Maps to a
  grid cell via ``display_to_grid``. On **empty floor**, places a new ``/`` mirror (uses
  **inventory** — purple HUD ticks). On an existing mirror, **cycles** ``/`` ↔ ``\\``.
  Cannot place on wall, hazard, emitter, or receptor. Off-grid or invalid clicks
  still **cost a step**.
- **ACTION1–4:** No-op (no step cost).
- **ACTION7 — Undo:** Restore board, mirror inventory, and step count to before the last
  **ACTION5** or **ACTION6** (no step cost). Stack clears on level change; capped depth.

**Lose:** Step counter (cyan bottom HUD) reaches zero before clearing the level.
"""

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
HAZ_C = 8
EMIT_C = 12
GOAL_C = 11
# Slash vs backslash use different hues so ACTION6 cycles are visible on a 1×1 cell.
MIR_SL = 15  # purple — /
MIR_BS = 7  # light magenta — \

MAX_UNDO = 64


class Ml01UI(RenderableUserDisplay):
    """HUD + optional post-shot laser trace (same 64×64 scale/pad as the playfield)."""

    LASER_COLOR = 6  # beam trace — distinct from mirrors (7/15) and step HUD (10)
    LASER_HOLD_FRAMES = 14

    def __init__(self, inv: int, steps: int) -> None:
        self._inv = inv
        self._steps = steps
        self._laser_path: list[tuple[int, int]] = []
        self._laser_frames = 0

    def update(self, inv: int, steps: int) -> None:
        self._inv = inv
        self._steps = steps

    def set_laser_path(self, path: list[tuple[int, int]]) -> None:
        self._laser_path = list(path)
        self._laser_frames = self.LASER_HOLD_FRAMES if path else 0

    def clear_laser(self) -> None:
        self._laser_path = []
        self._laser_frames = 0

    def render_interface(self, frame):
        import numpy as np

        if not isinstance(frame, np.ndarray):
            return frame
        h, w = frame.shape
        for i in range(min(self._inv, 10)):
            frame[h - 2, 1 + i] = 15
        for i in range(min(self._steps, 30)):
            frame[h - 1, 1 + i] = 10

        if self._laser_frames > 0 and self._laser_path:
            scale = min(64 // CAM_W, 64 // CAM_H)
            pad = (64 - CAM_W * scale) // 2

            def cell_center(gx: int, gy: int) -> tuple[int, int]:
                cx = gx * scale + scale // 2 + pad
                cy = gy * scale + scale // 2 + pad
                return cx, cy

            def plot(px: int, py: int) -> None:
                if 0 <= px < w and 0 <= py < h:
                    frame[py, px] = self.LASER_COLOR

            def segment(x0: int, y0: int, x1: int, y1: int) -> None:
                if y0 == y1:
                    lo, hi = (x0, x1) if x0 <= x1 else (x1, x0)
                    for px in range(lo, hi + 1):
                        plot(px, y0)
                elif x0 == x1:
                    lo, hi = (y0, y1) if y0 <= y1 else (y1, y0)
                    for py in range(lo, hi + 1):
                        plot(x0, py)

            prev: tuple[int, int] | None = None
            for gx, gy in self._laser_path:
                cx, cy = cell_center(gx, gy)
                if prev is not None:
                    segment(prev[0], prev[1], cx, cy)
                prev = (cx, cy)
                for ox, oy in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
                    plot(cx + ox, cy + oy)

            self._laser_frames -= 1
            if self._laser_frames <= 0:
                self._laser_path = []

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
    emitter: tuple[int, int],
    emit_dxdy: tuple[int, int],
    receptor: tuple[int, int],
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
    sl.append(sprites["emitter"].clone().set_position(emitter[0], emitter[1]))
    sl.append(sprites["receptor"].clone().set_position(receptor[0], receptor[1]))
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
    # L1 — horizontal wall; 3-mirror detour (/, /, \\). Receptor under last south leg.
    mk(
        (24, 24),
        [(x, 12) for x in range(8, 15)],
        [],
        (3, 12),
        (1, 0),
        (19, 12),
        [],
        6,
        260,
        1,
    ),
    # L2 — same geometry + preset corner; two placements.
    mk(
        (24, 24),
        [(x, 12) for x in range(8, 15)],
        [],
        (3, 12),
        (1, 0),
        (19, 12),
        [(7, 9, "/")],
        5,
        240,
        2,
    ),
    # L3 — longer wall; receptor one row up.
    mk(
        (24, 24),
        [(x, 12) for x in range(8, 16)],
        [],
        (4, 12),
        (1, 0),
        (20, 10),
        [],
        6,
        300,
        3,
    ),
    # L4 — south-facing emitter; hazards + presets (different aiming skill).
    mk(
        (24, 24),
        [],
        [(8, 8), (16, 16)],
        (1, 1),
        (0, 1),
        (22, 22),
        [(12, 6, "/"), (6, 12, "\\")],
        8,
        320,
        4,
    ),
    # L5 — diagonal wall posts; open routing puzzle.
    mk(
        (24, 24),
        [(x, x) for x in range(24) if x % 4 == 0 and x not in (0, 20)],
        [],
        (2, 22),
        (1, 0),
        (21, 2),
        [],
        10,
        380,
        5,
    ),
]


def _reflect(dx: int, dy: int, slash: bool) -> tuple[int, int]:
    if slash:
        return (-dy, -dx)
    return (dy, dx)


class Ml01(ARCBaseGame):
    def __init__(self) -> None:
        self._undo_stack: list[tuple[Level, int, int]] = []
        self._ui = Ml01UI(0, 0)
        super().__init__(
            "ml01",
            levels,
            Camera(0, 0, CAM_W, CAM_H, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4, 5, 6, 7],
        )

    def _grid_to_frame_pixel(self, gx: int, gy: int) -> tuple[int, int]:
        cam = self.camera
        cw, ch = cam.width, cam.height
        scale = min(64 // cw, 64 // ch)
        x_pad = (64 - cw * scale) // 2
        y_pad = (64 - ch * scale) // 2
        return gx * scale + scale // 2 + x_pad, gy * scale + scale // 2 + y_pad

    def on_set_level(self, level: Level) -> None:
        self._undo_stack.clear()
        self._ui.clear_laser()
        em = self.current_level.get_sprites_by_tag("emitter")[0]
        self._emit = (em.x, em.y)
        edx_raw = self.current_level.get_data("emit_dx")
        edy_raw = self.current_level.get_data("emit_dy")
        self._edx = int(edx_raw) if edx_raw is not None else 1
        self._edy = int(edy_raw) if edy_raw is not None else 0
        mi = self.current_level.get_data("mirror_inv")
        self._inv = int(mi) if mi is not None else 6
        ms = self.current_level.get_data("max_steps")
        self._steps = int(ms) if ms is not None else 250
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

    def _push_undo(self) -> None:
        if len(self._undo_stack) >= MAX_UNDO:
            self._undo_stack.pop(0)
        self._undo_stack.append(
            (self.current_level.clone(), self._inv, self._steps)
        )

    def _apply_undo(self) -> bool:
        if not self._undo_stack:
            return False
        snap_level, inv, steps = self._undo_stack.pop()
        self._levels[self._current_level_index] = snap_level.clone()
        self._inv = inv
        self._steps = steps
        em = self.current_level.get_sprites_by_tag("emitter")[0]
        self._emit = (em.x, em.y)
        self._ui.clear_laser()
        self._sync_ui()
        return True

    def _trace_laser(self) -> tuple[list[tuple[int, int]], bool]:
        """Return (ordered grid cells visited, hit_receptor)."""
        path: list[tuple[int, int]] = []
        x, y = self._emit[0] + self._edx, self._emit[1] + self._edy
        dx, dy = self._edx, self._edy
        gw, gh = self.current_level.grid_size
        for _ in range(gw * gh + 10):
            if not (0 <= x < gw and 0 <= y < gh):
                break
            path.append((x, y))
            sp = self.current_level.get_sprite_at(x, y, ignore_collidable=True)
            if sp and "receptor" in sp.tags:
                return path, True
            if sp and "wall" in sp.tags:
                return path, False
            if sp and "hazard" in sp.tags:
                return path, False
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
            x += dx
            y += dy
        return path, False

    def _fire_laser(self) -> None:
        path, won = self._trace_laser()
        self._ui.set_laser_path(path)
        if won:
            self.next_level()

    def step(self) -> None:
        aid = self.action.id

        if aid in (
            GameAction.ACTION1,
            GameAction.ACTION2,
            GameAction.ACTION3,
            GameAction.ACTION4,
        ):
            self.complete_action()
            return

        if aid == GameAction.ACTION7:
            self._apply_undo()
            self.complete_action()
            return

        if aid == GameAction.ACTION5:
            self._push_undo()
            self._fire_laser()
            if self._burn():
                self.complete_action()
                return
            self.complete_action()
            return

        if aid != GameAction.ACTION6:
            self.complete_action()
            return

        self._push_undo()

        px = int(self.action.data.get("x", 0))
        py = int(self.action.data.get("y", 0))
        coords = self.camera.display_to_grid(px, py)
        if coords is None:
            if self._burn():
                self.complete_action()
                return
            self.complete_action()
            return

        gx, gy = int(coords[0]), int(coords[1])
        gw, gh = self.current_level.grid_size
        if not (0 <= gx < gw and 0 <= gy < gh):
            if self._burn():
                self.complete_action()
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
                self.complete_action()
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
                self.complete_action()
                return
            self.complete_action()
            return

        if self._inv <= 0:
            if self._burn():
                self.complete_action()
                return
            self.complete_action()
            return

        self.current_level.add_sprite(sprites["m_slash"].clone().set_position(gx, gy))
        self._inv -= 1
        self._sync_ui()
        if self._burn():
            self.complete_action()
            return
        self.complete_action()
