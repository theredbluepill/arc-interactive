"""Interactive human play using pygame (persistent window, ACTION6 = click)."""

from __future__ import annotations

import os
from typing import Any

import numpy as np
import pygame
from arc_agi.rendering import COLOR_MAP, hex_to_rgb
from arcengine import GameAction, GameState

# Toolkit / camera render is always 64×64; logical grid size comes from each game’s camera.
_FRAME = 64
# Default pixels per cell (window ≈ 64 * this + sidebar). Override: ARC_HUMAN_PLAY_SCALE=8–18.
_PREFERRED_CELL_PX = 9
_MIN_CELL_PX = 6
_MAX_CELL_PX = 14
_SIDEBAR_W = 280


def _resolve_cell_scale() -> int:
    """Pick cell size from env or screen fit so the window is not oversized on UHD / laptops."""
    raw = (os.environ.get("ARC_HUMAN_PLAY_SCALE") or "").strip()
    if raw.isdigit():
        return max(_MIN_CELL_PX, min(18, int(raw)))
    try:
        info = pygame.display.Info()
        cw, ch = int(info.current_w or 0), int(info.current_h or 0)
        if cw <= 0 or ch <= 0:
            return _PREFERRED_CELL_PX
        margin_x = 72
        margin_y = 96
        max_w = max(_MIN_CELL_PX, (cw - _SIDEBAR_W - margin_x) // _FRAME)
        max_h = max(_MIN_CELL_PX, (ch - margin_y) // _FRAME)
        max_fit = min(max_w, max_h)
        return max(_MIN_CELL_PX, min(_MAX_CELL_PX, min(_PREFERRED_CELL_PX, max_fit)))
    except Exception:
        return _PREFERRED_CELL_PX


def _camera_display_layout(environment: Any) -> tuple[int, int, int, int, int]:
    """Match ``Camera`` letterboxing: logical (gw, gh), cell size in frame px, padding in 64×64."""
    game = getattr(environment, "_game", None)
    cam = getattr(game, "camera", None) if game is not None else None
    if cam is None:
        return _FRAME, _FRAME, 1, 0, 0
    try:
        gw, gh = int(cam.width), int(cam.height)
    except (TypeError, ValueError):
        return _FRAME, _FRAME, 1, 0, 0
    if gw <= 0 or gh <= 0:
        return _FRAME, _FRAME, 1, 0, 0
    sc_x = _FRAME // gw
    sc_y = _FRAME // gh
    cs = min(sc_x, sc_y)
    if cs < 1:
        cs = 1
    sw, sh = gw * cs, gh * cs
    xp = (_FRAME - sw) // 2
    yp = (_FRAME - sh) // 2
    return gw, gh, cs, xp, yp


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


def _world_coords_tooltip(environment: Any, disp_x: int, disp_y: int) -> str:
    """World / camera grid position for ACTION6 display (x,y), or em dash in letterbox."""
    game = getattr(environment, "_game", None)
    cam = getattr(game, "camera", None) if game is not None else None
    dg = getattr(cam, "display_to_grid", None) if cam is not None else None
    if dg is None:
        return "—"
    try:
        w = dg(int(disp_x), int(disp_y))
    except Exception:
        return "—"
    if w is None:
        return "—"
    return f"({w[0]}, {w[1]})"


def _draw_cell_coord_popover(
    screen: pygame.Surface,
    tip_font: pygame.font.Font,
    mx: int,
    my: int,
    gx: int,
    gy: int,
    scale: int,
    environment: Any,
) -> None:
    """ACTION6 display coords + engine grid coords; clamped inside the 64×64 view area."""
    line_disp = f"display ({gx}, {gy})"
    line_grid = f"grid {_world_coords_tooltip(environment, gx, gy)}"
    surf_d = tip_font.render(line_disp, False, (248, 248, 248))
    surf_g = tip_font.render(line_grid, False, (248, 248, 248))
    pad_x, pad_y = 10, 8
    line_gap = 2
    bw = max(surf_d.get_width(), surf_g.get_width()) + pad_x * 2
    bh = surf_d.get_height() + line_gap + surf_g.get_height() + pad_y * 2
    ox = mx + 18
    oy = my + 18
    grid_px = _FRAME * scale
    ox = max(6, min(ox, grid_px - bw - 6))
    oy = max(6, min(oy, grid_px - bh - 6))
    rect = pygame.Rect(ox, oy, bw, bh)
    pygame.draw.rect(screen, (22, 22, 26), rect)
    pygame.draw.rect(screen, (120, 120, 135), rect, width=1)
    screen.blit(surf_d, (ox + pad_x, oy + pad_y))
    screen.blit(surf_g, (ox + pad_x, oy + pad_y + surf_d.get_height() + line_gap))


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


def _draw_grid_lines(
    screen: pygame.Surface,
    px_scale: int,
    layout: tuple[int, int, int, int, int],
) -> None:
    """Thin 1px lines on logical cell boundaries (matches camera viewport inside 64×64)."""
    gw, gh, cell_px, x_off, y_off = layout
    color = (72, 72, 82)
    x0, y0 = x_off * px_scale, y_off * px_scale
    wpx, hpx = gw * cell_px * px_scale, gh * cell_px * px_scale
    for i in range(gw + 1):
        x = x0 + i * cell_px * px_scale
        pygame.draw.line(screen, color, (x, y0), (x, y0 + hpx), 1)
    for j in range(gh + 1):
        y = y0 + j * cell_px * px_scale
        pygame.draw.line(screen, color, (x0, y), (x0 + wpx, y), 1)


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
    st = getattr(obs, "state", None)
    lines = [f"game: {game_id}"]
    if st == GameState.GAME_OVER:
        lines.append("GAME OVER — press R to reset")
    elif st == GameState.WIN:
        lines.append("YOU WIN — press R to reset")
    else:
        lines.append(f"state: {getattr(obs.state, 'name', obs.state)}")
    lines.extend(
        [
        _levels_hud_line(obs),
        f"steps: {steps}",
        f"avail: {getattr(obs, 'available_actions', [])}",
        "",
        "WASD / arrows: 1–4",
        "Space / F: 5",
        "Hover: display + grid coords",
        "Click grid: ACTION6",
        "U / Ctrl+Z / Cmd+Z: 7",
        "R: reset  Q: quit",
        "",
        "Click grid area first so keys go here",
        ]
    )
    for i, line in enumerate(lines):
        if i == 1 and st == GameState.GAME_OVER:
            color = (255, 140, 120)
        elif i == 1 and st == GameState.WIN:
            color = (130, 220, 140)
        else:
            color = (220, 220, 220)
        surf = small.render(line, True, color)
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
    frame_cache: dict[str, Any],
    environment: Any,
    *,
    error_line: str | None = None,
    idle_delay_ms: int = 25,
) -> None:
    raw = getattr(obs, "frame", None) or []
    st = getattr(obs, "state", None)
    # One toolkit step can append several full camera renders (e.g. level change);
    # show only the final frame so the grid matches the live game state.
    if raw:
        frame_cache["layer"] = raw[-1]
        layers = [raw[-1]]
    elif st in (GameState.GAME_OVER, GameState.WIN) and frame_cache.get("layer") is not None:
        # ARCBaseGame.perform_action returns frame=[] for actions after GAME_OVER/WIN; keep last board.
        layers = [frame_cache["layer"]]
    else:
        layers = []
    layout = _camera_display_layout(environment)
    x0 = _FRAME * scale
    screen.fill((40, 40, 40))
    if layers:
        for layer in layers:
            surf = _raster_to_surface(layer, scale)
            screen.blit(surf, (0, 0))
        _draw_grid_lines(screen, scale, layout)
        if hover_xy is not None:
            mx, my = hover_xy
            gw = gh = _FRAME * scale
            if 0 <= mx < gw and 0 <= my < gh:
                gx, gy = _display_xy_from_mouse(mx, my, scale)
                _draw_cell_coord_popover(screen, tip_font, mx, my, gx, gy, scale, environment)
    else:
        if st == GameState.GAME_OVER:
            hint_txt = "GAME OVER — press R to reset"
            hint_color = (255, 140, 120)
        elif st == GameState.WIN:
            hint_txt = "YOU WIN — press R to reset"
            hint_color = (130, 220, 140)
        else:
            hint_txt = "No frame in obs — use ARC_OPERATION_MODE=offline (or include_frame_data off)"
            hint_color = (200, 120, 120)
        hint = small.render(hint_txt, True, hint_color)
        screen.blit(hint, (8, 8))
    _draw_sidebar(screen, small, obs, game_id, steps, x0, error_line=error_line)
    pygame.display.flip()
    if idle_delay_ms > 0:
        pygame.time.delay(idle_delay_ms)


def run_interactive_pygame(environment: Any) -> int:
    """Run until user quits. Returns number of ``step`` calls (excludes ``reset``)."""
    os.environ.setdefault("SDL_VIDEO_HIGHDPI", "1")
    pygame.init()
    try:
        scale = _resolve_cell_scale()
        pygame.display.set_caption("ARC-AGI-3 — human play (pygame)")
        small = pygame.font.Font(None, 22)
        tip_font = pygame.font.Font(None, 26)
        w = _FRAME * scale + _SIDEBAR_W
        h = _FRAME * scale
        screen = pygame.display.set_mode((w, h))

        game_id = getattr(environment.info, "game_id", "?")
        obs = environment.reset()
        if obs is None:
            return 0
        step_count = 0
        hover_xy: tuple[int, int] | None = None
        frame_cache: dict[str, Any] = {"layer": None}

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
                scale,
                hover_xy,
                frame_cache,
                environment,
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
                    if mx < _FRAME * scale and my < _FRAME * scale:
                        dx, dy = _display_xy_from_mouse(mx, my, scale)
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
