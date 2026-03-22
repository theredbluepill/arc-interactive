"""Registry GIF capture for rk01–jw01: offline planners matching each game's physics."""

from __future__ import annotations

from collections import deque
from pathlib import Path
from typing import Any

from arcengine import GameAction, Level

from env_resolve import full_game_id_for_stem, load_stem_game_py
from gif_common import (
    append_frame_repeats,
    grid_cell_center_display,
    offline_arcade,
)
from registry_gif_lib import (
    _StepAbort,
    _frame_layer0,
    _cap_gif_frames,
    safe_env_step,
)

# Plan step: int 1–4 = ACTION1–4; "dig" = ACTION5; ("click", gx, gy) = ACTION6 cell center
PlanStep = int | str | tuple[str, int, int]

_ACT: dict[int, GameAction] = {
    1: GameAction.ACTION1,
    2: GameAction.ACTION2,
    3: GameAction.ACTION3,
    4: GameAction.ACTION4,
}


def _walls_player_goal(level: Level) -> tuple[set[tuple[int, int]], tuple[int, int] | None, set[tuple[int, int]], int, int]:
    walls: set[tuple[int, int]] = set()
    goals: set[tuple[int, int]] = set()
    player: tuple[int, int] | None = None
    gw, gh = level.grid_size
    for s in level.get_sprites():
        p = (s.x, s.y)
        t = set(s.tags)
        if "wall" in t:
            walls.add(p)
        if "goal" in t:
            goals.add(p)
        if "player" in t:
            player = p
    return walls, player, goals, gw, gh


def _rk_slide(
    walls: set[tuple[int, int]],
    gw: int,
    gh: int,
    goals: set[tuple[int, int]],
    x: int,
    y: int,
    dx: int,
    dy: int,
) -> tuple[tuple[int, int], bool]:
    """Rook slide; True if the path visits a goal (matches rk01 win-on-path)."""
    while True:
        nx, ny = x + dx, y + dy
        if not (0 <= nx < gw and 0 <= ny < gh) or (nx, ny) in walls:
            return (x, y), (x, y) in goals
        x, y = nx, ny
        if (x, y) in goals:
            return (x, y), True


def plan_rk01(level: Level) -> list[int] | None:
    walls, start, goals, gw, gh = _walls_player_goal(level)
    if start is None or not goals:
        return None
    deltas = ((0, -1, 1), (0, 1, 2), (-1, 0, 3), (1, 0, 4))
    q: deque[tuple[int, int]] = deque([start])
    prev: dict[tuple[int, int], tuple[tuple[int, int], int] | None] = {start: None}
    while q:
        x, y = q.popleft()
        if (x, y) in goals:
            out: list[int] = []
            cur = (x, y)
            while prev[cur] is not None:
                p, av = prev[cur]
                out.append(av)
                cur = p
            out.reverse()
            return out
        for dx, dy, av in deltas:
            nxt, wins = _rk_slide(walls, gw, gh, goals, x, y, dx, dy)
            if wins:
                out = []
                cur = (x, y)
                while prev[cur] is not None:
                    p, a = prev[cur]
                    out.append(a)
                    cur = p
                out.reverse()
                out.append(av)
                return out
            if nxt not in prev:
                prev[nxt] = ((x, y), av)
                q.append(nxt)
    return None


def plan_sn01(level: Level) -> list[int] | None:
    walls: set[tuple[int, int]] = set()
    foods: set[tuple[int, int]] = set()
    player: tuple[int, int] | None = None
    gw, gh = level.grid_size
    for s in level.get_sprites():
        p = (s.x, s.y)
        t = set(s.tags)
        if "wall" in t:
            walls.add(p)
        if "food" in t:
            foods.add(p)
        if "player" in t:
            player = p
    if player is None:
        return None
    start_body = (player,)
    start_food = frozenset(foods)
    start = (start_body, start_food)
    deltas = ((0, -1, 1), (0, 1, 2), (-1, 0, 3), (1, 0, 4))
    q: deque[tuple[tuple[tuple[int, int], ...], frozenset[tuple[int, int]]]] = deque([start])
    prev: dict[Any, Any] = {start: None}
    nodes = 0
    while q:
        nodes += 1
        if nodes > 120_000:
            return None
        body, fset = q.popleft()
        if not fset:
            out: list[int] = []
            cur: Any = (body, fset)
            while prev[cur] is not None:
                p, av = prev[cur]
                out.append(av)
                cur = p
            out.reverse()
            return out
        hx, hy = body[-1]
        tail = body[0]
        for dx, dy, av in deltas:
            nx, ny = hx + dx, hy + dy
            if not (0 <= nx < gw and 0 <= ny < gh) or (nx, ny) in walls:
                continue
            grow = (nx, ny) in fset
            if (nx, ny) in body and (nx, ny) != tail:
                continue
            if grow and (nx, ny) in body:
                continue
            if grow:
                new_body = body + ((nx, ny),)
                new_f = fset - {(nx, ny)}
            elif len(body) == 1:
                new_body = ((nx, ny),)
                new_f = fset
            else:
                new_body = body[1:] + ((nx, ny),)
                new_f = fset
            ns = (new_body, new_f)
            if ns not in prev:
                prev[ns] = ((body, fset), av)
                q.append(ns)
    return None


