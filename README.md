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

<!-- Auto-updated on push to `main` when `GAMES.md` changes (see `.github/workflows/readme-stats.yml`, `devtools/scripts/update_readme_stats.py`). -->
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
uv run python run_game.py --game ez01 --version auto
```

Use any stem / version folder shown by `uv run python run_game.py --list`, or pass `--version auto` so the sole package under that stem is used.

Play by hand (matplotlib window):

```bash
uv run python run_game.py --game sk01 --version auto --mode human
```

## Kaggle Benchmarks

From the repo root, generate task notebooks (then attach a dataset with **`environment_files/`** and publish tasks on Kaggle as in [`benchmarks/README.md`](benchmarks/README.md)):

```bash
# Four canonical tasks → benchmarks/kaggle/notebooks/*.ipynb
python3 benchmarks/kaggle/rebuild_kaggle_notebooks.py

# One notebook per game stem → benchmarks/kaggle/notebooks/all/ (gitignored)
uv run python benchmarks/kaggle/export_kaggle_notebooks_all_stems.py
```

Local smoke (no hosted model): `uv run python -m benchmarks.kaggle.run_task_kbench_mock`. Papermill / proxy / region notes: [`benchmarks/kaggle/notebooks/README.md`](benchmarks/kaggle/notebooks/README.md).
