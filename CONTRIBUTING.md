# Contributing

This guide covers how to run and create games for the ARC-AGI-3 benchmark. You can implement games by hand or **use an AI coding agent** (Cursor, Copilot, etc.) with the files linked below—the repo is set up so agents can follow one skill and land a complete game.

## Table of contents

- [Ways to contribute](#ways-to-contribute)
- [Prerequisites](#prerequisites)
- [Running games](#running-games)
  - [List available games](#list-available-games)
  - [Run a game](#run-a-game)
  - [Interactive play](#interactive-play)
  - [Auto mode (random actions)](#auto-mode-random-actions)
- [Creating a new game](#creating-a-new-game)
  - [AI-assisted workflow](#ai-assisted-workflow-recommended-for-speed)
- [Key patterns](#key-patterns)
  - [Camera](#camera)
  - [Action space](#action-space)
  - [Target collection](#target-collection)
- [Repository structure](#repository-structure)
- [Issues and pull requests](#issues-and-pull-requests)
- [Documentation](#documentation)

## Ways to contribute

You do not have to ship a full game to help. Pick a track that matches your goal; [AGENTS.md](AGENTS.md) and the skills under [`skills/`](skills/) apply to both humans and agents.

| Track | What you might do | Primary references |
|-------|-------------------|--------------------|
| **New or updated games** | Add a stem under `environment_files/`, register in [GAMES.md](GAMES.md), metadata, smoke tests | [skills/create-arc-game/SKILL.md](skills/create-arc-game/SKILL.md), [AGENTS.md](AGENTS.md) |
| **Playtesting and repro** | Run games locally, file issues with repro steps, verify regressions | [skills/play-arc-game/SKILL.md](skills/play-arc-game/SKILL.md), [run_game.py](run_game.py) |
| **Preview GIFs and registry media** | HUD-ready captures, `registry_gif_*`, `assets/*.gif` | [skills/generate-arc-game-gif/SKILL.md](skills/generate-arc-game-gif/SKILL.md), [scripts/render_arc_game_gif.py](scripts/render_arc_game_gif.py) |
| **Design review (discoverability)** | Cold-start clarity; goals and rules learnable from observation; fair shared interface for humans and agents | [skills/check-arc-game-discoverable/SKILL.md](skills/check-arc-game-discoverable/SKILL.md) |
| **Mechanical solvability** | Per-level winnability under the real `step()` rules; complements discoverability | [skills/check-arc-game-solvable/SKILL.md](skills/check-arc-game-solvable/SKILL.md), [`devtools/verify_level_solvability.py`](devtools/verify_level_solvability.py) |
| **Tooling and CI** | `devtools/`, workflows, registry checks, similarity reports | [Issues and pull requests](#issues-and-pull-requests), [`devtools/`](devtools/) |
| **Documentation** | README, this guide, [GAMES.md](GAMES.md) rows, triage guides | [Documentation](#documentation), [devtools/SIMILARITY_TRIAGE.md](devtools/SIMILARITY_TRIAGE.md) |

The **create-arc-game**, **play-arc-game**, **generate-arc-game-gif**, **check-arc-game-discoverable**, and **check-arc-game-solvable** skills live under repo root **`skills/`**. **`.opencode/skills/`**, **`.agents/skills/`**, and **`.claude/skills/`** are symlinks to **`skills/`** for different tool layouts—use whichever path your tool resolves best.

## Prerequisites

This project uses [uv](https://github.com/astral-sh/uv) for dependency management.

## Running Games

### List Available Games
```bash
uv run python run_game.py --list
```

### Run a Game
```bash
uv run python run_game.py --game ez01 --version auto
```

### Interactive Play
```bash
uv run python run_game.py --game ez01 --version auto --mode terminal
```

Controls (actions are abstract - each game defines what they mean):
- `1-4`: Primary actions (can be movement, rotation, firing, etc.)
- `5`: Special action (interact, select, rotate, attach/detach, etc.)
- `6`: Coordinate-based action (click at position)
- `7`: Undo
- `q`: Quit

### Auto Mode (Random Actions)
```bash
uv run python run_game.py --game ez01 --version auto --mode random-agent --steps 50
```

## Creating a New Game

### AI-assisted workflow (recommended for speed)

Point your agent at the same conventions humans use:

| Resource | What it’s for |
|----------|----------------|
| [AGENTS.md](AGENTS.md) | Camera/UI patterns, abstract actions, common bugs, testing checklist, palette |
| [skills/create-arc-game/SKILL.md](skills/create-arc-game/SKILL.md) | End-to-end steps: layout, sprites, levels, `step()`, metadata, registry |
| [skills/play-arc-game/SKILL.md](skills/play-arc-game/SKILL.md) | Running and validating games locally (`run_game.py` modes, controls) |
| [skills/generate-arc-game-gif/SKILL.md](skills/generate-arc-game-gif/SKILL.md) | Preview GIFs: `RenderableUserDisplay` GIF-readiness, `scripts/render_arc_game_gif.py` |
| [skills/check-arc-game-discoverable/SKILL.md](skills/check-arc-game-discoverable/SKILL.md) | Discovery-through-play review: goals and rules fair from observation |
| [skills/check-arc-game-solvable/SKILL.md](skills/check-arc-game-solvable/SKILL.md) | Mechanical solvability: `devtools/verify_level_solvability.py`, reports |

See [Ways to contribute](#ways-to-contribute) for how these map to contribution types and symlink paths.

**Minimal prompt you can paste** (replace `{game_id}` with your stem, e.g. `ez01`):

```text
Implement a new ARC-AGI-3 game {game_id} at environment_files/{game_id}/v1/. Follow AGENTS.md, CONTRIBUTING.md, and skills/create-arc-game/SKILL.md: static levels only, ARCBaseGame + metadata.json, register a row in GAMES.md. Game design: [grid size, entities, win/lose, which actions 1–7 do].
```

**Done when:** `uv run python run_game.py --game {game_id} --version auto` runs, win advances levels, and [GAMES.md](GAMES.md) has a complete table row (optional: preview GIF under `assets/` like existing games).

If you prefer to implement without an agent, follow the numbered steps below.

### 1. Create Game Directory
```
environment_files/{game_id}/{version}/
├── {game_id}.py
└── metadata.json
```

### 2. Implement Game

Follow the patterns from established games in `environment_files/`.

**Basic structure:**
```python
from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)

# Define sprites
sprites = {
    "player": Sprite(pixels=[[9]], name="player", visible=True, collidable=True, tags=["player"]),
    "target": Sprite(pixels=[[4]], name="target", visible=True, collidable=False, tags=["target"]),
}

# Define levels
levels = [
    Level(
        sprites=[
            sprites["player"].clone().set_position(1, 1),
            sprites["target"].clone().set_position(3, 3),
        ],
        grid_size=(8, 8),
        data={"difficulty": 1},
    ),
]

class MyGame(ARCBaseGame):
    def __init__(self) -> None:
        self._ui = MyGameUI(0)
        super().__init__(
            "mygame",
            levels,
            Camera(0, 0, 8, 8, 0, 4, [self._ui]),
            False,
            1,
            [1, 2, 3, 4],
        )

    def on_set_level(self, level: Level) -> None:
        self._player = self.current_level.get_sprites_by_tag("player")[0]
        self._targets = self.current_level.get_sprites_by_tag("target")

    def step(self) -> None:
        # Handle actions (abstract - define what they mean for YOUR game)
        if self.action.id.value == 1:
            # ACTION1 - could be movement, rotation, firing, etc.
            dy = -1
        elif self.action.id.value == 2:
            dy = 1
        elif self.action.id.value == 3:
            dx = -1
        elif self.action.id.value == 4:
            dx = 1
        
        # ... game logic ...
        
        self.complete_action()
```

### 3. Add Metadata
```json
{
  "game_id": "mygame-v1",
  "title": "My Game",
  "description": "Game description",
  "default_fps": 20,
  "baseline_actions": [15],
  "tags": ["static"],
  "local_dir": "environment_files/mygame/v1",
  "date_created": "2026-03-18"
}
```

### 4. Register Game

Add entry to [GAMES.md](GAMES.md):
```markdown
| mygame | 8×8 | 1 | Description here. | | • 1-4: Actions |
```

### 5. Test
```bash
uv run python run_game.py --game mygame --version auto
```

### 6. Registry distinctiveness (similarity)

After adding or heavily refactoring multiple stems, or bulk-editing shared templates, regenerate the automated scan so false “same levels” or ambiguous cross-family pairs surface early:

```bash
uv run python devtools/similar_games_report.py --only-games-md --top-k 12 --min-score 0.25
```

Optional: add `--suspicious-min-score 0.40` when you want **smaller** overlap components (stronger edges) without raising the main pair threshold. Outputs land in [`devtools/reports/similar_games.md`](devtools/reports/similar_games.md) and [`devtools/reports/similar_games.json`](devtools/reports/similar_games.json).

**Triage** — For high-scoring or suspicious pairs, follow [`devtools/SIMILARITY_TRIAGE.md`](devtools/SIMILARITY_TRIAGE.md): compare `step()` and HUD; if `same_levels_fingerprint` is true across unrelated prefixes, diff `levels = …` sources; prefer **GAMES.md** lead + **metadata** (`tags`, `physics_rules`) before large refactors; smoke affected stems with [`devtools/smoke_games.py`](devtools/smoke_games.py); append one line to **Resolved notes** when a cluster is closed.

**New stem checklist** (also in the [create-arc-game](skills/create-arc-game/SKILL.md) skill):

- [ ] **GAMES.md** row: first sentence states the **unique** rule; for `xx02` / `xx03`, prefix **Variant of `xx01`.** where helpful.
- [ ] **`metadata.json`**: `description`, `tags`, and `physics_rules` (if used) match `step()`.
- [ ] **HUD** encodes the main constraint the agent/human cannot infer from tiles alone.
- [ ] Avoid **verbatim** `levels = …` one-liners copied from unrelated stems (raises false level fingerprint).
- [ ] Run `smoke_games.py` for the new stem; regenerate the similarity report if the change is large.

CI uploads an **advisory** report artifact (no fail gate) on relevant PRs — [`.github/workflows/similar-games-report.yml`](.github/workflows/similar-games-report.yml).

## Key Patterns

### Camera
Camera must match your largest level's grid size:
```python
Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR)
```

### Action Space
Actions are **abstract** - each game defines what they mean:

| Action | Description |
|--------|-------------|
| ACTION1 | Abstract 1 (semantically up) |
| ACTION2 | Abstract 2 (semantically down) |
| ACTION3 | Abstract 3 (semantically left) |
| ACTION4 | Abstract 4 (semantically right) |
| ACTION5 | Special (interact, select, rotate, etc.) |
| ACTION6 | Coordinate-based (x,y required) |
| ACTION7 | Undo |

### Target Collection
```python
# Must use ignore_collidable=True for targets
sprite = self.current_level.get_sprite_at(x, y, ignore_collidable=True)

# Check target first (before checking collidable)
if sprite and "target" in sprite.tags:
    self.current_level.remove_sprite(sprite)
elif not sprite or not sprite.is_collidable:
    self._player.set_position(new_x, new_y)
```

## Repository Structure

```
arc-interactive/
├── devtools/                # `smoke_games.py`, `check_registry.py` (CI / local; see Issues & PRs below)
├── environment_files/     # All games
│   ├── ez01/<ver>/
│   ├── tt01/<ver>/
│   └── ...
├── skills/                  # Agent skills (create / play / gif / discoverable / solvable); canonical copy
├── .opencode/skills/        # Symlink → ../skills (OpenCode)
├── .agents/skills/          # Symlink → ../skills (Cursor agents)
├── .claude/skills/          # Symlink → ../skills (Claude Code)
├── assets/                  # Game preview GIFs
├── run_game.py              # CLI runner
├── AGENTS.md                # Agent + human patterns for games
├── GAMES.md                 # Game registry
├── README.md                # Quick start
└── CONTRIBUTING.md          # This guide
```

## Issues and pull requests

Use the repo’s [issue templates](.github/ISSUE_TEMPLATE/) (bug report, game idea / feature) and [pull request template](.github/PULL_REQUEST_TEMPLATE.md) so reports include game IDs, repro steps, and the same `run_game.py` checks as above. Blank issues stay enabled if none of the templates fit.

Pull requests that change files under `environment_files/` are **smoke-tested in CI** (`devtools/smoke_games.py` via [`.github/workflows/pr-game-smoke.yml`](.github/workflows/pr-game-smoke.yml)): each affected game is loaded and stepped with random ACTION1–5. That catches load/`step()` crashes and missing `GAMES.md` rows; it does not replace manual or agent review for design and solvability.

**Package version folders (commit short SHA, same idea as `ls20/cb3b57cc`)** — One-shot bulk rename from `v1/` is [`devtools/migrate_all_v1_to_sha.py`](devtools/migrate_all_v1_to_sha.py); day-to-day, [`.github/workflows/bump-env-versions.yml`](.github/workflows/bump-env-versions.yml) runs on same-repo PRs that touch `environment_files/**`. It renames any changed `environment_files/<stem>/<old>/` tree to `environment_files/<stem>/<8-hex-of-PR-head>/`, rewrites that folder’s `metadata.json` (`game_id`, `local_dir`, `date_downloaded`), and removes `<old>`. Stems `vc33`, `ls20`, and `ft09` are skipped (see [`devtools/bump_env_versions.py`](devtools/bump_env_versions.py)). Fork PRs are skipped (no push permission). The repo needs **Settings → Actions → General → Workflow permissions → Read and write** so the workflow can push the bump commit. Commits containing `[env-version-bump]` are not processed again (avoids loops). You can still start from `v1` locally; the first push that changes the game will retag the folder.

Optional local checks (not in CI by default):

- **Full-table smoke with ACTION6** — [`devtools/smoke_registry_games.py`](devtools/smoke_registry_games.py): e.g. `uv run python devtools/smoke_registry_games.py --from pb01 --through bn03 --steps 80`
- **Batch preview GIFs (multi-level + wall-bump “fails”)** — [`scripts/render_arc_game_gif.py`](scripts/render_arc_game_gif.py) + [`scripts/registry_gif_lib.py`](scripts/registry_gif_lib.py); per-stem tuning in [`scripts/registry_gif_overrides.json`](scripts/registry_gif_overrides.json). Example: `uv run python scripts/render_arc_game_gif.py --from pb01 --through bn03`. Pending/backfill: add `--pending` (see [`skills/generate-arc-game-gif/SKILL.md`](skills/generate-arc-game-gif/SKILL.md)).

Other automation:

- **Similar games report (advisory)** — [`devtools/similar_games_report.py`](devtools/similar_games_report.py) on [`similar-games-report.yml`](.github/workflows/similar-games-report.yml): Jaccard-style code overlap + level fingerprints from `GAMES.md` / `environment_files/`; downloads `similar_games.md` / `.json` from the workflow run artifact. Does **not** fail PRs; use [`devtools/SIMILARITY_TRIAGE.md`](devtools/SIMILARITY_TRIAGE.md) to interpret results.
- **Registry check** — [`devtools/check_registry.py`](devtools/check_registry.py) on [`pr-registry.yml`](.github/workflows/pr-registry.yml): `metadata.json` shape, `game_id` / `local_dir`, `GAMES.md` rows vs disk (reference stems `vc33` / `ls20` / `ft09` are intentionally omitted from the table; see script).
- **Ruff** — [`pr-ruff.yml`](.github/workflows/pr-ruff.yml) runs on `devtools/` (including `devtools/scripts/`), `run_game.py`, and related paths when those appear in the PR diff; use **Actions → PR Ruff → Run workflow** for a full pass on that surface.
- **Labels** — [`labeler.yml`](.github/labeler.yml) (via [`labeler` workflow](.github/workflows/labeler.yml)) tags PRs by area (`game`, `documentation`, `ci`, `devtools`).
- **Dependabot** — [`.github/dependabot.yml`](.github/dependabot.yml) bumps GitHub Actions and `uv` dependencies weekly.
- **Official stem overlap** — [`.github/workflows/official-stem-overlap.yml`](.github/workflows/official-stem-overlap.yml) runs weekly (and manually); it needs the **`ARC_API_KEY`** repository secret and may open a bot PR with [`devtools/reports/official_stem_overlap.md`](devtools/reports/official_stem_overlap.md) when remote catalog stems collide with local packages. Ignored stems are **read from** the create-arc-game skill **`## Examples`** (concrete `environment_files/<stem>/<8-hex>/` paths); see [`devtools/check_official_stem_overlap.py`](devtools/check_official_stem_overlap.py).
- **First PR welcome** — static comment with links (no code from the PR is executed).

Maintainers: turn on **required status checks** for `main` as described in [`.github/BRANCH_PROTECTION.md`](.github/BRANCH_PROTECTION.md).

## Documentation

- [ARC-AGI-3 Docs](https://docs.arcprize.org/add_game)
- [AGENTS.md](AGENTS.md) — implementation patterns and pitfalls
- [SIMILARITY_TRIAGE.md](devtools/SIMILARITY_TRIAGE.md) — interpreting the similar-games report and resolving false positives
- [Game Registry](GAMES.md)
- Agent skills (**`skills/`** at repo root; **`.opencode/skills/`** / **`.agents/skills/`** / **`.claude/skills/`** symlink there): **create-arc-game**, **play-arc-game**, **generate-arc-game-gif**, **check-arc-game-discoverable**, **check-arc-game-solvable**
