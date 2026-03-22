"""Registry GIF capture for pk01–ec01 batch (packing, ladder, planes, echo, traffic, etc.)."""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
from fractions import Fraction
from pathlib import Path
from typing import Any

from arcengine import GameAction, GameState, Level
from env_resolve import full_game_id_for_stem, load_stem_game_py
from gif_common import append_frame_repeats, grid_cell_center_display, offline_arcade
from registry_gif_lib import _cap_gif_frames, _frame_layer0, _StepAbort, safe_env_step

# pk01: per-level placement segments — "d" = domino (2 orth-adjacent clicks), "t" = tromino (3 collinear)
PK01_PLANS: list[list[tuple[str, tuple[int, ...]]]] = [
    [("d", (2, 2, 3, 2)), ("d", (2, 3, 3, 3))],
    [("t", (1, 1, 2, 1, 3, 1)), ("t", (5, 5, 6, 5, 7, 5))],
    [("t", (0, 0, 1, 0, 2, 0)), ("t", (4, 4, 5, 4, 6, 4))],
    [
        ("d", (2, 2, 2, 3)),
        ("d", (3, 2, 3, 3)),
        ("d", (2, 4, 2, 5)),
        ("d", (3, 4, 3, 5)),
        ("t", (4, 3, 5, 3, 6, 3)),
    ],
    [
        ("t", (3, 3, 4, 3, 5, 3)),
        ("d", (2, 4, 2, 5)),
        ("d", (3, 4, 3, 5)),
        ("d", (4, 4, 4, 5)),
        ("d", (5, 4, 5, 5)),
        ("d", (6, 4, 6, 5)),
    ],
]


def _click6(env: Any, gx: int, gy: int) -> Any:
    level = env._game.current_level
    gw, gh = level.grid_size
    cx, cy = grid_cell_center_display(gx, gy, grid_w=gw, grid_h=gh)
    return safe_env_step(env, GameAction.ACTION6, reasoning={}, data={"x": cx, "y": cy})


def _move(env: Any, aid: int) -> Any:
    return safe_env_step(env, _ACTIONS[aid], reasoning={})


_ACTIONS = {
    1: GameAction.ACTION1,
    2: GameAction.ACTION2,
    3: GameAction.ACTION3,
    4: GameAction.ACTION4,
    5: GameAction.ACTION5,
    6: GameAction.ACTION6,
}


def _kv_voltages(r0: int, r1: int, r2: int) -> tuple[Fraction, Fraction]:
    s = r0 + r1 + r2
    if s == 0:
        return Fraction(0), Fraction(0)
    return Fraction(12 * (r1 + r2), s), Fraction(12 * r2, s)


def _kv_bfs_plan(
    r0: int, r1: int, r2: int, t1: Fraction, t2: Fraction
) -> list[int] | None:
    opts = (1, 2, 4)

    def cyc(x: int) -> int:
        i = opts.index(x) if x in opts else 0
        return opts[(i + 1) % 3]

    start = (r0, r1, r2)
    v1s, v2s = _kv_voltages(*start)
    if v1s == t1 and v2s == t2:
        return []

    q: deque[tuple[int, int, int]] = deque([start])
    prev: dict[tuple[int, int, int], tuple[tuple[int, int, int], int] | None] = {
        start: None
    }
    while q:
        a, b, c = q.popleft()
        for act, nxt in (
            (1, (cyc(a), b, c)),
            (2, (a, cyc(b), c)),
            (3, (a, b, cyc(c))),
        ):
            if nxt in prev:
                continue
            prev[nxt] = ((a, b, c), act)
            v1, v2 = _kv_voltages(*nxt)
            if v1 == t1 and v2 == t2:
                out: list[int] = []
                cur = nxt
                while cur != start:
                    p, ac = prev[cur]  # type: ignore[misc]
                    out.append(ac)
                    cur = p  # type: ignore[assignment]
                out.reverse()
                return out
            q.append(nxt)
    return None


