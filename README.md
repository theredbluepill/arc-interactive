# ARC-Interactive

A collection of community game environments for the ARC-AGI-3 benchmark.

<table align="center">
  <tr>
    <td align="center"><img src="assets/mm01.gif" alt="mm01 Memory Match" width="64" height="64" /></td>
    <td align="center"><img src="assets/sk01.gif" alt="sk01 Sokoban" width="64" height="64" /></td>
    <td align="center"><img src="assets/tb01.gif" alt="tb01 Bridge Builder" width="64" height="64" /></td>
    <td align="center"><img src="assets/rs01.gif" alt="rs01 Rule Switcher" width="64" height="64" /></td>
    <td align="center"><img src="assets/sy01.gif" alt="sy01 Mirror Maker" width="64" height="64" /></td>
    <td align="center"><img src="assets/tt01.gif" alt="tt01 Collection" width="64" height="64" /></td>
    <td align="center"><img src="assets/ms01.gif" alt="ms01 Blind Sapper" width="64" height="64" /></td>
    <td align="center"><img src="assets/ff01.gif" alt="ff01 Flood Fill" width="64" height="64" /></td>
  </tr>
  <tr>
    <td align="center"><code>mm01</code></td>
    <td align="center"><code>sk01</code></td>
    <td align="center"><code>tb01</code></td>
    <td align="center"><code>rs01</code></td>
    <td align="center"><code>sy01</code></td>
    <td align="center"><code>tt01</code></td>
    <td align="center"><code>ms01</code></td>
    <td align="center"><code>ff01</code></td>
  </tr>
</table>

<!-- Auto-updated on push to `main` when `GAMES.md` changes (see `.github/workflows/readme-stats.yml`, `devtools/scripts/update_readme_stats.py`). -->
<!-- readme-stats:begin -->

<p align="center">
  <a href="GAMES.md"><img src="https://img.shields.io/badge/250-INTERACTIVE_GAME-58A6FF?style=for-the-badge" alt="250 interactive games in registry" /></a>
  &nbsp;
  <a href="CONTRIBUTING.md#creating-a-new-game"><img src="https://img.shields.io/badge/Contributing-Add_an_interactive_game-238636?style=for-the-badge" alt="Contributing: add an interactive game" /></a>
</p>

<!-- readme-stats:end -->

## What for?

