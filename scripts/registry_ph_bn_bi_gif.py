"""Registry GIF recorders for ph03 (field XOR + clicks), bn03 (beacon + flag), bi01 (bishop slide)."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from arcengine import GameAction, Level
from env_resolve import full_game_id_for_stem, load_stem_game_py
from gif_common import append_frame_repeats, grid_cell_center_display, offline_arcade
from registry_gif_lib import _cap_gif_frames, safe_env_step

Ortho = tuple[tuple[int, int], ...]
ORTH: Ortho = ((0, 1), (0, -1), (1, 0), (-1, 0))

# bi01: (dx, dy, action_num) NW, NE, SW, SE
BI_DIAG: tuple[tuple[int, int, int], ...] = (
    (-1, -1, 1),
    (1, -1, 2),
    (-1, 1, 3),
    (1, 1, 4),
)

# bn03 cardinal movement (matches GameAction ACTION1–4)
BN_CARD: tuple[tuple[int, int, int], ...] = (
    (0, -1, 1),
    (0, 1, 2),
    (-1, 0, 3),
    (1, 0, 4),
)

_PUSH_ACTION: dict[int, GameAction] = {
    1: GameAction.ACTION1,
    2: GameAction.ACTION2,
    3: GameAction.ACTION3,
    4: GameAction.ACTION4,
}


def _frame_layer0(res: Any) -> list:
    return getattr(res, "frame", None) or []


# --- ph03 offline simulation ---


def _ph03_parse_level(
    level: Level,
) -> tuple[
    set[tuple[int, int]],
    set[tuple[int, int]],
    dict[tuple[int, int], int],
    int,
    int,
    int,
    int,
]:
    walls: set[tuple[int, int]] = set()
    marks: set[tuple[int, int]] = set()
    for sp in level.get_sprites():
        t = set(sp.tags)
        if "wall" in t:
            walls.add((sp.x, sp.y))
        if "mark" in t:
            marks.add((sp.x, sp.y))
    raw = level.get_data("target") or []
    target: dict[tuple[int, int], int] = {}
    for row in raw:
        x, y, v = int(row[0]), int(row[1]), int(row[2])
        target[(x, y)] = v
    max_blur = int(level.get_data("max_blur") or 40)
    gw, gh = level.grid_size
    diff = int(level.get_data("difficulty") or 1)
    return walls, marks, target, max_blur, gw, gh, diff


def _ph03_apply_step(
    g: list[list[int]],
    walls: set[tuple[int, int]],
    gw: int,
    gh: int,
) -> None:
    old = [[g[x][y] for y in range(gh)] for x in range(gw)]
    for y in range(gh):
        for x in range(gw):
            if (x, y) in walls:
                continue
            acc = old[x][y]
            for dx, dy in ORTH:
                nx, ny = x + dx, y + dy
                if 0 <= nx < gw and 0 <= ny < gh:
                    acc ^= old[nx][ny]
            g[x][y] = acc % 4


def _ph03_win(g: list[list[int]], target: dict[tuple[int, int], int]) -> bool:
    return all(g[x][y] == v for (x, y), v in target.items())


def _ph03_grid_key(g: list[list[int]], gw: int, gh: int) -> tuple[int, ...]:
    out: list[int] = []
    for x in range(gw):
        for y in range(gh):
            out.append(g[x][y])
    return tuple(out)


def _ph03_inc_candidates(
    walls: set[tuple[int, int]],
    target: dict[tuple[int, int], int],
    marks: set[tuple[int, int]],
    gw: int,
    gh: int,
    *,
    wide: bool = False,
) -> list[tuple[int, int]]:
    s: set[tuple[int, int]] = set(target) | set(marks)
    if wide:
        for x, y in list(s):
            for dx, dy in ORTH:
                nx, ny = x + dx, y + dy
                if 0 <= nx < gw and 0 <= ny < gh:
                    s.add((nx, ny))
    return sorted((x, y) for x, y in s if (x, y) not in walls)


def _ph03_bfs_plan(level: Level, *, max_states: int = 50_000) -> list[Literal["S"] | tuple[str, int, int]] | None:
    walls, marks, target, max_blur, gw, gh, _ = _ph03_parse_level(level)
    g0 = [[0 for _ in range(gh)] for _ in range(gw)]
    if _ph03_win(g0, target):
        return []

    for wide in (False, True):
        inc_cells = _ph03_inc_candidates(walls, target, marks, gw, gh, wide=wide)
        if not inc_cells:
            inc_cells = [(x, y) for x in range(gw) for y in range(gh) if (x, y) not in walls]
        plan = _ph03_bfs_plan_inner(
            walls,
            target,
            max_blur,
            gw,
            gh,
            g0,
            inc_cells,
            max_states=max_states,
        )
        if plan is not None:
            return plan
    return None


def _ph03_bfs_plan_inner(
    walls: set[tuple[int, int]],
    target: dict[tuple[int, int], int],
    max_blur: int,
    gw: int,
    gh: int,
    g0: list[list[int]],
    inc_cells: list[tuple[int, int]],
    *,
    max_states: int,
) -> list[Literal["S"] | tuple[str, int, int]] | None:

    start_key: tuple[tuple[int, ...], int] = (_ph03_grid_key(g0, gw, gh), max_blur)
    q: deque[tuple[list[list[int]], int]] = deque([(g0, max_blur)])
    parent: dict[
        tuple[tuple[int, ...], int],
        tuple[tuple[tuple[int, ...], int], str, tuple[int, ...]],
    ] = {start_key: (start_key, "", ())}
    seen: set[tuple[tuple[int, ...], int]] = {start_key}
    nodes = 0

    while q and nodes < max_states:
        g, blur = q.popleft()
        nodes += 1
        if _ph03_win(g, target):
            path: list[Literal["S"] | tuple[str, int, int]] = []
            k = (_ph03_grid_key(g, gw, gh), blur)
            while k != start_key:
                pk, op, extra = parent[k]
                if op == "S":
                    path.append("S")
                elif op == "I":
                    path.append(("I", extra[0], extra[1]))
                k = pk
            path.reverse()
            return path

        if blur > 0:
            g2 = [[g[x][y] for y in range(gh)] for x in range(gw)]
            _ph03_apply_step(g2, walls, gw, gh)
            b2 = blur - 1
            k2 = (_ph03_grid_key(g2, gw, gh), b2)
            if k2 not in seen:
                seen.add(k2)
                parent[k2] = ((_ph03_grid_key(g, gw, gh), blur), "S", ())
                q.append((g2, b2))

        for x, y in inc_cells:
            g2 = [[g[i][j] for j in range(gh)] for i in range(gw)]
            if (x, y) in walls:
                continue
            g2[x][y] = (g2[x][y] + 1) % 4
            k2 = (_ph03_grid_key(g2, gw, gh), blur)
            if k2 not in seen:
                seen.add(k2)
                parent[k2] = ((_ph03_grid_key(g, gw, gh), blur), "I", (x, y))
                q.append((g2, blur))

    return None


def record_ph03_registry_gif(
    game_id: str,
    root: Path,
    *,
    overrides: dict[str, Any] | None = None,
    verbose: bool = False,
    seed: int = 0,
) -> tuple[Any, list]:
    _ = seed
    o = dict(overrides or {})
    target_levels = int(o.get("target_levels", 0))
    max_gif = int(o.get("max_gif_frames", 900))
    level_hold = int(o.get("ph_level_hold_frames", 16))
    fail_open = bool(o.get("ph_fail_opening", True))

    mod = load_stem_game_py(game_id, f"{game_id}_registry_ph")
    level_defs: list = mod.levels
    n_authored = len(level_defs)
    L = target_levels if target_levels > 0 else min(5, max(1, n_authored))

    arc = offline_arcade(root)
    env = arc.make(full_game_id_for_stem(game_id), seed=0, render_mode=None)
    res = env.reset()
    images: list = []

    def snap_repeats(times: int) -> None:
        fr = _frame_layer0(res)
        if fr:
            append_frame_repeats(images, fr[0], times)

    snap_repeats(8)

    def step_ph(act: GameAction, *, data: dict | None = None) -> None:
        nonlocal res
        res = safe_env_step(env, act, reasoning={}, data=data or {})
        snap_repeats(1)
        if act == GameAction.ACTION6:
            for _ in range(6):
                fr = _frame_layer0(res)
                if fr:
                    append_frame_repeats(images, fr[0], 1)

    if fail_open:
        _, _, _, mb0, _, _, _ = _ph03_parse_level(level_defs[0])
        for _i in range(mb0 + 1):
            step_ph(GameAction.ACTION5)
        snap_repeats(14)
        res = env.reset()
        snap_repeats(10)

    for li in range(L):
        lvl = level_defs[li]
        plan = _ph03_bfs_plan(lvl)
        if plan is None:
            raise RuntimeError(f"{game_id}: level {li} has no ph03 BFS plan for registry GIF")
        for op in plan:
            if op == "S":
                step_ph(GameAction.ACTION5)
            else:
                _, gx, gy = op
                cx, cy = grid_cell_center_display(gx, gy, grid_w=lvl.grid_size[0], grid_h=lvl.grid_size[1])
                step_ph(GameAction.ACTION6, data={"x": cx, "y": cy})
        snap_repeats(level_hold)

    snap_repeats(12)
    _cap_gif_frames(images, max_gif)
    if verbose:
        print(f"  {game_id}: ph03 registry GIF, {L} levels, {len(images)} frames")
    return res, images


# --- bn03 offline simulation ---


def _bn_parse(
    level: Level,
) -> tuple[set[tuple[int, int]], tuple[int, int], int, int, int, int, int]:
    walls: set[tuple[int, int]] = set()
    player: tuple[int, int] = (0, 0)
    for sp in level.get_sprites():
        t = set(sp.tags)
        if "wall" in t:
            walls.add((sp.x, sp.y))
        if "player" in t:
            player = (sp.x, sp.y)
    budget = int(level.get_data("beacon_budget") or 8)
    radius = int(level.get_data("reveal_radius") or 8)
    steps = int(level.get_data("max_steps") or 500)
    gw, gh = level.grid_size
    return walls, player, budget, radius, steps, gw, gh


def _bn_revealed(beacons: tuple[tuple[int, int], ...], r: int, gw: int, gh: int) -> set[tuple[int, int]]:
    out: set[tuple[int, int]] = set()
    if r < 0:
        return out
    for bx, by in beacons:
        for y in range(by - r, by + r + 1):
            for x in range(bx - r, bx + r + 1):
                if abs(x - bx) + abs(y - by) <= r:
                    if 0 <= x < gw and 0 <= y < gh:
                        out.add((x, y))
    return out


def _bn_walkable(
    walls: set[tuple[int, int]],
    gw: int,
    gh: int,
    x: int,
    y: int,
) -> bool:
    if not (0 <= x < gw and 0 <= y < gh):
        return False
    return (x, y) not in walls


@dataclass(frozen=True)
class _BnSt:
    """BFS state: steps are not part of the key — each edge costs one step; check len(plan) <= max_steps at goal."""

    px: int
    py: int
    budget: int
    radius: int
    beacons: tuple[tuple[int, int], ...]
    flagged: frozenset[tuple[int, int]]


def _bn_bfs_plan(level: Level, *, max_nodes: int = 800_000) -> list[tuple[str, ...]] | None:
    walls, (sx, sy), budget0, radius0, steps0, gw, gh = _bn_parse(level)
    raw = level.get_data("hidden") or []
    hidden = frozenset(tuple(int(t) for t in p) for p in raw)

    def revealed(st: _BnSt) -> set[tuple[int, int]]:
        return _bn_revealed(st.beacons, st.radius, gw, gh)

    start = _BnSt(sx, sy, budget0, radius0, (), frozenset())
    if start.flagged == hidden:
        return []

    q: deque[_BnSt] = deque([start])
    parent: dict[_BnSt, tuple[_BnSt, tuple[str, ...]]] = {}
    seen: set[_BnSt] = {start}
    nodes = 0

    while q and nodes < max_nodes:
        st = q.popleft()
        nodes += 1
        if st.flagged == hidden:
            seq: list[tuple[str, ...]] = []
            cur = st
            while cur != start:
                cur, op = parent[cur]
                seq.append(op)
            seq.reverse()
            if len(seq) <= steps0:
                return seq
            return None

        rset = revealed(st)
        for gx, gy in sorted(hidden):
            if (gx, gy) in st.flagged or (gx, gy) not in rset:
                continue
            nf = frozenset(st.flagged | {(gx, gy)})
            nst = _BnSt(st.px, st.py, st.budget, st.radius, st.beacons, nf)
            if nst not in seen:
                seen.add(nst)
                parent[nst] = (st, ("F", str(gx), str(gy)))
                q.append(nst)

        for dx, dy, anum in BN_CARD:
            nx, ny = st.px + dx, st.py + dy
            if not _bn_walkable(walls, gw, gh, nx, ny):
                continue
            nst = _BnSt(nx, ny, st.budget, st.radius, st.beacons, st.flagged)
            if nst not in seen:
                seen.add(nst)
                parent[nst] = (st, ("M", str(anum)))
                q.append(nst)

        if st.budget > 0:
            nb = st.beacons + ((st.px, st.py),)
            nr = max(0, st.radius - 1)
            nst = _BnSt(st.px, st.py, st.budget - 1, nr, nb, st.flagged)
            if nst not in seen:
                seen.add(nst)
                parent[nst] = (st, ("B",))
                q.append(nst)

    return None


def record_bn03_registry_gif(
    game_id: str,
    root: Path,
    *,
    overrides: dict[str, Any] | None = None,
    verbose: bool = False,
    seed: int = 0,
) -> tuple[Any, list]:
    _ = seed
    o = dict(overrides or {})
    target_levels = int(o.get("target_levels", 0))
    max_gif = int(o.get("max_gif_frames", 1400))
    level_hold = int(o.get("bn_level_hold_frames", 14))

    mod = load_stem_game_py(game_id, f"{game_id}_registry_bn")
    level_defs: list = mod.levels
    n_authored = len(level_defs)
    L = target_levels if target_levels > 0 else min(3, max(1, n_authored))

    plans: list[list[tuple[str, ...]]] = []
    for i in range(L):
        p = _bn_bfs_plan(level_defs[i])
        if p is None:
            raise RuntimeError(f"{game_id}: level {i} has no bn03 BFS plan for registry GIF")
        plans.append(p)

    arc = offline_arcade(root)
    env = arc.make(full_game_id_for_stem(game_id), seed=0, render_mode=None)
    res = env.reset()
    images: list = []

    def snap_repeats(times: int) -> None:
        fr = _frame_layer0(res)
        if fr:
            append_frame_repeats(images, fr[0], times)

    snap_repeats(8)

    def step_bn(act: GameAction, *, data: dict | None = None) -> None:
        nonlocal res
        res = safe_env_step(env, act, reasoning={}, data=data or {})
        snap_repeats(1)

    lvl0 = level_defs[0]
    gw0, gh0 = lvl0.grid_size
    walls0 = {(sp.x, sp.y) for sp in lvl0.get_sprites() if "wall" in sp.tags}
    hid0 = {tuple(int(t) for t in p) for p in (lvl0.get_data("hidden") or [])}
    fail_x, fail_y = 0, 0
    for x in range(gw0):
        for y in range(gh0):
            if (x, y) in walls0 or (x, y) in hid0:
                continue
            fail_x, fail_y = x, y
            break
        else:
            continue
        break

    for li, plan in enumerate(plans):
        lvl = level_defs[li]
        gw, gh = lvl.grid_size
        if li == 0 and plan:
            warm = 0
            for op in plan:
                if warm >= 4:
                    break
                if op[0] == "M":
                    step_bn(_PUSH_ACTION[int(op[1])])
                    warm += 1
            cx, cy = grid_cell_center_display(fail_x, fail_y, grid_w=gw, grid_h=gh)
            step_bn(GameAction.ACTION6, data={"x": cx, "y": cy})
            snap_repeats(18)
            res = env.reset()
            snap_repeats(10)

        for op in plan:
            if op[0] == "M":
                step_bn(_PUSH_ACTION[int(op[1])])
            elif op[0] == "B":
                step_bn(GameAction.ACTION5)
            else:
                gx, gy = int(op[1]), int(op[2])
                cx, cy = grid_cell_center_display(gx, gy, grid_w=gw, grid_h=gh)
                step_bn(GameAction.ACTION6, data={"x": cx, "y": cy})
        snap_repeats(level_hold)

    snap_repeats(12)
    _cap_gif_frames(images, max_gif)
    if verbose:
        print(f"  {game_id}: bn03 registry GIF, {L} levels, {len(images)} frames")
    return res, images


# --- bi01 diagonal slide ---


def _bi_parse(level: Level) -> tuple[set[tuple[int, int]], tuple[int, int], tuple[int, int], int, int]:
    walls: set[tuple[int, int]] = set()
    player = (0, 0)
    goal = (0, 0)
    for sp in level.get_sprites():
        t = set(sp.tags)
        if "wall" in t:
            walls.add((sp.x, sp.y))
        if "player" in t:
            player = (sp.x, sp.y)
        if "goal" in t:
            goal = (sp.x, sp.y)
    gw, gh = level.grid_size
    return walls, player, goal, gw, gh


def _bi_slide(
    walls: set[tuple[int, int]],
    gw: int,
    gh: int,
    x: int,
    y: int,
    dx: int,
    dy: int,
    goal: tuple[int, int],
) -> tuple[int, int]:
    gx, gy = goal
    while True:
        nx, ny = x + dx, y + dy
        if not (0 <= nx < gw and 0 <= ny < gh):
            break
        if (nx, ny) in walls:
            break
        x, y = nx, ny
        if x == gx and y == gy:
            break
    return x, y


def _bi_bfs_plan(level: Level) -> list[int] | None:
    walls, start, goal, gw, gh = _bi_parse(level)
    if start == goal:
        return []

    q: deque[tuple[int, int]] = deque([start])
    prev: dict[tuple[int, int], tuple[tuple[int, int], int] | None] = {start: None}
    found: tuple[int, int] | None = None
    while q:
        x, y = q.popleft()
        if (x, y) == goal:
            found = (x, y)
            break
        for dx, dy, anum in BI_DIAG:
            nx, ny = _bi_slide(walls, gw, gh, x, y, dx, dy, goal)
            if (nx, ny) == (x, y):
                continue
            if (nx, ny) not in prev:
                prev[(nx, ny)] = ((x, y), anum)
                q.append((nx, ny))
    if found is None:
        return None
    path: list[int] = []
    cur = found
    while prev[cur] is not None:
        p, anum = prev[cur]
        path.append(anum)
        cur = p
    path.reverse()
    return path


def record_bi01_registry_gif(
    game_id: str,
    root: Path,
    *,
    overrides: dict[str, Any] | None = None,
    verbose: bool = False,
    seed: int = 0,
) -> tuple[Any, list]:
    _ = seed
    o = dict(overrides or {})
    target_levels = int(o.get("target_levels", 0))
    max_gif = int(o.get("max_gif_frames", 520))
    level_hold = int(o.get("bi_level_hold_frames", 14))
    no_move_frames = int(o.get("bi_no_move_frames", 3))

    mod = load_stem_game_py(game_id, f"{game_id}_registry_bi")
    level_defs: list = mod.levels
    n_authored = len(level_defs)
    L = target_levels if target_levels > 0 else min(5, max(1, n_authored))

    plans: list[list[int]] = []
    for i in range(L):
        p = _bi_bfs_plan(level_defs[i])
        if p is None:
            raise RuntimeError(f"{game_id}: level {i} has no bi01 diagonal plan for registry GIF")
        plans.append(p)

    arc = offline_arcade(root)
    env = arc.make(full_game_id_for_stem(game_id), seed=0, render_mode=None)
    res = env.reset()
    images: list = []

    def snap_repeats(times: int) -> None:
        fr = _frame_layer0(res)
        if fr:
            append_frame_repeats(images, fr[0], times)

    snap_repeats(8)
    for plan in plans:
        for av in plan:
            g = env._game
            px, py = g._player.x, g._player.y
            res = safe_env_step(env, _PUSH_ACTION[av], reasoning={})
            if g._player.x == px and g._player.y == py:
                snap_repeats(no_move_frames)
            else:
                snap_repeats(1)
        snap_repeats(level_hold)

    snap_repeats(10)
    _cap_gif_frames(images, max_gif)
    if verbose:
        moves = sum(len(p) for p in plans)
        print(f"  {game_id}: bi01 registry GIF, {L} levels, {moves} moves, {len(images)} frames")
    return res, images
