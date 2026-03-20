# ARC-AGI-3 Games

A collection of games for the ARC-AGI-3 benchmark.

<!-- Auto-updated on push to `main` when `GAMES.md` or `environment_files/` change (see `.github/workflows/readme-stats.yml`). -->
<!-- readme-stats:begin -->

<!-- Typing animation: readme-typing-svg.demolab.com (external); multiline stack (no wipe). -->
<p align="center">
  <img src="https://readme-typing-svg.demolab.com/?lines=44+games+in+GAMES.md%3B47+runnable+packages+in+environment_files%2F%3BCounts+differ+%E2%80%94+sync+GAMES.md+with+disk&font=VT323&size=28&pause=700&duration=2200&color=58A6FF&center=true&vCenter=true&width=600&height=127&multiline=true&repeat=true" alt="44 games in GAMES.md; 47 runnable packages in environment_files/; registry and disk counts differ" />
</p>

<!-- readme-stats:end -->

See [GAMES.md](GAMES.md) for the complete game registry with previews.

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

See [CONTRIBUTING.md](CONTRIBUTING.md) for full documentation on running and creating games.

## Kaggle Benchmarks

If you’ve finished Kaggle-side setup—a **dataset** whose root contains **`environment_files/`**, one or more **published benchmark tasks** built from [`benchmarks/kaggle/arc_kaggle_notebook_template.py`](benchmarks/kaggle/arc_kaggle_notebook_template.py), and those tasks **added to a benchmark**—you’re aligned with this repo’s layout. Operational details (bootstrap deps for papermill vs Python 3.12, optional notebook regeneration, model proxy / region notes) live in **[`benchmarks/README.md`](benchmarks/README.md)** and **[`benchmarks/kaggle/notebooks/README.md`](benchmarks/kaggle/notebooks/README.md)**.

Local checks without calling the hosted model:

```bash
uv run python -m benchmarks.kaggle.run_task_kbench_mock
```