def plan_vp01(level: Level) -> list[int] | None:
    walls, start, goals, gw, gh = _walls_player_goal(level)
    if start is None or not goals:
        return None
    deltas = ((0, -1, 1), (0, 1, 2), (-1, 0, 3), (1, 0, 4))
    q: deque[tuple[int, int, frozenset[tuple[int, int]]]] = deque([(start[0], start[1], frozenset({start}))])
    prev: dict[Any, Any] = {q[0]: None}
    while q:
        x, y, vis = q.popleft()
        if (x, y) in goals:
            out: list[int] = []
            cur: Any = (x, y, vis)
            while prev[cur] is not None:
                p, av = prev[cur]
                out.append(av)
                cur = p
            out.reverse()
            return out
        for dx, dy, av in deltas:
            nx, ny = x + dx, y + dy
            if not (0 <= nx < gw and 0 <= ny < gh) or (nx, ny) in walls:
                continue
            if (nx, ny) in vis:
                continue
            nvis = frozenset(vis | {(nx, ny)})
            nxt = (nx, ny, nvis)
            if nxt not in prev:
                prev[nxt] = ((x, y, vis), av)
                q.append(nxt)
    return None


def plan_fg01(level: Level) -> list[int] | None:
    """Unconstrained grid BFS (fog is render-only)."""
    walls, start, goals, gw, gh = _walls_player_goal(level)
    if start is None or not goals:
        return None
    deltas = ((0, -1, 1), (0, 1, 2), (-1, 0, 3), (1, 0, 4))
    q: deque[tuple[int, int]] = deque([start])
    prev: dict[tuple[int, int], Any] = {start: None}
    while q:
        x, y = q.popleft()
        if (x, y) in goals:
            out: list[int] = []
            cur = (x, y)
            while prev[cur] is not None:
                p, av = prev[cur]
                out.append(av)
                cur = p
            out.reverse()
            return out
        for dx, dy, av in deltas:
            nx, ny = x + dx, y + dy
            if not (0 <= nx < gw and 0 <= ny < gh) or (nx, ny) in walls:
                continue
            if (nx, ny) not in prev:
                prev[(nx, ny)] = ((x, y), av)
                q.append((nx, ny))
    return None


def plan_kb01(level: Level) -> list[int] | None:
    walls, start, goals, gw, gh = _walls_player_goal(level)
    key_pos: tuple[int, int] | None = None
    for s in level.get_sprites():
        if "key" in s.tags:
            key_pos = (s.x, s.y)
            break
    if start is None or not goals or key_pos is None:
        return None
    r = int(level.get_data("leash") or 4)
    kx, ky = key_pos
    deltas = ((0, -1, 1), (0, 1, 2), (-1, 0, 3), (1, 0, 4))
    q: deque[tuple[int, int]] = deque([start])
    prev: dict[tuple[int, int], Any] = {start: None}
    while q:
        x, y = q.popleft()
        if (x, y) in goals:
            out: list[int] = []
            cur = (x, y)
            while prev[cur] is not None:
                p, av = prev[cur]
                out.append(av)
                cur = p
            out.reverse()
            return out
        for dx, dy, av in deltas:
            nx, ny = x + dx, y + dy
            if not (0 <= nx < gw and 0 <= ny < gh) or (nx, ny) in walls:
                continue
            if abs(nx - kx) + abs(ny - ky) > r:
                continue
            if (nx, ny) not in prev:
                prev[(nx, ny)] = ((x, y), av)
                q.append((nx, ny))
    return None


