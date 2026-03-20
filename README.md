# ARC-AGI-3 Games

A collection of games for the ARC-AGI-3 benchmark.

It is a **working** copy you can run on your own machine: play in the terminal, hook up agents, read or change how levels work, ship new games, or reuse the same `environment_files/` layout in evaluation pipelines (including the optional Kaggle hooks below). No single "intended" role—pick whatever fits your project.

## Games

<!-- Auto-updated on push to `main` when `GAMES.md` or `environment_files/` change (see `.github/workflows/readme-stats.yml`). -->
<!-- readme-stats:begin -->

- **Games listed in [GAMES.md](GAMES.md):** 44
- **Runnable packages in `environment_files/`:** 47 (`game_id` + version folder with `metadata.json`)
- *Counts differ — sync the registry table with on-disk packages when you add or remove games.*

<!-- readme-stats:end -->

See [GAMES.md](GAMES.md) for the complete game registry with previews.

## Quick Run

Requires [Python 3.12+](https://www.python.org/) and [uv](https://github.com/astral-sh/uv). From the repo root, install dependencies once:

```bash
uv sync
```

Then run a game (example: tutorial **ez01**):

```bash
uv run python run_game.py --game ez01 --version v1
```

Use any `game_id` / `version` pair that appears in `uv run python run_game.py --list`.

See [CONTRIBUTING.md](CONTRIBUTING.md) for full documentation on running and creating games.

## Kaggle Benchmarks

If you’ve finished Kaggle-side setup—a **dataset** whose root contains **`environment_files/`**, one or more **published benchmark tasks** built from [`benchmarks/kaggle/arc_kaggle_notebook_template.py`](benchmarks/kaggle/arc_kaggle_notebook_template.py), and those tasks **added to a benchmark**—you’re aligned with this repo’s layout. Operational details (bootstrap deps for papermill vs Python 3.12, optional notebook regeneration, model proxy / region notes) live in **[`benchmarks/README.md`](benchmarks/README.md)** and **[`benchmarks/kaggle/notebooks/README.md`](benchmarks/kaggle/notebooks/README.md)**.

Local checks without calling the hosted model:

```bash
uv run python -m benchmarks.kaggle.run_task_kbench_mock
```