def record_pk01_registry_gif(
    game_id: str,
    root: Path,
    *,
    overrides: dict[str, Any] | None = None,
    verbose: bool = False,
    seed: int = 0,
) -> tuple[Any, list]:
    _ = seed
    o = dict(overrides or {})
    max_gif = int(o.get("max_gif_frames", 520))
    hold = int(o.get("pk01_segment_hold_frames", 5))
    target_levels = int(o.get("target_levels", 0))
    mod = load_stem_game_py(game_id, f"{game_id}_registry_pk")
    n_authored = len(mod.levels)
    lc_goal = target_levels if target_levels > 0 else min(4, max(1, n_authored))

    arc = offline_arcade(root)
    env = arc.make(full_game_id_for_stem(game_id), seed=0, render_mode=None)
    res = env.reset()
    images: list = []

    def snap_repeats(times: int) -> None:
        fr = _frame_layer0(res)
        if fr:
            append_frame_repeats(images, fr[0], times)

    snap_repeats(8)
    step_abort = False
    try:
        for _guard in range(80):
            lc = getattr(res, "levels_completed", 0) or 0
            if lc >= lc_goal:
                break
            if res.state in (GameState.WIN, GameState.GAME_OVER):
                break
            li = env._game.level_index
            if li >= len(PK01_PLANS):
                break
            plan = PK01_PLANS[li]
            for seg in plan:
                kind, coords = seg[0], seg[1]
                need_t = kind == "t"
                g = env._game
                if need_t and g._mode_domino:
                    res = safe_env_step(env, GameAction.ACTION5, reasoning={})
                    snap_repeats(hold)
                elif not need_t and not g._mode_domino:
                    res = safe_env_step(env, GameAction.ACTION5, reasoning={})
                    snap_repeats(hold)
                n = len(coords) // 2
                for i in range(n):
                    x, y = coords[2 * i], coords[2 * i + 1]
                    res = _click6(env, x, y)
                    snap_repeats(hold)
            snap_repeats(int(o.get("pk01_level_hold_frames", 18)))
    except _StepAbort as ex:
        step_abort = True
        if verbose:
            print(f"  {game_id}: pk01 step abort ({ex})")

    snap_repeats(12)
    if step_abort and len(images) < 20:
        res = env.reset()
        fr = _frame_layer0(res)
        if fr:
            append_frame_repeats(images, fr[0], 24)

    _cap_gif_frames(images, max_gif)
    if verbose:
        print(f"  {game_id}: pk01 registry GIF, {len(images)} frames")
    return res, images


def record_kv01_registry_gif(
    game_id: str,
    root: Path,
    *,
    overrides: dict[str, Any] | None = None,
    verbose: bool = False,
    seed: int = 0,
) -> tuple[Any, list]:
    _ = seed
    o = dict(overrides or {})
    max_gif = int(o.get("max_gif_frames", 520))
    target_levels = int(o.get("target_levels", 0))
    mod = load_stem_game_py(game_id, f"{game_id}_registry_kv")
    n_authored = len(mod.levels)
    lc_goal = target_levels if target_levels > 0 else min(4, max(1, n_authored))

    arc = offline_arcade(root)
    env = arc.make(full_game_id_for_stem(game_id), seed=0, render_mode=None)
    res = env.reset()
    images: list = []

    def snap_repeats(times: int) -> None:
        fr = _frame_layer0(res)
        if fr:
            append_frame_repeats(images, fr[0], times)

    snap_repeats(8)
    step_abort = False
    try:
        for _guard in range(120):
            lc = getattr(res, "levels_completed", 0) or 0
            if lc >= lc_goal:
                break
            if res.state in (GameState.WIN, GameState.GAME_OVER):
                break
            level = env._game.current_level
            r0 = int(level.get_data("r0"))
            r1 = int(level.get_data("r1"))
            r2 = int(level.get_data("r2"))
            t1 = Fraction(int(level.get_data("t1_num")), int(level.get_data("t1_den")))
            t2 = Fraction(int(level.get_data("t2_num")), int(level.get_data("t2_den")))
            v1, v2 = _kv_voltages(r0, r1, r2)
            if v1 != t1 or v2 != t2:
                res = safe_env_step(env, GameAction.ACTION5, reasoning={})
                snap_repeats(6)
            plan = _kv_bfs_plan(r0, r1, r2, t1, t2)
            if not plan:
                break
            for act in plan:
                res = _move(env, act)
                snap_repeats(4)
            res = safe_env_step(env, GameAction.ACTION5, reasoning={})
            snap_repeats(int(o.get("kv01_level_hold_frames", 20)))
    except _StepAbort as ex:
        step_abort = True
        if verbose:
            print(f"  {game_id}: kv01 step abort ({ex})")

    snap_repeats(12)
    if step_abort and len(images) < 20:
        res = env.reset()
        fr = _frame_layer0(res)
        if fr:
            append_frame_repeats(images, fr[0], 24)

    _cap_gif_frames(images, max_gif)
    if verbose:
        print(f"  {game_id}: kv01 registry GIF, {len(images)} frames")
    return res, images


def _parse_dp_level(level: Level) -> tuple[tuple[int, int], tuple[int, int], set[tuple[int, int]], set[tuple[int, int]]]:
    player = goal = None
    wa: set[tuple[int, int]] = set()
    wb: set[tuple[int, int]] = set()
    for s in level.get_sprites():
        p = (s.x, s.y)
        if "player" in s.tags:
            player = p
        elif "goal" in s.tags:
            goal = p
        elif "wall" in s.tags and "plane_a" in s.tags:
            wa.add(p)
        elif "wall" in s.tags and "plane_b" in s.tags:
            wb.add(p)
    assert player and goal
    return player, goal, wa, wb


def _dp_blocked(
    x: int, y: int, plane_a: bool, wa: set[tuple[int, int]], wb: set[tuple[int, int]]
) -> bool:
    if (x, y) in wa and plane_a:
        return True
    if (x, y) in wb and not plane_a:
        return True
    return False