def plan_bt01(level: Level) -> list[int] | None:
    walls, start, goals, gw, gh = _walls_player_goal(level)
    pads: set[tuple[int, int]] = set()
    for s in level.get_sprites():
        if "charge" in s.tags:
            pads.add((s.x, s.y))
    cap = int(level.get_data("cap") or 25)
    if start is None or not goals:
        return None
    deltas = ((0, -1, 1), (0, 1, 2), (-1, 0, 3), (1, 0, 4))
    q: deque[tuple[int, int, int]] = deque([(start[0], start[1], cap)])
    prev: dict[tuple[int, int, int], Any] = {q[0]: None}
    nodes = 0
    while q:
        nodes += 1
        if nodes > 2_000_000:
            return None
        x, y, ch = q.popleft()
        if (x, y) in goals:
            out: list[int] = []
            cur = (x, y, ch)
            while prev[cur] is not None:
                p, av = prev[cur]
                out.append(av)
                cur = p
            out.reverse()
            return out
        for dx, dy, av in deltas:
            nx, ny = x + dx, y + dy
            if not (0 <= nx < gw and 0 <= ny < gh) or (nx, ny) in walls:
                continue
            nch = ch - 1
            if (nx, ny) in pads:
                nch = cap
            if nch <= 0:
                continue
            nxt = (nx, ny, nch)
            if nxt not in prev:
                prev[nxt] = ((x, y, ch), av)
                q.append(nxt)
    return None


def _plan_tr01_ttl(level: Level, *, max_nodes: int) -> list[int] | None:
    walls, start, goals, gw, gh = _walls_player_goal(level)
    ttl = int(level.get_data("ttl") or 20)
    if start is None or not goals:
        return None
    deltas = ((0, -1, 1), (0, 1, 2), (-1, 0, 3), (1, 0, 4))

    def tr_step(
        w: int,
        fz: frozenset[tuple[tuple[int, int], int]],
        px: int,
        py: int,
        av: int,
    ) -> tuple[int, frozenset[tuple[tuple[int, int], int]], int, int] | None:
        w2 = w + 1
        dx, dy = {1: (0, -1), 2: (0, 1), 3: (-1, 0), 4: (1, 0)}[av]
        nx, ny = px + dx, py + dy
        if not (0 <= nx < gw and 0 <= ny < gh) or (nx, ny) in walls:
            return None
        ent = dict(fz)
        if (nx, ny) in ent:
            if w2 - ent[(nx, ny)] >= ttl:
                return None
        if (nx, ny) not in ent:
            ent[(nx, ny)] = w2
        for c, t0 in ent.items():
            if w2 - t0 >= ttl and c == (nx, ny):
                return None
        nfz = frozenset(ent.items())
        return (w2, nfz, nx, ny)

    s0 = frozenset({(start, 1)})
    start_state = (1, s0, start[0], start[1])
    q: deque[tuple[int, frozenset[tuple[tuple[int, int], int]], int, int]] = deque(
        [start_state]
    )
    prev: dict[Any, Any] = {start_state: None}
    nodes = 0
    while q:
        nodes += 1
        if nodes > max_nodes:
            return None
        w, fz, x, y = q.popleft()
        if (x, y) in goals:
            out: list[int] = []
            cur: Any = (w, fz, x, y)
            while prev[cur] is not None:
                p, av = prev[cur]
                out.append(av)
                cur = p
            out.reverse()
            return out
        for _dx, _dy, av in deltas:
            sim = tr_step(w, fz, x, y, av)
            if sim is None:
                continue
            w2, nfz, nx, ny = sim
            st = (w2, nfz, nx, ny)
            if st not in prev:
                prev[st] = ((w, fz, x, y), av)
                q.append(st)
    return None


def plan_tr01(level: Level) -> list[int] | None:
    """TTL-aware search is expensive; try a small cap then fall back to grid BFS."""
    p = _plan_tr01_ttl(level, max_nodes=35_000)
    if p is not None:
        return p
    return plan_fg01(level)