> The intelligence of a system is a measure of its skill-acquisition efficiency over a scope of tasks, with respect to priors, experience, and generalization difficulty.  
> — François Chollet, *[On the Measure of Intelligence](https://arxiv.org/abs/1911.01547)* (2019)

These games are designed to be easy for humans to solve, but very hard for modern AI systems—including frontier large language models. Together they stress reasoning, planning, and interactive control rather than memorized puzzle templates.

## Why use ARC-Interactive?

- **Hundreds of interactive ARC-AGI-3 games** in one registry ([`GAMES.md`](GAMES.md))—a broad test bed for agents, smoke tests, and benchmarks.
- Quickstart with **ARC-AGI-3** interactive play—the [ARC-AGI Toolkit](https://docs.arcprize.org/toolkit/overview), [competition mode](https://docs.arcprize.org/toolkit/competition_mode), actions and observations, and how games load from `environment_files/`.
- Create or modify games quickly using patterns in [`AGENTS.md`](AGENTS.md) and the skills under [`.opencode/skills/`](.opencode/skills/) (mirrored at [`skills/`](skills/)): [create-arc-game](.opencode/skills/create-arc-game/SKILL.md), [play-arc-game](.opencode/skills/play-arc-game/SKILL.md).
- Games land in a community pool through normal repo contributions.
- Many stems live in one tree, so the catalog grows with `main`.
- Powered by [ARC-AGI Toolkit](https://docs.arcprize.org/toolkit/overview).

## Quickstart

Requires [Python 3.12+](https://www.python.org/) and [uv](https://github.com/astral-sh/uv). From the repo root, install dependencies once:

```bash
uv sync
```

Run a game (tutorial **ez01**). **`--game` last** makes swapping stems a one-line edit. Omitting **`--mode`** defaults to **`random-agent`** (random **ACTION1–ACTION5** for **`--steps`**); the examples below set **`--mode random-agent`** explicitly. Local play uses **local environments** (`environment_files/`) by default; add optional **`--offline`** if you want to **force** that (same as omitting **`--online`** / **`--competition`**).

```bash
uv run python run_game.py \
  --version auto \
  --mode random-agent \
  --game ez01
```

**Local environments, explicit `--offline`** (same tutorial **ez01**):

```bash
uv run python run_game.py \
  --offline \
  --version auto \
  --mode random-agent \
  --game ez01
```

Discover stems: `uv run python run_game.py --list` (add **`--offline`** there too if you want a listing pinned to **local environments**). **`--version auto`** picks the sole package under that stem.

**Headless random smoke:** omit **`--mode`** or pass **`--mode random-agent`**; use **`--steps`** for how many random **ACTION1–ACTION5** steps to take (default 100). Example: `uv run python run_game.py --offline --version auto --mode random-agent --steps 50 --game ez01`.

### Human play

**`--mode human`** runs [`scripts/human_play_pygame.py`](scripts/human_play_pygame.py) (pygame). Abstract actions and human bindings are the same as in the official ARC Prize doc **[Actions](https://docs.arcprize.org/actions)**; each game still defines what ACTION1–7 mean.

| Action | Role |
| --- | --- |
| `RESET` | Initialize or restart |
| `ACTION1`–`ACTION4` | Simple actions (UI maps to up / down / left / right; semantics are game-specific) |
| `ACTION5` | Special (e.g. interact, rotate, execute) |
| `ACTION6` | Coordinate action (`x`, `y` in 0–63) |
| `ACTION7` | Undo |

Local pygame mapping (aligned with that doc’s WASD + Space and arrows + F schemes; digits `1`–`5` also send ACTION1–5):

| Input | Action |
| --- | --- |
| `W` / `↑`, `S` / `↓`, `A` / `←`, `D` / `→` (or `1`–`4`) | `ACTION1`–`ACTION4` |
| `Space` / `F` / `5` | `ACTION5` |
| Click grid | `ACTION6` |
| `U` or `Ctrl`/`Cmd`+`Z` | `ACTION7` |
| `R` | Restart (calls `environment.reset()`) |
| `Q` / `Esc` | Quit window |

```bash
uv run python run_game.py \
  --offline \
  --version auto \
  --mode human \
  --game ez01
```

Swap **`ez01`** for any stem from `uv run python run_game.py --list` (use **`--offline`** to list only local `environment_files/` packages).

### API / leaderboard / competition

**[three.arcprize.org](https://three.arcprize.org/)** — leaderboard, online play, and **`ARC_API_KEY`**. Only **online** runs count there; play against **local environments** does not.

1. Copy [`.env.example`](.env.example) → **`.env`** and set **`ARC_API_KEY`** (nothing else required in the template).
2. For API play, pass **`--online`** (registry) or **`--competition`** ([competition rules](https://docs.arcprize.org/toolkit/competition_mode), Kaggle-style) — pick one; they are mutually exclusive. Omit both to use **local environments** (same as Quickstart). More flags: **`uv run python run_game.py --help`**.

**Online** (registry):

```bash
uv run python run_game.py --online \
  --version auto \
  --game ls20
```

**Competition** toolkit mode:

```bash
uv run python run_game.py --competition \
  --version auto \
  --game ls20
```

`run_game.py` never passes **`scorecard_id`** into **`arc.make`** and does not call **`create_scorecard`**, **`get_scorecard`**, or **`close_scorecard`**. In **online** mode the toolkit may still attach play to its **default** scorecard ([Local vs Online](https://docs.arcprize.org/local-vs-online), [Get Scorecard](https://docs.arcprize.org/toolkit/get-scorecard)). For **custom** scorecards or create → close workflows: [Create Scorecard](https://docs.arcprize.org/toolkit/create-scorecard), [Close Scorecard](https://docs.arcprize.org/toolkit/close-scorecard).

### Create a game with AI Agent

Example prompt (replace `{game_id}` and the bracketed design):

```
Implement a new ARC-AGI-3 game {game_id} at environment_files/{game_id}/v1/. Follow AGENTS.md and .opencode/skills/create-arc-game/SKILL.md: static levels only, ARCBaseGame + metadata.json, register a row in GAMES.md. Game design: [grid size, entities, win/lose, which actions 1–7 do].
```

**Available skills** (under [`.opencode/skills/`](.opencode/skills/), mirrored at [`skills/`](skills/)):

- **[create-arc-game](.opencode/skills/create-arc-game/SKILL.md)** — End-to-end game design and implementation (`environment_files/`, `ARCBaseGame`, `metadata.json`, `GAMES.md`) aligned with [`AGENTS.md`](AGENTS.md).
- **[play-arc-game](.opencode/skills/play-arc-game/SKILL.md)** — Run and smoke-test stems with `run_game.py` (list, random agent, human pygame, offline/online flags).
- **[generate-arc-game-gif](.opencode/skills/generate-arc-game-gif/SKILL.md)** — GIF-ready `RenderableUserDisplay` and registry previews via `scripts/render_arc_game_gif.py`.

Full checklist: [CONTRIBUTING.md](CONTRIBUTING.md#creating-a-new-game).

## Community Benchmarks

### Kaggle

Community or parallel evaluation can use Kaggle-style task notebooks derived from this tree. From the repo root, generate notebooks (then attach a dataset with **`environment_files/`** and publish tasks on Kaggle as in [`benchmarks/README.md`](benchmarks/README.md)):

```bash
# Four canonical tasks → benchmarks/kaggle/notebooks/*.ipynb
python3 benchmarks/kaggle/rebuild_kaggle_notebooks.py

# One notebook per game stem → benchmarks/kaggle/notebooks/all/ (gitignored)
uv run python benchmarks/kaggle/export_kaggle_notebooks_all_stems.py
```

Local smoke (no hosted model): `uv run python -m benchmarks.kaggle.run_task_kbench_mock`. Papermill / proxy / region notes: [`benchmarks/kaggle/notebooks/README.md`](benchmarks/kaggle/notebooks/README.md).