def _dp_bfs_plan(
    start: tuple[int, int],
    goal: tuple[int, int],
    wa: set[tuple[int, int]],
    wb: set[tuple[int, int]],
    gw: int,
    gh: int,
) -> list[int] | None:
    # state: (x, y, plane_a_bool) — plane_a True means A-plane walls block
    start_s = (start[0], start[1], True)
    q: deque[tuple[int, int, bool]] = deque([start_s])
    prev: dict[tuple[int, int, bool], tuple[tuple[int, int, bool], int] | None] = {
        start_s: None
    }
    while q:
        x, y, pa = q.popleft()
        if (x, y) == goal:
            cur: tuple[int, int, bool] | None = (x, y, pa)
            out: list[int] = []
            while cur is not None and prev[cur] is not None:
                pstate, act = prev[cur]  # type: ignore[misc]
                out.append(act)
                cur = pstate  # type: ignore[assignment]
            out.reverse()
            return out
        # toggle plane
        nxt = (x, y, not pa)
        if nxt not in prev:
            prev[nxt] = ((x, y, pa), 5)
            q.append(nxt)
        for act, (dx, dy) in (
            (1, (0, -1)),
            (2, (0, 1)),
            (3, (-1, 0)),
            (4, (1, 0)),
        ):
            nx, ny = x + dx, y + dy
            if not (0 <= nx < gw and 0 <= ny < gh):
                continue
            if _dp_blocked(nx, ny, pa, wa, wb):
                continue
            nn = (nx, ny, pa)
            if nn not in prev:
                prev[nn] = ((x, y, pa), act)
                q.append(nn)
    return None


def record_dp01_registry_gif(
    game_id: str,
    root: Path,
    *,
    overrides: dict[str, Any] | None = None,
    verbose: bool = False,
    seed: int = 0,
) -> tuple[Any, list]:
    _ = seed
    o = dict(overrides or {})
    max_gif = int(o.get("max_gif_frames", 520))
    target_levels = int(o.get("target_levels", 0))
    mod = load_stem_game_py(game_id, f"{game_id}_registry_dp")
    n_authored = len(mod.levels)
    lc_goal = target_levels if target_levels > 0 else min(4, max(1, n_authored))

    arc = offline_arcade(root)
    env = arc.make(full_game_id_for_stem(game_id), seed=0, render_mode=None)
    res = env.reset()
    images: list = []

    def snap_repeats(times: int) -> None:
        fr = _frame_layer0(res)
        if fr:
            append_frame_repeats(images, fr[0], times)

    snap_repeats(8)
    step_abort = False
    try:
        for _guard in range(100):
            lc = getattr(res, "levels_completed", 0) or 0
            if lc >= lc_goal:
                break
            if res.state in (GameState.WIN, GameState.GAME_OVER):
                break
            level = env._game.current_level
            gw, gh = level.grid_size
            st, gl, wa, wb = _parse_dp_level(level)
            plan = _dp_bfs_plan(st, gl, wa, wb, gw, gh)
            if not plan:
                break
            for act in plan:
                res = _move(env, act)
                snap_repeats(3)
            snap_repeats(int(o.get("dp01_level_hold_frames", 16)))
    except _StepAbort as ex:
        step_abort = True
        if verbose:
            print(f"  {game_id}: dp01 step abort ({ex})")

    snap_repeats(12)
    if step_abort and len(images) < 20:
        res = env.reset()
        fr = _frame_layer0(res)
        if fr:
            append_frame_repeats(images, fr[0], 24)

    _cap_gif_frames(images, max_gif)
    if verbose:
        print(f"  {game_id}: dp01 registry GIF, {len(images)} frames")
    return res, images


def _parse_ec_level(
    level: Level,
) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int], set[tuple[int, int]]]:
    px = py = ex = ey = gx = gy = 0
    walls: set[tuple[int, int]] = set()
    for s in level.get_sprites():
        p = (s.x, s.y)
        if "player" in s.tags:
            px, py = p
        elif "echo" in s.tags:
            ex, ey = p
        elif "goal" in s.tags:
            gx, gy = p
        elif "wall" in s.tags:
            walls.add(p)
    return (px, py), (ex, ey), (gx, gy), walls


def _ec_wall_at(
    walls: set[tuple[int, int]], x: int, y: int, gw: int, gh: int
) -> bool:
    if not (0 <= x < gw and 0 <= y < gh):
        return True
    return (x, y) in walls