def plan_dg01(level: Level) -> list[PlanStep] | None:
    walls, start, goals, gw, gh = _walls_player_goal(level)
    mud: set[tuple[int, int]] = set()
    for s in level.get_sprites():
        if "mud" in s.tags:
            mud.add((s.x, s.y))
    budget = int(level.get_data("dig_budget") or 5)
    if start is None or not goals:
        return None
    deltas = ((0, -1, 1), (0, 1, 2), (-1, 0, 3), (1, 0, 4))
    start_state = (start[0], start[1], frozenset(mud), budget)
    q: deque[tuple[int, int, frozenset[tuple[int, int]], int]] = deque([start_state])
    prev: dict[Any, Any] = {start_state: None}
    nodes = 0
    while q:
        nodes += 1
        if nodes > 2_000_000:
            return None
        x, y, mset, b = q.popleft()
        if (x, y) in goals:
            out: list[PlanStep] = []
            cur: Any = (x, y, mset, b)
            while prev[cur] is not None:
                p, step = prev[cur]
                out.append(step)
                cur = p
            out.reverse()
            return out
        if b > 0:
            for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                nx, ny = x + dx, y + dy
                if (nx, ny) in mset:
                    nm = frozenset(mset - {(nx, ny)})
                    st = (x, y, nm, b - 1)
                    if st not in prev:
                        prev[st] = ((x, y, mset, b), "dig")
                        q.append(st)
        for dx, dy, av in deltas:
            nx, ny = x + dx, y + dy
            if not (0 <= nx < gw and 0 <= ny < gh) or (nx, ny) in walls or (nx, ny) in mset:
                continue
            st = (nx, ny, mset, b)
            if st not in prev:
                prev[st] = ((x, y, mset, b), av)
                q.append(st)
    return None


def _eb_escalate(walls: set[tuple[int, int]], gw: int, gh: int, row: int, x: int, y: int) -> tuple[int, int]:
    while y == row:
        nx = x + 1
        if not (0 <= nx < gw and 0 <= y < gh) or (nx, y) in walls:
            break
        x = nx
    return (x, y)


def plan_eb01(level: Level) -> list[int] | None:
    walls, start, goals, gw, gh = _walls_player_goal(level)
    row = int(level.get_data("escalator_row") or 5)
    if start is None or not goals:
        return None
    deltas = ((0, -1, 1), (0, 1, 2), (-1, 0, 3), (1, 0, 4))
    q: deque[tuple[int, int]] = deque([start])
    prev: dict[tuple[int, int], Any] = {start: None}
    while q:
        x, y = q.popleft()
        if (x, y) in goals:
            out: list[int] = []
            cur = (x, y)
            while prev[cur] is not None:
                p, av = prev[cur]
                out.append(av)
                cur = p
            out.reverse()
            return out
        for dx, dy, av in deltas:
            nx, ny = x + dx, y + dy
            if not (0 <= nx < gw and 0 <= ny < gh) or (nx, ny) in walls:
                continue
            fx, fy = _eb_escalate(walls, gw, gh, row, nx, ny)
            nxt = (fx, fy)
            if nxt not in prev:
                prev[nxt] = ((x, y), av)
                q.append(nxt)
    return None


def _mb_pull(
    walls: set[tuple[int, int]],
    goals: set[tuple[int, int]],
    gw: int,
    gh: int,
    px: int,
    py: int,
    crates: list[tuple[int, int]],
) -> list[tuple[int, int]]:
    out = list(crates)
    for i, (cx, cy) in enumerate(out):

        def blocked(ex: int, ey: int, ignore_idx: int | None) -> bool:
            if not (0 <= ex < gw and 0 <= ey < gh):
                return True
            if (ex, ey) in walls:
                return True
            if (ex, ey) in goals:
                return False
            for j, (ox, oy) in enumerate(out):
                if j == ignore_idx:
                    continue
                if (ox, oy) == (ex, ey):
                    return True
            return False

        dx = (1 if px > cx else -1) if px != cx else 0
        dy = (1 if py > cy else -1) if py != cy else 0
        if dx != 0 and dy != 0:
            if abs(px - cx) >= abs(py - cy):
                dy = 0
            else:
                dx = 0
        nx, ny = cx + dx, cy + dy
        if not blocked(nx, ny, i):
            out[i] = (nx, ny)
    return out


