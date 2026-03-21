"""Interactive human play using pygame (persistent window, ACTION6 = click)."""

from __future__ import annotations

from typing import Any

import numpy as np
import pygame
from arc_agi.rendering import COLOR_MAP, hex_to_rgb
from arcengine import GameAction, GameState

# Logical frame is always 64×64 in toolkit observations.
_FRAME = 64
# Pixels per logical cell — larger values = bigger window and readable cell coords.
_SCALE = 14
_SIDEBAR_W = 280
def _raster_to_surface(layer: Any, scale: int) -> pygame.Surface:
    arr = np.asarray(layer, dtype=np.uint8)
    h, w = arr.shape
    rgb = np.zeros((h, w, 3), dtype=np.uint8)
    for idx, hx in COLOR_MAP.items():
        rgb[arr == idx] = hex_to_rgb(hx)
    surf = pygame.Surface((w, h))
    for yy in range(h):
        for xx in range(w):
            surf.set_at((xx, yy), (int(rgb[yy, xx, 0]), int(rgb[yy, xx, 1]), int(rgb[yy, xx, 2])))
    if scale != 1:
        surf = pygame.transform.scale(surf, (w * scale, h * scale))
    return surf


def _draw_cell_coord_popover(
    screen: pygame.Surface,
    tip_font: pygame.font.Font,
    mx: int,
    my: int,
    gx: int,
    gy: int,
    scale: int,
) -> None:
    """Crisp tooltip for ACTION6 (x, y); clamped inside the grid area."""
    text = f"({gx}, {gy})"
    # Bitmap-style glyph edges read better on busy backgrounds than tiny AA text.
    surf = tip_font.render(text, False, (248, 248, 248))
    pad_x, pad_y = 10, 8
    bw = surf.get_width() + pad_x * 2
    bh = surf.get_height() + pad_y * 2
    ox = mx + 18
    oy = my + 18
    grid_px = _FRAME * scale
    ox = max(6, min(ox, grid_px - bw - 6))
    oy = max(6, min(oy, grid_px - bh - 6))
    rect = pygame.Rect(ox, oy, bw, bh)
    pygame.draw.rect(screen, (22, 22, 26), rect)
    pygame.draw.rect(screen, (120, 120, 135), rect, width=1)
    screen.blit(surf, (ox + pad_x, oy + pad_y))


def _levels_hud_line(obs: Any) -> str:
    """Toolkit ``levels_completed`` = levels *finished* (starts at 0). Show 1-based *current* level."""
    lc = int(getattr(obs, "levels_completed", 0) or 0)
    wl_raw = getattr(obs, "win_levels", None)
    wl = int(wl_raw) if wl_raw is not None else 0
    st = obs.state
    if wl <= 0:
        return f"level: {lc + 1}/?"
    if st == GameState.WIN:
        return f"level: {wl}/{wl}"
    current = min(max(lc + 1, 1), wl)
    return f"level: {current}/{wl}"


