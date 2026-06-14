"""GF(2) solvability for Lights Out toggles, matching lo02/lo03/lo05 ``step()``.

Modes: ``orth``/``king`` wrap on the torus (lo02/lo03); ``knight_clip`` is the
closed chess-knight neighborhood CLIPPED at the board edge (lo05 — no wrap)."""

from __future__ import annotations

from typing import Literal

ToggleMode = Literal["orth", "king", "knight_clip"]


def _cell_index(gw: int, gx: int, gy: int) -> int:
    return gy * gw + gx


def _orth_neighbors(gw: int, gh: int, gx: int, gy: int) -> list[tuple[int, int]]:
    return [
        ((gx - 1) % gw, gy),
        ((gx + 1) % gw, gy),
        (gx, (gy - 1) % gh),
        (gx, (gy + 1) % gh),
    ]


def _king_neighbors(gw: int, gh: int, gx: int, gy: int) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            out.append(((gx + dx) % gw, (gy + dy) % gh))
    return out


_KNIGHT = (
    (2, 1),
    (1, 2),
    (-1, 2),
    (-2, 1),
    (-2, -1),
    (-1, -2),
    (1, -2),
    (2, -1),
)


def _knight_neighbors_clipped(gw: int, gh: int, gx: int, gy: int) -> list[tuple[int, int]]:
    return [
        (gx + dx, gy + dy)
        for dx, dy in _KNIGHT
        if 0 <= gx + dx < gw and 0 <= gy + dy < gh
    ]


def click_affected_cells(
    gw: int,
    gh: int,
    cx: int,
    cy: int,
    walls: set[tuple[int, int]],
    *,
    mode: ToggleMode,
) -> list[tuple[int, int]]:
    """Cells toggled when clicking (cx, cy); walls are skipped (not toggled)."""
    if (cx, cy) in walls:
        return []
    if mode == "orth":
        raw = [(cx, cy)] + _orth_neighbors(gw, gh, cx, cy)
    elif mode == "king":
        raw = [(cx, cy)] + _king_neighbors(gw, gh, cx, cy)
    else:
        raw = [(cx, cy)] + _knight_neighbors_clipped(gw, gh, cx, cy)
    return [(tx, ty) for tx, ty in raw if (tx, ty) not in walls]


def apply_click(
    lit: set[tuple[int, int]],
    gw: int,
    gh: int,
    cx: int,
    cy: int,
    walls: set[tuple[int, int]],
    *,
    mode: ToggleMode,
) -> None:
    for tx, ty in click_affected_cells(gw, gh, cx, cy, walls, mode=mode):
        p = (tx, ty)
        if p in lit:
            lit.remove(p)
        else:
            lit.add(p)


def lights_from_virtual_clicks(
    gw: int,
    gh: int,
    walls: set[tuple[int, int]],
    clicks: list[tuple[int, int]],
    *,
    mode: ToggleMode,
) -> set[tuple[int, int]]:
    """Start from all-off; apply clicks in order (same semantics as the game)."""
    lit: set[tuple[int, int]] = set()
    for cx, cy in clicks:
        apply_click(lit, gw, gh, cx, cy, walls, mode=mode)
    return lit


def _row_mask_for_cell(
    gw: int,
    gh: int,
    walls: set[tuple[int, int]],
    gx: int,
    gy: int,
    *,
    mode: ToggleMode,
) -> int:
    """Bitmask over click variables: which clicks affect lit state at (gx, gy)."""
    mask = 0
    for cgy in range(gh):
        for cgx in range(gw):
            if (cgx, cgy) in walls:
                continue
            idx = _cell_index(gw, cgx, cgy)
            affected = click_affected_cells(gw, gh, cgx, cgy, walls, mode=mode)
            if (gx, gy) in affected:
                mask |= 1 << idx
    return mask