def _ec_bfs_plan(
    p0: tuple[int, int],
    e0: tuple[int, int],
    goal: tuple[int, int],
    walls: set[tuple[int, int]],
    gw: int,
    gh: int,
) -> list[int] | None:
    q: deque[tuple[int, int, int, int]] = deque([(*p0, *e0)])
    prev: dict[tuple[int, int, int, int], tuple[tuple[int, int, int, int], int] | None] = {
        (*p0, *e0): None
    }
    while q:
        px, py, ex, ey = q.popleft()
        if (px, py) == goal:
            cur: tuple[int, int, int, int] | None = (px, py, ex, ey)
            out: list[int] = []
            while cur is not None and prev[cur] is not None:
                pst, act = prev[cur]  # type: ignore[misc]
                out.append(act)
                cur = pst  # type: ignore[assignment]
            out.reverse()
            return out
        for act, (dx, dy) in (
            (1, (0, -1)),
            (2, (0, 1)),
            (3, (-1, 0)),
            (4, (1, 0)),
        ):
            gdx = -dx
            enx, eny = ex + gdx, ey + dy
            if _ec_wall_at(walls, enx, eny, gw, gh):
                continue
            nx, ny = px + dx, py + dy
            if _ec_wall_at(walls, nx, ny, gw, gh):
                continue
            nn = (nx, ny, enx, eny)
            if nn not in prev:
                prev[nn] = ((px, py, ex, ey), act)
                q.append(nn)
    return None


def record_ec01_registry_gif(
    game_id: str,
    root: Path,
    *,
    overrides: dict[str, Any] | None = None,
    verbose: bool = False,
    seed: int = 0,
) -> tuple[Any, list]:
    _ = seed
    o = dict(overrides or {})
    max_gif = int(o.get("max_gif_frames", 520))
    target_levels = int(o.get("target_levels", 0))
    mod = load_stem_game_py(game_id, f"{game_id}_registry_ec")
    n_authored = len(mod.levels)
    lc_goal = target_levels if target_levels > 0 else min(4, max(1, n_authored))

    arc = offline_arcade(root)
    env = arc.make(full_game_id_for_stem(game_id), seed=0, render_mode=None)
    res = env.reset()
    images: list = []

    def snap_repeats(times: int) -> None:
        fr = _frame_layer0(res)
        if fr:
            append_frame_repeats(images, fr[0], times)

    snap_repeats(8)
    step_abort = False
    try:
        for _guard in range(100):
            lc = getattr(res, "levels_completed", 0) or 0
            if lc >= lc_goal:
                break
            if res.state in (GameState.WIN, GameState.GAME_OVER):
                break
            level = env._game.current_level
            gw, gh = level.grid_size
            p0, e0, gl, walls = _parse_ec_level(level)
            plan = _ec_bfs_plan(p0, e0, gl, walls, gw, gh)
            if not plan:
                break
            for act in plan:
                res = _move(env, act)
                snap_repeats(3)
            snap_repeats(int(o.get("ec01_level_hold_frames", 16)))
    except _StepAbort as ex:
        step_abort = True
        if verbose:
            print(f"  {game_id}: ec01 step abort ({ex})")

    snap_repeats(12)
    if step_abort and len(images) < 20:
        res = env.reset()
        fr = _frame_layer0(res)
        if fr:
            append_frame_repeats(images, fr[0], 24)

    _cap_gif_frames(images, max_gif)
    if verbose:
        print(f"  {game_id}: ec01 registry GIF, {len(images)} frames")
    return res, images


def _parse_tf_level(level: Level) -> tuple[tuple[int, int], tuple[int, int], set[tuple[int, int]]]:
    px = py = gx = gy = 0
    cross: set[tuple[int, int]] = set()
    for s in level.get_sprites():
        p = (s.x, s.y)
        if "player" in s.tags:
            px, py = p
        elif "goal" in s.tags:
            gx, gy = p
        elif "crossing" in s.tags:
            cross.add(p)
    return (px, py), (gx, gy), cross


def record_tf01_registry_gif(
    game_id: str,
    root: Path,
    *,
    overrides: dict[str, Any] | None = None,
    verbose: bool = False,
    seed: int = 0,
) -> tuple[Any, list]:
    _ = seed
    o = dict(overrides or {})
    max_gif = int(o.get("max_gif_frames", 520))
    target_levels = int(o.get("target_levels", 0))
    mod = load_stem_game_py(game_id, f"{game_id}_registry_tf")
    n_authored = len(mod.levels)
    lc_goal = target_levels if target_levels > 0 else min(4, max(1, n_authored))

    arc = offline_arcade(root)
    env = arc.make(full_game_id_for_stem(game_id), seed=0, render_mode=None)
    res = env.reset()
    images: list = []

    def snap_repeats(times: int) -> None:
        fr = _frame_layer0(res)
        if fr:
            append_frame_repeats(images, fr[0], times)

    snap_repeats(8)
    step_abort = False
    try:
        for _guard in range(100):
            lc = getattr(res, "levels_completed", 0) or 0
            if lc >= lc_goal:
                break
            if res.state in (GameState.WIN, GameState.GAME_OVER):
                break
            level = env._game.current_level
            gw, gh = level.grid_size
            st, gl, cr = _parse_tf_level(level)
            t0 = int(getattr(env._game, "_t", 0))
            plan2 = _tf_bfs_plan_from_t(st, gl, cr, gw, gh, t0 % 4)
            if not plan2:
                break
            for act in plan2:
                res = _move(env, act)
                snap_repeats(3)
            snap_repeats(int(o.get("tf01_level_hold_frames", 14)))
    except _StepAbort as ex:
        step_abort = True
        if verbose:
            print(f"  {game_id}: tf01 step abort ({ex})")

    snap_repeats(12)
    if step_abort and len(images) < 20:
        res = env.reset()
        fr = _frame_layer0(res)
        if fr:
            append_frame_repeats(images, fr[0], 24)

    _cap_gif_frames(images, max_gif)
    if verbose:
        print(f"  {game_id}: tf01 registry GIF, {len(images)} frames")
    return res, images