def _display_xy_from_mouse(mx: int, my: int, scale: int) -> tuple[int, int]:
    gx = int(mx // scale)
    gy = int(my // scale)
    return max(0, min(_FRAME - 1, gx)), max(0, min(_FRAME - 1, gy))


def _draw_sidebar(
    screen: pygame.Surface,
    small: pygame.font.Font,
    obs: Any,
    game_id: str,
    steps: int,
    x0: int,
    *,
    error_line: str | None = None,
) -> None:
    y = 8
    lines = [
        f"game: {game_id}",
        f"state: {getattr(obs.state, 'name', obs.state)}",
        _levels_hud_line(obs),
        f"steps: {steps}",
        f"avail: {getattr(obs, 'available_actions', [])}",
        "",
        "WASD / arrows: 1–4",
        "Space / F: 5",
        "Hover grid: (x,y) tooltip",
        "Click grid: ACTION6",
        "U / Ctrl+Z / Cmd+Z: 7",
        "R: reset  Q: quit",
        "",
        "Click grid area first so keys go here",
    ]
    for line in lines:
        surf = small.render(line, True, (220, 220, 220))
        screen.blit(surf, (x0 + 6, y))
        y += small.get_height() + 2
    if error_line:
        surf = small.render(error_line[:80], True, (255, 100, 100))
        screen.blit(surf, (x0 + 6, y))


def _present_obs(
    screen: pygame.Surface,
    small: pygame.font.Font,
    tip_font: pygame.font.Font,
    obs: Any,
    game_id: str,
    steps: int,
    scale: int,
    hover_xy: tuple[int, int] | None,
    *,
    error_line: str | None = None,
    idle_delay_ms: int = 25,
) -> None:
    layers = getattr(obs, "frame", None) or []
    # One toolkit step can append several full camera renders (e.g. level change);
    # show only the final frame so the grid matches the live game state.
    if layers:
        layers = [layers[-1]]
    x0 = _FRAME * scale
    screen.fill((40, 40, 40))
    if layers:
        for layer in layers:
            surf = _raster_to_surface(layer, scale)
            screen.blit(surf, (0, 0))
        if hover_xy is not None:
            mx, my = hover_xy
            gw = gh = _FRAME * scale
            if 0 <= mx < gw and 0 <= my < gh:
                gx, gy = _display_xy_from_mouse(mx, my, scale)
                _draw_cell_coord_popover(screen, tip_font, mx, my, gx, gy, scale)
    else:
        hint = small.render("No frame in obs — use ARC_OPERATION_MODE=offline", True, (200, 120, 120))
        screen.blit(hint, (8, 8))
    _draw_sidebar(screen, small, obs, game_id, steps, x0, error_line=error_line)
    pygame.display.flip()
    if idle_delay_ms > 0:
        pygame.time.delay(idle_delay_ms)


def run_interactive_pygame(environment: Any) -> int:
    """Run until user quits. Returns number of ``step`` calls (excludes ``reset``)."""
    pygame.init()
    try:
        pygame.display.set_caption("ARC-AGI-3 — human play (pygame)")
        small = pygame.font.Font(None, 22)
        tip_font = pygame.font.Font(None, 26)
        w = _FRAME * _SCALE + _SIDEBAR_W
        h = _FRAME * _SCALE
        screen = pygame.display.set_mode((w, h))

        game_id = getattr(environment.info, "game_id", "?")
        obs = environment.reset()
        if obs is None:
            return 0
        step_count = 0
        hover_xy: tuple[int, int] | None = None

        def paint(
            *,
            err: str | None = None,
            idle_delay_ms: int = 25,
        ) -> None:
            _present_obs(
                screen,
                small,
                tip_font,
                obs,
                game_id,
                step_count,
                _SCALE,
                hover_xy,
                error_line=err,
                idle_delay_ms=idle_delay_ms,
            )

        paint()

        running = True
        clock = pygame.time.Clock()
        while running:
            pygame.event.pump()
            events = pygame.event.get()
            if not events:
                clock.tick(60)
                continue

            for event in events:
                if event.type == pygame.QUIT:
                    running = False
                    break

                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_q, pygame.K_ESCAPE):
                        running = False
                        break
                    if event.key == pygame.K_r:
                        obs = environment.reset()
                        step_count = 0
                        if obs:
                            paint()
                        continue

                    action: GameAction | None = None
                    if event.key in (pygame.K_w, pygame.K_UP):
                        action = GameAction.ACTION1
                    elif event.key in (pygame.K_s, pygame.K_DOWN):
                        action = GameAction.ACTION2
                    elif event.key in (pygame.K_a, pygame.K_LEFT):
                        action = GameAction.ACTION3
                    elif event.key in (pygame.K_d, pygame.K_RIGHT):
                        action = GameAction.ACTION4
                    elif event.key in (pygame.K_SPACE, pygame.K_f):
                        action = GameAction.ACTION5
                    elif event.key == pygame.K_1:
                        action = GameAction.ACTION1
                    elif event.key == pygame.K_2:
                        action = GameAction.ACTION2
                    elif event.key == pygame.K_3:
                        action = GameAction.ACTION3
                    elif event.key == pygame.K_4:
                        action = GameAction.ACTION4
                    elif event.key == pygame.K_5:
                        action = GameAction.ACTION5
                    elif event.key == pygame.K_u:
                        action = GameAction.ACTION7
                    elif event.key == pygame.K_z and (
                        event.mod & (pygame.KMOD_CTRL | pygame.KMOD_META)
                    ):
                        action = GameAction.ACTION7

                    if action is None and event.unicode and len(event.unicode) == 1:
                        ch = event.unicode.lower()
                        if ch == "f" and not (
                            event.mod & (pygame.KMOD_CTRL | pygame.KMOD_META)
                        ):
                            action = GameAction.ACTION5

                    if action is not None:
                        nxt = environment.step(
                            action,
                            data={},
                            reasoning={"thought": "pygame key", "step": step_count + 1},
                        )
                        if nxt is not None:
                            obs = nxt
                            step_count += 1
                            paint()
                        else:
                            paint(
                                err="env.step failed — see terminal log",
                            )
                        if obs and obs.state in (GameState.WIN, GameState.GAME_OVER):
                            pass  # keep window open until R / Q

                elif event.type == pygame.MOUSEMOTION:
                    hover_xy = event.pos
                    paint(idle_delay_ms=0)

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    hover_xy = (mx, my)
                    if mx < _FRAME * _SCALE and my < _FRAME * _SCALE:
                        dx, dy = _display_xy_from_mouse(mx, my, _SCALE)
                        nxt = environment.step(
                            GameAction.ACTION6,
                            data={"x": dx, "y": dy},
                            reasoning={"thought": "pygame click", "step": step_count + 1},
                        )
                        if nxt is not None:
                            obs = nxt
                            step_count += 1
                            paint()
                        else:
                            paint(
                                err="env.step failed — see terminal log",
                            )

        return step_count
    finally:
        pygame.quit()