def _rref_gf2(aug: list[int], n_vars: int) -> tuple[bool, list[int]]:
    """RREF over GF(2); return (consistent, one solution with free vars = 0)."""
    rows = len(aug)
    r = 0
    pivot_row_for_col: dict[int, int] = {}
    for col in range(n_vars):
        pivot = None
        for rr in range(r, rows):
            if (aug[rr] >> col) & 1:
                pivot = rr
                break
        if pivot is None:
            continue
        aug[r], aug[pivot] = aug[pivot], aug[r]
        for rr in range(rows):
            if rr != r and ((aug[rr] >> col) & 1):
                aug[rr] ^= aug[r]
        pivot_row_for_col[col] = r
        r += 1

    for rr in range(rows):
        lhs = aug[rr] & ((1 << n_vars) - 1)
        rhs = (aug[rr] >> n_vars) & 1
        if rhs and lhs == 0:
            return False, [0] * n_vars

    x = [0] * n_vars
    for col, pr in pivot_row_for_col.items():
        x[col] = (aug[pr] >> n_vars) & 1
    return True, x


def is_solvable(
    lights_on: set[tuple[int, int]] | list[tuple[int, int]],
    walls: set[tuple[int, int]] | list[tuple[int, int]],
    gw: int,
    gh: int,
    *,
    mode: ToggleMode,
) -> bool:
    """Whether ``lights_on`` can be cleared with some click sequence."""
    lit_set = {(int(a), int(b)) for a, b in lights_on}
    wall_set = {(int(a), int(b)) for a, b in walls}
    n = gw * gh
    b = 0
    for gx, gy in lit_set:
        b |= 1 << _cell_index(gw, gx, gy)
    aug: list[int] = []
    for gy in range(gh):
        for gx in range(gw):
            rowm = _row_mask_for_cell(gw, gh, wall_set, gx, gy, mode=mode)
            rhs = (b >> _cell_index(gw, gx, gy)) & 1
            aug.append(rowm | (rhs << n))
    ok, _ = _rref_gf2(aug, n)
    return ok


def solve_clicks_mask(
    lights_on: set[tuple[int, int]] | list[tuple[int, int]],
    walls: set[tuple[int, int]] | list[tuple[int, int]],
    gw: int,
    gh: int,
    *,
    mode: ToggleMode,
) -> tuple[bool, int]:
    """Return (ok, bitmask over click variables: 1 = press that cell)."""
    lit_set = {(int(a), int(b)) for a, b in lights_on}
    wall_set = {(int(a), int(b)) for a, b in walls}
    n = gw * gh
    b = 0
    for gx, gy in lit_set:
        b |= 1 << _cell_index(gw, gx, gy)
    aug: list[int] = []
    for gy in range(gh):
        for gx in range(gw):
            rowm = _row_mask_for_cell(gw, gh, wall_set, gx, gy, mode=mode)
            rhs = (b >> _cell_index(gw, gx, gy)) & 1
            aug.append(rowm | (rhs << n))
    ok, x_list = _rref_gf2(aug, n)
    if not ok:
        return False, 0
    mask = 0
    for c, bit in enumerate(x_list):
        if bit:
            mask |= 1 << c
    return True, mask


def level_payload_solvable(
    level_data: dict,
    grid_size: tuple[int, int],
    *,
    mode: ToggleMode,
) -> bool:
    """``level_data`` has ``lights_on`` (list of pairs); walls from sprite list optional."""
    gw, gh = int(grid_size[0]), int(grid_size[1])
    raw_lit = level_data.get("lights_on") or []
    lights = {(int(t[0]), int(t[1])) for t in raw_lit}
    walls: set[tuple[int, int]] = set()
    return is_solvable(lights, walls, gw, gh, mode=mode)


def arc_level_is_solvable(level, *, mode: ToggleMode) -> bool:
    """``arcengine.level.Level`` from a loaded game module (``lights_on`` data + wall sprites)."""
    gw, gh = level.grid_size
    raw = level.get_data("lights_on") or []
    lights = {(int(p[0]), int(p[1])) for p in raw}
    walls = {(s.x, s.y) for s in level.get_sprites_by_tag("wall")}
    return is_solvable(lights, walls, gw, gh, mode=mode)
