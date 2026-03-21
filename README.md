# ARC-Interactive

A collection of community games for the ARC-AGI-3 benchmark.

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

You can create games quickly with the patterns in [`AGENTS.md`](AGENTS.md) and the create-game skill (static levels are enough); games land in a community pool through normal repo contributions, so you can fork and share layouts; many stems live in one tree, so the catalog grows with `main` and is handy for probing mechanics; locally, `run_game.py --mode human` opens a **pygame** window (persistent grid + mouse clicks for ACTION6) before you automate; and Arcade plus `environment_files/` matches ARC-AGI / ARCEngine expectations.

## Quickstart

Requires [Python 3.12+](https://www.python.org/) and [uv](https://github.com/astral-sh/uv). From the repo root, install dependencies once:

```bash
uv sync
```

Run a game (tutorial **ez01**). **`--game` last** makes swapping stems a one-line edit. Local play uses **local environments** (`environment_files/`) by default; add optional **`--offline`** if you want to **force** that (same as omitting **`--online`** / **`--competition`**).

```bash
uv run python run_game.py \
  --version auto \
  --game ez01
```

**Local environments, explicit `--offline`** (same tutorial **ez01**):

```bash
uv run python run_game.py \
  --offline \
  --version auto \
  --game ez01
```

Discover stems: `uv run python run_game.py --list` (add **`--offline`** there too if you want a listing pinned to **local environments**). **`--version auto`** picks the sole package under that stem.

### Play by hand (pygame)

```bash
uv run python run_game.py \
  --offline \
  --version auto \
  --mode human \
  --game ez01
```

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

Paste into your coding agent (replace `{game_id}` and the bracketed design). Full checklist: [CONTRIBUTING.md](CONTRIBUTING.md#creating-a-new-game).

```
Implement a new ARC-AGI-3 game {game_id} at environment_files/{game_id}/v1/. Follow AGENTS.md and skills/create-arc-game/SKILL.md: static levels only, ARCBaseGame + metadata.json, register a row in GAMES.md. Game design: [grid size, entities, win/lose, which actions 1–7 do].
```

## Benchmarks

### Official ARC-AGI-3 (ARC Prize)

The primary benchmark and leaderboard for interactive reasoning is **[ARC-AGI-3](https://arcprize.org/arc-agi/3/)** from [ARC Prize](https://arcprize.org): 1,000+ levels across 150+ environments, scored partly on **action efficiency** (how many steps to the goal vs. humans). This repo ships **public environment** games compatible with that ecosystem; see the site for competition rules, toolkit, and human baselines.

### Kaggle

Community or parallel evaluation can use Kaggle-style task notebooks derived from this tree. From the repo root, generate notebooks (then attach a dataset with **`environment_files/`** and publish tasks on Kaggle as in [`benchmarks/README.md`](benchmarks/README.md)):

```bash
# Four canonical tasks → benchmarks/kaggle/notebooks/*.ipynb
python3 benchmarks/kaggle/rebuild_kaggle_notebooks.py

# One notebook per game stem → benchmarks/kaggle/notebooks/all/ (gitignored)
uv run python benchmarks/kaggle/export_kaggle_notebooks_all_stems.py
```

Local smoke (no hosted model): `uv run python -m benchmarks.kaggle.run_task_kbench_mock`. Papermill / proxy / region notes: [`benchmarks/kaggle/notebooks/README.md`](benchmarks/kaggle/notebooks/README.md).