def plan_mb01(level: Level) -> list[int] | None:
    walls, start, goals, gw, gh = _walls_player_goal(level)
    crates = [(s.x, s.y) for s in level.get_sprites() if "metal" in s.tags]
    if start is None or not goals:
        return None
    deltas = ((0, -1, 1), (0, 1, 2), (-1, 0, 3), (1, 0, 4))
    start_crates = tuple(sorted(crates))
    q: deque[tuple[int, int, tuple[tuple[int, int], ...]]] = deque([(start[0], start[1], start_crates)])
    prev: dict[Any, Any] = {q[0]: None}
    nodes = 0
    while q:
        nodes += 1
        if nodes > 900_000:
            return None
        x, y, ct = q.popleft()
        if (x, y) in goals:
            out: list[int] = []
            cur: Any = (x, y, ct)
            while prev[cur] is not None:
                p, av = prev[cur]
                out.append(av)
                cur = p
            out.reverse()
            return out
        clist = list(ct)
        for dx, dy, av in deltas:
            nx, ny = x + dx, y + dy
            if not (0 <= nx < gw and 0 <= ny < gh) or (nx, ny) in walls:
                continue
            if any((nx, ny) == c for c in clist):
                continue
            after_p = (nx, ny)
            pulled = _mb_pull(walls, goals, gw, gh, after_p[0], after_p[1], clist)
            nct = tuple(sorted(pulled))
            nxt = (after_p[0], after_p[1], nct)
            if nxt not in prev:
                prev[nxt] = ((x, y, ct), av)
                q.append(nxt)
    return None


def plan_op01(level: Level) -> list[int] | None:
    walls: set[tuple[int, int]] = set()
    targets: set[tuple[int, int]] = set()
    player: tuple[int, int] | None = None
    block: tuple[int, int] | None = None
    gw, gh = level.grid_size
    for s in level.get_sprites():
        p = (s.x, s.y)
        t = set(s.tags)
        if "wall" in t:
            walls.add(p)
        if "target" in t:
            targets.add(p)
        if "player" in t:
            player = p
        if "block" in t:
            block = p
    if player is None or block is None or not targets:
        return None
    lim = int(level.get_data("step_limit") or 80)
    deltas = ((0, -1, 1), (0, 1, 2), (-1, 0, 3), (1, 0, 4))
    start_state = (player[0], player[1], block[0], block[1], False, 0)
    q: deque[tuple[int, int, int, int, bool, int]] = deque([start_state])
    prev: dict[Any, Any] = {start_state: None}
    nodes = 0
    while q:
        nodes += 1
        if nodes > 3_000_000:
            return None
        px, py, bx, by, pushed, steps = q.popleft()
        if any((bx, by) == t for t in targets):
            out: list[int] = []
            cur: Any = (px, py, bx, by, pushed, steps)
            while prev[cur] is not None:
                p, av = prev[cur]
                out.append(av)
                cur = p
            out.reverse()
            return out
        if steps >= lim:
            continue
        for dx, dy, av in deltas:
            nx, ny = px + dx, py + dy
            if not (0 <= nx < gw and 0 <= ny < gh) or (nx, ny) in walls:
                continue
            if (nx, ny) == (bx, by):
                if pushed:
                    continue
                bx2, by2 = bx + dx, by + dy
                if not (0 <= bx2 < gw and 0 <= by2 < gh):
                    continue
                if (bx2, by2) in walls:
                    continue
                npx, npy = nx, ny
                nbx, nby = bx2, by2
                npushed = True
            else:
                npx, npy = nx, ny
                nbx, nby = bx, by
                npushed = pushed
            nsteps = steps + 1
            st = (npx, npy, nbx, nby, npushed, nsteps)
            if st not in prev:
                prev[st] = ((px, py, bx, by, pushed, steps), av)
                q.append(st)
    return None


def _jw_rect_cells(x: int, y: int, w: int, h: int) -> list[tuple[int, int]]:
    return [(x + dx, y + dy) for dx in range(w) for dy in range(h)]


