"""Like tt02 but new yellow targets may spawn every few moves (capped)."""

from __future__ import annotations

import random

from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)


class Tt03UI(RenderableUserDisplay):
    def __init__(self, targets_remaining: int) -> None:
        self._targets = targets_remaining

    def update(self, targets_remaining: int) -> None:
        self._targets = targets_remaining

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
    "target": Sprite(
        pixels=[[11]],
        name="target",
        visible=True,
        collidable=False,
        tags=["target"],
    ),
    "wall": Sprite(
        pixels=[[3]],
        name="wall",
        visible=True,
        collidable=True,
        tags=["wall"],
    ),
    "hazard": Sprite(
        pixels=[[8]],
        name="hazard",
        visible=True,
        collidable=True,
        tags=["hazard", "patrol"],
    ),
}


def lvl(
    grid: tuple[int, int],
    sprites_list: list[Sprite],
    patrols: list[list[list[int]]],
    diff: int,
    *,
    spawn_every: int = 10,
    target_cap: int = 6,
) -> Level:
    return Level(
        sprites=sprites_list,
        grid_size=grid,
        data={
            "difficulty": diff,
            "patrols": patrols,
            "spawn_every": spawn_every,
            "target_cap": target_cap,
        },
    )


levels = [
    lvl(
        (8, 8),
        [
            sprites["player"].clone().set_position(1, 1),
            sprites["target"].clone().set_position(2, 6),
            sprites["target"].clone().set_position(6, 2),
            sprites["wall"].clone().set_position(2, 2),
            sprites["wall"].clone().set_position(4, 4),
            sprites["hazard"].clone().set_position(5, 3),
        ],
        [[[5, 3], [6, 3], [6, 4], [5, 4], [4, 4], [4, 3]]],
        1,
    ),
    lvl(
        (16, 16),
        [
            sprites["player"].clone().set_position(2, 2),
            sprites["target"].clone().set_position(10, 10),
            sprites["target"].clone().set_position(12, 4),
            sprites["hazard"].clone().set_position(6, 6),
            sprites["hazard"].clone().set_position(10, 6),
        ]
        + [sprites["wall"].clone().set_position(8, y) for y in range(16) if y != 7],
        [
            [[6, 6], [7, 6], [8, 6], [9, 6], [9, 7], [9, 8], [8, 8], [7, 8], [6, 8], [6, 7]],
            [[10, 6], [11, 6], [12, 6], [12, 7], [12, 8], [11, 8], [10, 8], [10, 7]],
        ],
        2,
    ),
    lvl(
        (24, 24),
        [
            sprites["player"].clone().set_position(3, 3),
            sprites["target"].clone().set_position(20, 20),
            sprites["target"].clone().set_position(15, 8),
            sprites["target"].clone().set_position(8, 18),
            sprites["hazard"].clone().set_position(12, 12),
        ],
        [[[12, 12], [13, 12], [14, 12], [14, 13], [14, 14], [13, 14], [12, 14], [12, 13]]],
        3,
    ),
]

BACKGROUND_COLOR = 5
PADDING_COLOR = 4


class Tt03(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = Tt03UI(0)
        super().__init__(
            "tt03",
            levels,
            Camera(0, 0, 24, 24, BACKGROUND_COLOR, PADDING_COLOR, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._targets = self.current_level.get_sprites_by_tag("target")
        paths = self.current_level.get_data("patrols") or []
        haz = [s for s in self.current_level.get_sprites_by_tag("patrol")]
        self._patrol_hazards: list[tuple[Sprite, list[tuple[int, int]], int]] = []
        for i, s in enumerate(haz):
            loop = paths[i] if i < len(paths) else [[s.x, s.y]]
            pts = [(int(p[0]), int(p[1])) for p in loop]
            self._patrol_hazards.append((s, pts, 0))
        self._spawn_every = int(self.current_level.get_data("spawn_every") or 10)
        self._target_cap = int(self.current_level.get_data("target_cap") or 6)
        self._move_count = 0
        self._ui.update(len(self._targets))

    def _maybe_spawn_target(self) -> None:
        if len(self._targets) >= self._target_cap:
            return
        gw, gh = self.current_level.grid_size
        opts: list[tuple[int, int]] = []
        for x in range(gw):
            for y in range(gh):
                sp = self.current_level.get_sprite_at(x, y, ignore_collidable=True)
                if sp and (
                    "wall" in sp.tags
                    or "hazard" in sp.tags
                    or "target" in sp.tags
                ):
                    continue
                if not sp or not sp.is_collidable:
                    opts.append((x, y))
        if not opts:
            return
        sx, sy = random.choice(opts)
        t = sprites["target"].clone().set_position(sx, sy)
        self.current_level.add_sprite(t)
        self._targets.append(t)
        self._ui.update(len(self._targets))

    def _advance_patrols(self) -> None:
        for i, (sp, pts, idx) in enumerate(self._patrol_hazards):
            if not pts:
                continue
            nidx = (idx + 1) % len(pts)
            nx, ny = pts[nidx]
            sp.set_position(nx, ny)
            self._patrol_hazards[i] = (sp, pts, nidx)

    def step(self) -> None:
        dx = dy = 0
        moved = False

        if self.action.id.value == 1:
            dy = -1
            moved = True
        elif self.action.id.value == 2:
            dy = 1
            moved = True
        elif self.action.id.value == 3:
            dx = -1
            moved = True
        elif self.action.id.value == 4:
            dx = 1
            moved = True

        if not moved:
            self.complete_action()
            return

        new_x = self._player.x + dx
        new_y = self._player.y + dy

        grid_w, grid_h = self.current_level.grid_size
        if 0 <= new_x < grid_w and 0 <= new_y < grid_h:
            sprite = self.current_level.get_sprite_at(
                new_x, new_y, ignore_collidable=True
            )

            if sprite and "target" in sprite.tags:
                self.current_level.remove_sprite(sprite)
                self._targets.remove(sprite)
                self._player.set_position(new_x, new_y)
                self._ui.update(len(self._targets))
            elif not sprite or not sprite.is_collidable:
                self._player.set_position(new_x, new_y)
            elif sprite and "hazard" in sprite.tags:
                self.complete_action()
                return

        self._advance_patrols()

        self._move_count += 1
        if self._spawn_every > 0 and self._move_count % self._spawn_every == 0:
            self._maybe_spawn_target()

        px, py = self._player.x, self._player.y
        hit = self.current_level.get_sprite_at(px, py, ignore_collidable=True)
        if hit and "hazard" in hit.tags:
            self.lose()
            self.complete_action()
            return

        if len(self._targets) == 0:
            self.next_level()

        self.complete_action()
