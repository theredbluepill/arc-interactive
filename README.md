# ARC-Interactive

A collection of games for the ARC-AGI-3 benchmark.

<p align="center">
  <img src="assets/mm01.gif" alt="mm01 Memory Match" width="64" height="64" />
  &nbsp;
  <img src="assets/sk01.gif" alt="sk01 Sokoban" width="64" height="64" />
  &nbsp;
  <img src="assets/tb01.gif" alt="tb01 Bridge Builder" width="64" height="64" />
  &nbsp;
  <img src="assets/rs01.gif" alt="rs01 Rule Switcher" width="64" height="64" />
  &nbsp;
  <img src="assets/sy01.gif" alt="sy01 Mirror Maker" width="64" height="64" />
  &nbsp;
  <img src="assets/tt01.gif" alt="tt01 Collection" width="64" height="64" />
  &nbsp;
  <img src="assets/ms01.gif" alt="ms01 Blind Sapper" width="64" height="64" />
  &nbsp;
  <img src="assets/ff01.gif" alt="ff01 Flood Fill" width="64" height="64" />
</p>

<!-- Auto-updated on push to `main` when `GAMES.md` changes (see `.github/workflows/readme-stats.yml`). -->
<!-- readme-stats:begin -->

<p align="center">
  <a href="GAMES.md"><img src="https://img.shields.io/badge/134-INTERACTIVE_GAME-58A6FF?style=for-the-badge" alt="134 interactive games in registry" /></a>
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
uv run python run_game.py --game ez01 --version v1
```

Use any `game_id` / `version` pair that appears in `uv run python run_game.py --list`.

## Kaggle Benchmarks

If you’ve finished Kaggle-side setup—a **dataset** whose root contains **`environment_files/`**, one or more **published benchmark tasks** built from [`benchmarks/kaggle/arc_kaggle_notebook_template.py`](benchmarks/kaggle/arc_kaggle_notebook_template.py), and those tasks **added to a benchmark**—you’re aligned with this repo’s layout. Operational details (bootstrap deps for papermill vs Python 3.12, optional notebook regeneration, model proxy / region notes) live in **[`benchmarks/README.md`](benchmarks/README.md)** and **[`benchmarks/kaggle/notebooks/README.md`](benchmarks/kaggle/notebooks/README.md)**.

Local checks without calling the hosted model:

```bash
uv run python -m benchmarks.kaggle.run_task_kbench_mock
```