def _jw_swap_boxes(
    boxes: frozenset[tuple[int, int]], ra: tuple[int, int, int, int], rb: tuple[int, int, int, int]
) -> frozenset[tuple[int, int]]:
    x0, y0, w0, h0 = ra
    x1, y1, w1, h1 = rb
    ca = _jw_rect_cells(x0, y0, w0, h0)
    cb = _jw_rect_cells(x1, y1, w1, h1)
    b = set(boxes)
    for (ax, ay), (bx, by) in zip(ca, cb):
        ah = (ax, ay) in b
        bh = (bx, by) in b
        if ah and not bh:
            b.remove((ax, ay))
            b.add((bx, by))
        elif bh and not ah:
            b.remove((bx, by))
            b.add((ax, ay))
    return frozenset(b)


def _jw_try_move(
    walls: set[tuple[int, int]],
    triggers: set[tuple[int, int]],
    gw: int,
    gh: int,
    px: int,
    py: int,
    boxes: frozenset[tuple[int, int]],
    av: int,
) -> tuple[int, int, frozenset[tuple[int, int]]] | None:
    dx, dy = {1: (0, -1), 2: (0, 1), 3: (-1, 0), 4: (1, 0)}[av]
    nx, ny = px + dx, py + dy
    if not (0 <= nx < gw and 0 <= ny < gh) or (nx, ny) in walls:
        return None
    if (nx, ny) in triggers:
        return None
    bs = set(boxes)
    if (nx, ny) in bs:
        bx, by = nx + dx, ny + dy
        if not (0 <= bx < gw and 0 <= by < gh):
            return None
        if (bx, by) in walls or (bx, by) in triggers:
            return None
        if (bx, by) in bs:
            return None
        bs.remove((nx, ny))
        bs.add((bx, by))
        return (nx, ny, frozenset(bs))
    return (nx, ny, boxes)


def _jw_bfs(
    level: Level,
    *,
    allow_swap: bool,
    max_nodes: int,
) -> list[PlanStep] | None:
    walls: set[tuple[int, int]] = set()
    triggers: set[tuple[int, int]] = set()
    goals: set[tuple[int, int]] = set()
    player: tuple[int, int] | None = None
    box_positions: set[tuple[int, int]] = set()
    gw, gh = level.grid_size
    for s in level.get_sprites():
        p = (s.x, s.y)
        t = set(s.tags)
        if "wall" in t:
            walls.add(p)
        if "trigger" in t:
            triggers.add(p)
        if "goal" in t:
            goals.add(p)
        if "player" in t:
            player = p
        if "box" in t:
            box_positions.add(p)
    ra = tuple(int(x) for x in (level.get_data("rect_a") or [1, 4, 2, 1]))
    rb = tuple(int(x) for x in (level.get_data("rect_b") or [6, 4, 2, 1]))
    if player is None or not goals:
        return None
    start = (player[0], player[1], frozenset(box_positions))
    deltas = ((0, -1, 1), (0, 1, 2), (-1, 0, 3), (1, 0, 4))
    q: deque[tuple[int, int, frozenset[tuple[int, int]]]] = deque([start])
    prev: dict[Any, Any] = {start: None}
    nodes = 0
    while q:
        nodes += 1
        if nodes > max_nodes:
            return None
        px, py, fz = q.popleft()
        if (px, py) in goals:
            out: list[PlanStep] = []
            cur: Any = (px, py, fz)
            while prev[cur] is not None:
                p, step = prev[cur]
                out.append(step)
                cur = p
            out.reverse()
            return out
        if allow_swap:
            nfz = _jw_swap_boxes(fz, ra, rb)
            if nfz != fz:
                st_sw = (px, py, nfz)
                if st_sw not in prev:
                    prev[st_sw] = ((px, py, fz), "swap")
                    q.append(st_sw)
        for _dx, _dy, av in deltas:
            tm = _jw_try_move(walls, triggers, gw, gh, px, py, fz, av)
            if tm is None:
                continue
            npx, npy, nfz2 = tm
            st = (npx, npy, nfz2)
            if st not in prev:
                prev[st] = ((px, py, fz), av)
                q.append(st)
    return None


def plan_jw01(level: Level) -> list[PlanStep] | None:
    """Try push-only BFS first (fast); then BFS with sparse swap edges (bounded)."""
    p = _jw_bfs(level, allow_swap=False, max_nodes=250_000)
    if p is not None:
        return p
    return _jw_bfs(level, allow_swap=True, max_nodes=200_000)


