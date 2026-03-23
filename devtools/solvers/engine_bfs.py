"""Breadth-first search over the real ``Arcade`` environment (sound for fully observable dynamics)."""

from __future__ import annotations

from collections import deque
from collections.abc import Callable, Iterable
from dataclasses import dataclass

from arcengine import GameAction, GameState

_GAME_ACTION_BY_ID: dict[int, GameAction] = {
    1: GameAction.ACTION1,
    2: GameAction.ACTION2,
    3: GameAction.ACTION3,
    4: GameAction.ACTION4,
    5: GameAction.ACTION5,
    6: GameAction.ACTION6,
    7: GameAction.ACTION7,
}


def _frame_key(env) -> bytes:
    o = env.observation_space
    f = o.frame
    if f is None or len(f) < 1:
        return b""
    return f[0].tobytes()


@dataclass(frozen=True)
class BFSResult:
    ok: bool
    nodes: int
    depth: int | None
    reason: str


def _display_click_payload_for_grid_cell(env, gx: int, gy: int, *, frame_size: int = 64) -> dict:
    """Map grid cell to ACTION6 ``data`` using the same letterboxing as typical 64×64 renders.

    Games use ``camera.display_to_grid`` on **display** pixels, not raw grid indices
    (see AGENTS.md). Passing ``(gx, gy)`` as x/y falsely appears as clicks on the
    top-left corner only.
    """
    cam = getattr(env._game, "camera", None)
    if cam is None:
        return {"x": gx, "y": gy}
    cw, ch = int(cam.width), int(cam.height)
    scale = max(1, min(frame_size // cw, frame_size // ch))
    x_pad = (frame_size - cw * scale) // 2
    y_pad = (frame_size - ch * scale) // 2
    px = gx * scale + scale // 2 + x_pad
    py = gy * scale + scale // 2 + y_pad
    return {"x": px, "y": py}


def _iter_action_specs(
    *,
    available: Iterable[int],
    grid_w: int,
    grid_h: int,
    max_click_cells: int,
    env,
) -> list[tuple[int, dict]]:
    specs: list[tuple[int, dict]] = []
    avail = sorted(set(available))
    n_cells = max(0, grid_w) * max(0, grid_h)
    for aid in avail:
        if aid not in _GAME_ACTION_BY_ID:
            continue
        if aid == 6:
            if n_cells > max_click_cells:
                raise ValueError(
                    f"ACTION6 grid {grid_w}x{grid_h}={n_cells} exceeds max_click_cells={max_click_cells}"
                )
            for y in range(grid_h):
                for x in range(grid_w):
                    specs.append((6, _display_click_payload_for_grid_cell(env, x, y)))
        else:
            specs.append((aid, {}))
    return specs


def engine_bfs_single_level(
    env,
    *,
    level_index: int,
    max_nodes: int,
    max_depth: int,
    max_click_cells: int,
    allowed_action_ids: set[int] | None = None,
    extra_state_key: Callable[[object], bytes] | None = None,
) -> BFSResult:
    """Return whether level ``level_index`` can be cleared from a reset + ``set_level``."""
    g = env._game
    gw, gh = g.current_level.grid_size

    def replay(path: list[tuple[int, dict]]) -> tuple[bool, object | None]:
        env.reset()
        g.set_level(level_index)
        res = None
        for aid, data in path:
            act = _GAME_ACTION_BY_ID[aid]
            res = env.step(act, data=data, reasoning={})
            if res is None:
                return False, None
            if res.state == GameState.GAME_OVER:
                return False, res
        return True, res

    env.reset()
    g.set_level(level_index)
    start_lc = env.observation_space.levels_completed
    raw_avail = list(env.observation_space.available_actions)
    if allowed_action_ids is not None:
        avail = [a for a in raw_avail if a in allowed_action_ids]
    else:
        avail = raw_avail
    if not avail:
        return BFSResult(False, 0, None, "no available actions")

    try:
        action_specs = _iter_action_specs(
            available=avail,
            grid_w=gw,
            grid_h=gh,
            max_click_cells=max_click_cells,
            env=env,
        )
    except ValueError as e:
        return BFSResult(False, 0, None, str(e))

    q: deque[list[tuple[int, dict]]] = deque([[]])
    seen: set[tuple] = set()
    nodes = 0

    def state_tuple() -> tuple:
        li = g.level_index
        lc = env.observation_space.levels_completed
        st = env.observation_space.state
        ex = extra_state_key(env) if extra_state_key else b""
        return (li, lc, _frame_key(env), st, ex)

    while q:
        path = q.popleft()
        if len(path) > max_depth:
            continue
        nodes += 1
        if nodes > max_nodes:
            return BFSResult(False, nodes, None, f"max_nodes {max_nodes} exceeded")

        ok, res = replay(path)
        if not ok:
            continue
        li = g.level_index
        lc = env.observation_space.levels_completed
        st = env.observation_space.state

        if st == GameState.WIN or li > level_index or lc > start_lc:
            return BFSResult(True, nodes, len(path), "win")

        key = state_tuple()
        if key in seen:
            continue
        seen.add(key)

        for aid, data in action_specs:
            q.append(path + [(aid, data)])

    return BFSResult(False, nodes, None, "search exhausted")
