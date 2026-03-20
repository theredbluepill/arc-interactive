# ARC-AGI-3 Benchmarks

Benchmarks for evaluating AI models on ARC-AGI-3 games, including Kaggle benchmark tasks (e.g. [Measuring Progress Toward AGI](https://www.kaggle.com/competitions/kaggle-measuring-agi)).

## Structure

- **`arc_game_wrapper.py`** – Run ARC games with an LLM: frame → text prompt, parse digit actions, game loop. Stops on `WIN`, `LOSE`, `LOST`, or **`GAME_OVER`** (e.g. sv01 death). Prompts treat ACTION1–7 as **game-defined** (IDs 1–4 are not guaranteed to mean up/down/left/right; see [ARC Actions](https://docs.arcprize.org/actions)). Use `default_action_help()` for 4- vs 5-ID prompts without hard-coding semantics.
- **`mock_llms.py`** – `ReplayMockLLM` / `ConstantMockLLM` for local smoke tests without the Model Proxy.
- **`kaggle/`** – `@kbench.task` definitions using [kaggle-benchmarks](https://pypi.org/project/kaggle-benchmarks/).

## Kaggle tasks (executive / cognitive suite)

| Task name | Game stem | Grid crop | Default `max_steps` | Success |
|-----------|-----------|-----------|---------------------|---------|
| `arc_ez01_go_up` | ez01 | 8 | 30 | ≥ 1 level |
| `arc_sk01_sokoban` | sk01 | 16 | 200 | ≥ 1 level |
| `arc_tt01_collect` | tt01 | 24 | 200 | ≥ 1 level |
| `arc_sv01_survive` | sv01 | 24 | 80 | ≥ 1 level (60 survival steps each) |

Full `game_id` strings come from each package’s `metadata.json` (resolved in `arc_tasks.py` via `scripts/env_resolve.py`).

Source of truth: `benchmarks/kaggle/arc_tasks.py` (`ARC_TASK_NAMES`).  
`benchmarks/kaggle/arc_ez01_task.py` re-exports `arc_ez01_go_up` for backward compatibility.

### Running locally

Configure a `.env` in the repo root (Model Proxy):

```env
MODEL_PROXY_URL=https://mp-staging.kaggle.net/models/openapi
MODEL_PROXY_API_KEY=your_token
LLM_DEFAULT=google/gemini-2.5-flash
```

Obtain `MODEL_PROXY_API_KEY` from the [Kaggle Models API onboarding](https://www.kaggle.com/models-api-onboarding-packet).

Then:

```bash
uv run python -m benchmarks.kaggle.arc_ez01_task
```

Wrapper smoke test (always move up on ez01, no kaggle_benchmarks; repo root on `PYTHONPATH`):

```bash
PYTHONPATH=. uv run python benchmarks/run_task_test.py
```

All four `@kbench.task` entries with **mock** LLMs (no proxy HTTP to a real model):

```bash
uv run python -m benchmarks.kaggle.run_task_kbench_mock
```

### Publishing to Kaggle Benchmarks

1. **Dataset** – Zip and upload **`environment_files/`** (full tree is simplest so every stem’s package dir resolves). On Kaggle it appears under e.g. **`/kaggle/input/datasets/poonszesen/arc-interactive/`**; notebooks resolve that path automatically.
2. **Task notebook** – [Create new task](https://www.kaggle.com/benchmarks/tasks/new), attach the dataset, then paste cells from `benchmarks/kaggle/arc_kaggle_notebook_template.py` (one `@kbench.task` per published task), or run `python3 benchmarks/kaggle/rebuild_kaggle_notebooks.py` to generate `benchmarks/kaggle/notebooks/*.ipynb`. See `benchmarks/kaggle/notebooks/README.md` for **3.11 vs 3.12** / bootstrap deps.
3. **Benchmark** – Add each published task to your benchmark; see [Kaggle Benchmarks docs](https://www.kaggle.com/docs/benchmarks).

**Geo / model API:** If a run fails with **`User location not supported for this model/API`** after games load, the issue is the **hosted LLM** (provider region rules), not your notebook or dataset. Try another benchmark model or contact Kaggle; see `benchmarks/kaggle/notebooks/README.md`.

## Adding more games

From a new `@kbench.task` in `arc_tasks.py`, call `run_game_with_llm(..., game_id=…, grid_size=<camera width>, max_steps=…)` where `game_id` is the string in that package’s `metadata.json` (see `full_game_id_for_stem` in `scripts/env_resolve.py`, as used at the top of `arc_tasks.py`). Add a row to the table above. For mocks, record a digit string with `ReplayMockLLM` (see `MOCK_*` constants in `arc_tasks.py`).
