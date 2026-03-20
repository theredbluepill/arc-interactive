# ARC-Interactive

A collection of games for the ARC-AGI-3 benchmark.

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
  <a href="GAMES.md"><img src="https://img.shields.io/badge/169-INTERACTIVE_GAME-58A6FF?style=for-the-badge" alt="169 interactive games in registry" /></a>
  &nbsp;
  <a href="CONTRIBUTING.md#creating-a-new-game"><img src="https://img.shields.io/badge/Contributing-Add_an_interactive_game-238636?style=for-the-badge" alt="Contributing: add an interactive game" /></a>
</p>

<!-- readme-stats:end -->

## Quickstart

Requires [Python 3.12+](https://www.python.org/) and [uv](https://github.com/astral-sh/uv). From the repo root, install dependencies once:

```bash
uv sync
```

Then run a game (example: tutorial **ez01**):

```bash
uv run python run_game.py --game ez01 --version auto
```

Use any stem / version folder shown by `uv run python run_game.py --list`, or pass `--version auto` so the sole package under that stem is used.

### Online scorecard and scoring

`run_game.py` does not pass **`scorecard_id`** to **`arc.make`** or call **`create_scorecard`** / **`close_scorecard`** (see [Create](https://docs.arcprize.org/toolkit/create-scorecard), [Get](https://docs.arcprize.org/toolkit/get-scorecard), [Close](https://docs.arcprize.org/toolkit/close-scorecard)). For that flow, set **`ARC_API_KEY`** ([`.env.example`](.env.example)); the CLI loads repo-root **`.env`** on startup (via `python-dotenv` from `arc-agi`). Example: quickstarter §**5b** (`ls20`).

### Play by hand (matplotlib window)

```bash
uv run python run_game.py --game sk01 --version auto --mode human
```

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