def _tf_bfs_plan_from_t(
    start: tuple[int, int],
    goal: tuple[int, int],
    cross: set[tuple[int, int]],
    gw: int,
    gh: int,
    t0: int,
) -> list[int] | None:
    q: deque[tuple[int, int, int]] = deque([(*start, t0)])
    prev: dict[tuple[int, int, int], tuple[tuple[int, int, int], int] | None] = {
        (*start, t0): None
    }
    while q:
        x, y, t = q.popleft()
        if (x, y) == goal:
            cur: tuple[int, int, int] | None = (x, y, t)
            out: list[int] = []
            while cur is not None and prev[cur] is not None:
                pst, act = prev[cur]  # type: ignore[misc]
                out.append(act)
                cur = pst  # type: ignore[assignment]
            out.reverse()
            return out
        for act, (dx, dy) in (
            (1, (0, -1)),
            (2, (0, 1)),
            (3, (-1, 0)),
            (4, (1, 0)),
        ):
            nx, ny = x + dx, y + dy
            if not (0 <= nx < gw and 0 <= ny < gh):
                continue
            if (nx, ny) in cross and (t % 4) >= 2:
                continue
            nt = t + 1
            nn = (nx, ny, nt)
            if nn not in prev:
                prev[nn] = ((x, y, t), act)
                q.append(nn)
    return None


def _rot_cw(g: int, x: int, y: int) -> tuple[int, int]:
    return y, g - 1 - x


def _wr01_parse(level: Level) -> tuple[int, int, tuple[int, int], tuple[int, int], set[tuple[int, int]]]:
    every = int(level.get_data("rotate_every") or 10)
    brace = int(level.get_data("brace_budget") or 2)
    px = py = gx = gy = 0
    walls: set[tuple[int, int]] = set()
    for s in level.get_sprites():
        p = (s.x, s.y)
        if "player" in s.tags:
            px, py = p
        elif "goal" in s.tags:
            gx, gy = p
        elif "wall" in s.tags:
            walls.add(p)
    return every, brace, (px, py), (gx, gy), walls


def _wr01_step_state(
    state: tuple[int, int, int, int, frozenset, int, int, bool],
    action: int,
    g: int,
    every: int,
) -> tuple[tuple[int, int, int, int, frozenset, int, int, bool] | None, bool]:
    """Returns (new_state, moved) or (None, False) if invalid. action 1-4 move, 5 brace."""
    px, py, gx, gy, wf, sub, br, sk = state
    walls = set(wf)

    if action == 5:
        if br <= 0:
            return None, False
        return (px, py, gx, gy, wf, sub, br - 1, True), False  # brace: skip next rot, no sub++

    dx, dy = 0, 0
    if action == 1:
        dy = -1
    elif action == 2:
        dy = 1
    elif action == 3:
        dx = -1
    elif action == 4:
        dx = 1
    else:
        return None, False

    nx, ny = px + dx, py + dy
    if not (0 <= nx < g and 0 <= ny < g):
        return None, False
    if (nx, ny) in walls:
        return None, False

    px, py = nx, ny
    sub += 1
    if sub % every == 0:
        if sk:
            sk = False
        else:
            px, py = _rot_cw(g, px, py)
            gx, gy = _rot_cw(g, gx, gy)
            walls = {_rot_cw(g, wx, wy) for wx, wy in walls}
            wf = frozenset(walls)
    return (px, py, gx, gy, wf, sub, br, sk), True


def _wr01_bfs_plan(
    every: int,
    brace: int,
    p0: tuple[int, int],
    g0: tuple[int, int],
    walls: set[tuple[int, int]],
    g: int,
) -> list[int] | None:
    wf0 = frozenset(walls)
    start = (*p0, *g0, wf0, 0, brace, False)
    q: deque[tuple[Any, ...]] = deque([start])
    prev: dict[tuple[Any, ...], tuple[tuple[Any, ...], int] | None] = {start: None}
    cap = 180_000
    nodes = 0
    while q and nodes < cap:
        state = q.popleft()
        nodes += 1
        px, py, gx, gy = state[0], state[1], state[2], state[3]
        if (px, py) == (gx, gy):
            out: list[int] = []
            cur = state
            while prev[cur] is not None:
                pst, act = prev[cur]  # type: ignore[misc]
                out.append(act)
                cur = pst  # type: ignore[assignment]
            out.reverse()
            return out
        for act in (1, 2, 3, 4, 5):
            nst = _wr01_step_state(
                (state[0], state[1], state[2], state[3], state[4], state[5], state[6], state[7]),
                act,
                g,
                every,
            )[0]
            if nst is None:
                continue
            if nst not in prev:
                prev[nst] = (state, act)
                q.append(nst)
    return None


