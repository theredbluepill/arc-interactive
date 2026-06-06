---
name: check-arc-game-solvable
description: >-
  Checks mechanical per-level solvability (a winning trajectory exists under the
  real game rules). Use when authoring or reviewing stems, after logic changes,
  or when debugging “impossible” puzzles. Complements discoverability review.
---

# Check ARC game mechanical solvability

## Soul of this skill

**Mechanical solvability** means: for each static authored level, there exists **some** sequence of legal actions under the **actual** `environment_files/` implementation that reaches the win condition (e.g. `next_level()`, goal state), without relying on hidden information or repo prose.

This is **not** the same as [check-arc-game-discoverable](../check-arc-game-discoverable/SKILL.md): discoverability asks whether a **cold-start participant can learn** goals and rules **through play**. A game can be mechanically solvable yet opaque, or discoverable yet broken if a level is mathematically unwinnable. **Both** matter for fair ARC-style tasks.

## Primary tool

From the repo root:

```bash
uv run python devtools/verify_level_solvability.py --stem <stem>
```

- Writes `devtools/reports/level_solvability.json` (and `--md` for Markdown).
- **`proved`** — harness found a witness or a stem-specific proof path.
- **`counterexample`** — harness believes the level is unwinnable under its model (investigate; may be harness gap).
- **`tooling_gap`** — no strict proof in this harness (see `notes` / [`devtools/solvers/registry.py`](../../devtools/solvers/registry.py)); do **not** assume “pass by omission.”

## Stem-specific proofs

When generic **engine BFS** is wrong or too large, the repo adds a dedicated strategy in `devtools/solvers/` and maps the stem in [`devtools/solvers/registry.py`](../../devtools/solvers/registry.py).

**Lights Out GF(2) (`lo02`, `lo03`, `lo05`):** orthogonal/king neighbors with torus wrap (lo02/lo03) and the **clipped** closed chess-knight neighborhood (lo05, `knight_clip` — no wrap) are checked with GF(2) linear algebra in [`devtools/solvers/torus_lights_gf2.py`](../../devtools/solvers/torus_lights_gf2.py). Initial `lights_on` layouts should be built by **forward simulation** (apply virtual clicks from all-off) so they lie in the reachable subspace — clipped kernels are rank-deficient (lo05's matrix is 56/64), so most hand-placed patterns are unreachable.

**Lattice / paint toggles (`gp02`, …):** may remain `TOOLING_GAP` until a dedicated checker exists; use witness generation or small-state proofs rather than guessing layouts.

## When changing level data

1. Run `verify_level_solvability.py` for the stem.
2. For toggle/grid linear games, re-run GF(2) or forward-click generation; **do not** copy patterns from bounded Lights Out without re-proving on **torus** rules.
3. Add or extend tests under `tests/` if you introduce a new proof path (see `tests/test_torus_lights_gf2.py`).

## Related references

- Discoverability bar: [check-arc-game-discoverable](../check-arc-game-discoverable/SKILL.md)
- Authoring workflow: [AGENTS.md](../../AGENTS.md), [create-arc-game](../create-arc-game/SKILL.md)