PLAN_DISPATCH: dict[str, Any] = {
    "rk01": plan_rk01,
    "sn01": plan_sn01,
    "tr01": plan_tr01,
    "vp01": plan_vp01,
    "bt01": plan_bt01,
    "dg01": plan_dg01,
    "mb01": plan_mb01,
    "op01": plan_op01,
    "kb01": plan_kb01,
    "eb01": plan_eb01,
    "fg01": plan_fg01,
    "jw01": plan_jw01,
}


def _apply_step(
    env: Any,
    res: Any,
    step: PlanStep,
    gw: int,
    gh: int,
) -> Any:
    if step == "dig":
        return safe_env_step(env, GameAction.ACTION5, reasoning={})
    if isinstance(step, tuple) and step[0] == "click":
        _, gx, gy = step
        cx, cy = grid_cell_center_display(
            gx, gy, grid_w=gw, grid_h=gh, frame_size=64
        )
        return safe_env_step(
            env,
            GameAction.ACTION6,
            reasoning={},
            data={"x": cx, "y": cy},
        )
    if isinstance(step, int):
        return safe_env_step(env, _ACT[step], reasoning={})
    raise ValueError(f"bad plan step {step!r}")


def record_rk_jw_registry_gif(
    game_id: str,
    root: Path,
    *,
    overrides: dict[str, Any] | None,
    verbose: bool,
    seed: int,
) -> tuple[Any, list]:
    _ = seed
    o = dict(overrides or {})
    target_levels = int(o.get("target_levels", 0))
    max_gif = int(o.get("max_gif_frames", 950))
    level_hold = int(o.get("rk_jw_level_hold_frames", 14))
    open_hold = int(o.get("rk_jw_fail_hold_frames", 18))

    mod = load_stem_game_py(game_id, f"{game_id}_registry_rk_jw")
    level_defs: list = mod.levels
    n_authored = len(level_defs)
    L = target_levels if target_levels > 0 else min(5, max(1, n_authored))
    if game_id == "sn01":
        L = min(L, 4)

    fail_kb01: list[int] | None = None
    if game_id == "kb01":
        fail_kb01 = [3, 1, 1]

    plans: list[list[PlanStep]] = []
    for i in range(L):
        raw = PLAN_DISPATCH[game_id](level_defs[i])
        if raw is None:
            break
        if game_id == "jw01":
            tr_pos: tuple[int, int] | None = None
            for s in level_defs[i].get_sprites():
                if "trigger" in s.tags:
                    tr_pos = (s.x, s.y)
                    break
            fixed: list[PlanStep] = []
            for st in raw:
                if st == "swap":
                    if tr_pos:
                        fixed.append(("click", tr_pos[0], tr_pos[1]))
                else:
                    fixed.append(st)
            raw = fixed
        plans.append(raw)

    if not plans:
        raise RuntimeError(f"{game_id}: registry RK-JW planner found no solvable level")

    arc = offline_arcade(root)
    env = arc.make(full_game_id_for_stem(game_id), seed=0, render_mode=None)
    res = env.reset()
    images: list = []

    def snap_repeats(times: int) -> None:
        fr = _frame_layer0(res)
        if fr:
            append_frame_repeats(images, fr[0], times)

    gw, gh = env._game.current_level.grid_size

    snap_repeats(8)
    step_abort = False
    try:
        if fail_kb01 is not None:
            for av in fail_kb01:
                res = safe_env_step(env, _ACT[av], reasoning={})
                snap_repeats(1)
            snap_repeats(open_hold)
            res = env.reset()
            snap_repeats(8)
            gw, gh = env._game.current_level.grid_size

        for plan in plans:
            for step in plan:
                res = _apply_step(env, res, step, gw, gh)
                snap_repeats(1)
            snap_repeats(level_hold)
            if env._game.current_level:
                gw, gh = env._game.current_level.grid_size
    except _StepAbort as ex:
        step_abort = True
        if verbose:
            print(f"  {game_id}: rk-jw GIF step abort ({ex})")

    snap_repeats(10)
    if step_abort and not images:
        res = env.reset()
        fr = _frame_layer0(res)
        if fr:
            append_frame_repeats(images, fr[0], 24)

    _cap_gif_frames(images, max_gif)

    if verbose:
        nst = sum(len(p) for p in plans)
        print(
            f"  {game_id}: rk-jw planned GIF, {len(plans)} levels, {nst} steps, {len(images)} frames"
        )

    return res, images