def record_wr01_registry_gif(
    game_id: str,
    root: Path,
    *,
    overrides: dict[str, Any] | None = None,
    verbose: bool = False,
    seed: int = 0,
) -> tuple[Any, list]:
    _ = seed
    o = dict(overrides or {})
    max_gif = int(o.get("max_gif_frames", 520))
    target_levels = int(o.get("target_levels", 0))
    mod = load_stem_game_py(game_id, f"{game_id}_registry_wr")
    n_authored = len(mod.levels)
    lc_goal = target_levels if target_levels > 0 else min(3, max(1, n_authored))

    arc = offline_arcade(root)
    env = arc.make(full_game_id_for_stem(game_id), seed=0, render_mode=None)
    res = env.reset()
    images: list = []

    def snap_repeats(times: int) -> None:
        fr = _frame_layer0(res)
        if fr:
            append_frame_repeats(images, fr[0], times)

    snap_repeats(8)
    step_abort = False
    try:
        for _guard in range(80):
            lc = getattr(res, "levels_completed", 0) or 0
            if lc >= lc_goal:
                break
            if res.state in (GameState.WIN, GameState.GAME_OVER):
                break
            level = env._game.current_level
            gw, _ = level.grid_size
            every, br0, p0, g0, walls = _wr01_parse(level)
            plan = _wr01_bfs_plan(every, br0, p0, g0, walls, gw)
            if not plan:
                break
            for act in plan:
                res = _move(env, act)
                snap_repeats(3)
            snap_repeats(int(o.get("wr01_level_hold_frames", 16)))
    except _StepAbort as ex:
        step_abort = True
        if verbose:
            print(f"  {game_id}: wr01 step abort ({ex})")

    snap_repeats(12)
    if step_abort and len(images) < 20:
        res = env.reset()
        fr = _frame_layer0(res)
        if fr:
            append_frame_repeats(images, fr[0], 24)

    _cap_gif_frames(images, max_gif)
    if verbose:
        print(f"  {game_id}: wr01 registry GIF, {len(images)} frames")
    return res, images


def record_df01_registry_gif(
    game_id: str,
    root: Path,
    *,
    overrides: dict[str, Any] | None = None,
    verbose: bool = False,
    seed: int = 0,
) -> tuple[Any, list]:
    _ = seed
    o = dict(overrides or {})
    max_gif = int(o.get("max_gif_frames", 520))
    target_levels = int(o.get("target_levels", 0))
    from registry_gif_lib import bfs_next_action, goal_positions_set

    mod = load_stem_game_py(game_id, f"{game_id}_registry_df")
    n_authored = len(mod.levels)
    lc_goal = target_levels if target_levels > 0 else min(3, max(1, n_authored))

    arc = offline_arcade(root)
    env = arc.make(full_game_id_for_stem(game_id), seed=0, render_mode=None)
    res = env.reset()
    images: list = []

    def snap_repeats(times: int) -> None:
        fr = _frame_layer0(res)
        if fr:
            append_frame_repeats(images, fr[0], times)

    snap_repeats(8)
    try:
        for _guard in range(200):
            lc = getattr(res, "levels_completed", 0) or 0
            if lc >= lc_goal:
                break
            if res.state in (GameState.WIN, GameState.GAME_OVER):
                break
            level = env._game.current_level
            res = _move(env, 1)
            snap_repeats(2)
            res = _move(env, 2)
            snap_repeats(2)
            gw, gh = level.grid_size
            res = _click6(env, gw // 2, gh // 2)
            snap_repeats(5)
            lc0 = lc
            for _ in range(160):
                lc2 = getattr(res, "levels_completed", 0) or 0
                if lc2 > lc0 or res.state in (GameState.WIN, GameState.GAME_OVER):
                    break
                level = env._game.current_level
                goals = goal_positions_set(level)
                pl = level.get_sprites_by_tag("player")[0]
                act = bfs_next_action(level, (pl.x, pl.y), goals)
                if act is None:
                    break
                res = safe_env_step(env, act, reasoning={})
                snap_repeats(2)
            snap_repeats(int(o.get("df01_level_hold_frames", 14)))
    except _StepAbort as ex:
        if verbose:
            print(f"  {game_id}: df01 step abort ({ex})")

    snap_repeats(12)
    _cap_gif_frames(images, max_gif)
    if verbose:
        print(f"  {game_id}: df01 registry GIF, {len(images)} frames")
    return res, images


def record_rn01_registry_gif(
    game_id: str,
    root: Path,
    *,
    overrides: dict[str, Any] | None = None,
    verbose: bool = False,
    seed: int = 0,
) -> tuple[Any, list]:
    _ = seed
    o = dict(overrides or {})
    max_gif = int(o.get("max_gif_frames", 520))
    target_levels = int(o.get("target_levels", 0))
    from registry_gif_lib import bfs_next_action, goal_positions_set

    mod = load_stem_game_py(game_id, f"{game_id}_registry_rn")
    n_authored = len(mod.levels)
    lc_goal = target_levels if target_levels > 0 else min(4, max(1, n_authored))

    arc = offline_arcade(root)
    env = arc.make(full_game_id_for_stem(game_id), seed=0, render_mode=None)
    res = env.reset()
    images: list = []

    def snap_repeats(times: int) -> None:
        fr = _frame_layer0(res)
        if fr:
            append_frame_repeats(images, fr[0], times)

    snap_repeats(8)

    def anchor_pair_click() -> None:
        nonlocal res
        level = env._game.current_level
        anchors = [(s.x, s.y) for s in level.get_sprites_by_tag("anchor")]
        if len(anchors) >= 2:
            (ax, ay), (bx, by) = anchors[0], anchors[1]
            res = _click6(env, ax, ay)
            snap_repeats(4)
            res = _click6(env, bx, by)
            snap_repeats(5)

    try:
        for _guard in range(100):
            lc = getattr(res, "levels_completed", 0) or 0
            if lc >= lc_goal:
                break
            if res.state in (GameState.WIN, GameState.GAME_OVER):
                break
            anchor_pair_click()
            lc0 = lc
            for _ in range(100):
                lc2 = getattr(res, "levels_completed", 0) or 0
                if lc2 > lc0:
                    break
                level = env._game.current_level
                goals = goal_positions_set(level)
                pl = level.get_sprites_by_tag("player")[0]
                act = bfs_next_action(level, (pl.x, pl.y), goals)
                if act is None:
                    break
                res = safe_env_step(env, act, reasoning={})
                snap_repeats(2)
            snap_repeats(int(o.get("rn01_level_hold_frames", 14)))
    except _StepAbort as ex:
        if verbose:
            print(f"  {game_id}: rn01 step abort ({ex})")

    snap_repeats(12)
    _cap_gif_frames(images, max_gif)
    if verbose:
        print(f"  {game_id}: rn01 registry GIF, {len(images)} frames")
    return res, images


def record_sc01_registry_gif(
    game_id: str,
    root: Path,
    *,
    overrides: dict[str, Any] | None = None,
    verbose: bool = False,
    seed: int = 0,
) -> tuple[Any, list]:
    _ = seed
    o = dict(overrides or {})
    max_gif = int(o.get("max_gif_frames", 520))
    target_levels = int(o.get("target_levels", 0))
    from registry_gif_lib import bfs_next_action, goal_positions_set

    mod = load_stem_game_py(game_id, f"{game_id}_registry_sc")
    n_authored = len(mod.levels)
    lc_goal = target_levels if target_levels > 0 else min(3, max(1, n_authored))

    arc = offline_arcade(root)
    env = arc.make(full_game_id_for_stem(game_id), seed=0, render_mode=None)
    res = env.reset()
    images: list = []

    def snap_repeats(times: int) -> None:
        fr = _frame_layer0(res)
        if fr:
            append_frame_repeats(images, fr[0], times)

    snap_repeats(8)
    try:
        for _guard in range(120):
            lc = getattr(res, "levels_completed", 0) or 0
            if lc >= lc_goal:
                break
            if res.state in (GameState.WIN, GameState.GAME_OVER):
                break
            # mask pulse then greedily walk
            res = safe_env_step(env, GameAction.ACTION5, reasoning={})
            snap_repeats(5)
            for _ in range(100):
                if res.state == GameState.GAME_OVER:
                    break
                level = env._game.current_level
                goals = goal_positions_set(level)
                pl = level.get_sprites_by_tag("player")[0]
                act = bfs_next_action(level, (pl.x, pl.y), goals)
                if act is None:
                    break
                res = safe_env_step(env, act, reasoning={})
                snap_repeats(2)
                if getattr(res, "levels_completed", 0) or 0 > lc:
                    break
            snap_repeats(int(o.get("sc01_level_hold_frames", 14)))
    except _StepAbort as ex:
        if verbose:
            print(f"  {game_id}: sc01 step abort ({ex})")

    snap_repeats(12)
    _cap_gif_frames(images, max_gif)
    if verbose:
        print(f"  {game_id}: sc01 registry GIF, {len(images)} frames")
    return res, images


def record_au01_registry_gif(
    game_id: str,
    root: Path,
    *,
    overrides: dict[str, Any] | None = None,
    verbose: bool = False,
    seed: int = 0,
) -> tuple[Any, list]:
    _ = seed
    o = dict(overrides or {})
    max_gif = int(o.get("max_gif_frames", 520))
    from registry_gif_lib import bfs_next_action, goal_positions_set

    load_stem_game_py(game_id, f"{game_id}_registry_au")

    arc = offline_arcade(root)
    env = arc.make(full_game_id_for_stem(game_id), seed=0, render_mode=None)
    res = env.reset()
    images: list = []

    def snap_repeats(times: int) -> None:
        fr = _frame_layer0(res)
        if fr:
            append_frame_repeats(images, fr[0], times)

    snap_repeats(8)
    try:
        for _guard in range(500):
            if res.state == GameState.GAME_OVER:
                snap_repeats(20)
                break
            if env._game.level_index >= 1:
                res = _move(env, 1)
                snap_repeats(1)
                res = _move(env, 2)
                snap_repeats(1)
                continue
            level = env._game.current_level
            goals = goal_positions_set(level)
            pl = level.get_sprites_by_tag("player")[0]
            act = bfs_next_action(level, (pl.x, pl.y), goals)
            if act is None:
                break
            res = safe_env_step(env, act, reasoning={})
            snap_repeats(2)
    except _StepAbort as ex:
        if verbose:
            print(f"  {game_id}: au01 step abort ({ex})")

    snap_repeats(12)
    _cap_gif_frames(images, max_gif)
    if verbose:
        print(f"  {game_id}: au01 registry GIF, {len(images)} frames")
    return res, images


def record_cf01_registry_gif(
    game_id: str,
    root: Path,
    *,
    overrides: dict[str, Any] | None = None,
    verbose: bool = False,
    seed: int = 0,
) -> tuple[Any, list]:
    _ = seed
    o = dict(overrides or {})
    max_gif = int(o.get("max_gif_frames", 520))
    from registry_gif_lib import bfs_next_action, goal_positions_set

    load_stem_game_py(game_id, f"{game_id}_registry_cf")

    arc = offline_arcade(root)
    env = arc.make(full_game_id_for_stem(game_id), seed=0, render_mode=None)
    res = env.reset()
    images: list = []

    def snap_repeats(times: int) -> None:
        fr = _frame_layer0(res)
        if fr:
            append_frame_repeats(images, fr[0], times)

    snap_repeats(8)
    try:
        for _guard in range(400):
            if res.state == GameState.GAME_OVER:
                snap_repeats(18)
                break
            if env._game.level_index >= 1:
                res = _move(env, 4)
                snap_repeats(2)
                res = _move(env, 3)
                snap_repeats(2)
                res = _move(env, 4)
                snap_repeats(2)
                continue
            level = env._game.current_level
            goals = goal_positions_set(level)
            pl = level.get_sprites_by_tag("player")[0]
            act = bfs_next_action(level, (pl.x, pl.y), goals)
            if act is None:
                break
            res = safe_env_step(env, act, reasoning={})
            snap_repeats(2)
    except _StepAbort as ex:
        if verbose:
            print(f"  {game_id}: cf01 step abort ({ex})")

    snap_repeats(12)
    _cap_gif_frames(images, max_gif)
    if verbose:
        print(f"  {game_id}: cf01 registry GIF, {len(images)} frames")
    return res, images


def record_ep01_registry_gif(
    game_id: str,
    root: Path,
    *,
    overrides: dict[str, Any] | None = None,
    verbose: bool = False,
    seed: int = 0,
) -> tuple[Any, list]:
    _ = seed
    o = dict(overrides or {})
    max_gif = int(o.get("max_gif_frames", 520))
    from registry_gif_lib import bfs_next_action, goal_positions_set

    load_stem_game_py(game_id, f"{game_id}_registry_ep")

    arc = offline_arcade(root)
    env = arc.make(full_game_id_for_stem(game_id), seed=0, render_mode=None)
    res = env.reset()
    images: list = []

    def snap_repeats(times: int) -> None:
        fr = _frame_layer0(res)
        if fr:
            append_frame_repeats(images, fr[0], times)

    snap_repeats(8)
    burn = False
    try:
        for _guard in range(500):
            if res.state == GameState.GAME_OVER:
                snap_repeats(18)
                break
            if env._game.level_index >= 1:
                burn = True
            if burn:
                res = _move(env, 4)
                snap_repeats(1)
                res = _move(env, 3)
                snap_repeats(1)
                continue
            level = env._game.current_level
            goals = goal_positions_set(level)
            pl = level.get_sprites_by_tag("player")[0]
            act = bfs_next_action(level, (pl.x, pl.y), goals)
            if act is None:
                break
            res = safe_env_step(env, act, reasoning={})
            snap_repeats(2)
    except _StepAbort as ex:
        if verbose:
            print(f"  {game_id}: ep01 step abort ({ex})")

    snap_repeats(12)
    _cap_gif_frames(images, max_gif)
    if verbose:
        print(f"  {game_id}: ep01 registry GIF, {len(images)} frames")
    return res, images


PK_EC_RECORDERS: dict[str, Callable[..., tuple[Any, list]]] = {
    "pk01": record_pk01_registry_gif,
    "kv01": record_kv01_registry_gif,
    "wr01": record_wr01_registry_gif,
    "dp01": record_dp01_registry_gif,
    "df01": record_df01_registry_gif,
    "rn01": record_rn01_registry_gif,
    "sc01": record_sc01_registry_gif,
    "au01": record_au01_registry_gif,
    "cf01": record_cf01_registry_gif,
    "ep01": record_ep01_registry_gif,
    "tf01": record_tf01_registry_gif,
    "ec01": record_ec01_registry_gif,
}
