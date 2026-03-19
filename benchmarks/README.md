# ARC-AGI-3 Benchmarks

Benchmarks for evaluating AI models on ARC-AGI-3 games, including Kaggle benchmark tasks.

## Structure

- **`arc_game_wrapper.py`** – Reusable wrapper to run ARC games with an LLM agent. Serializes game state to text, parses action responses, and runs the game loop.
- **`kaggle/`** – Kaggle benchmark tasks using the [kaggle-benchmarks](https://pypi.org/project/kaggle-benchmarks/) library.

## Sample Task: arc_ez01_go_up

Evaluates an LLM playing **ez01 (Go Up)** – the simplest ARC game (4 movement actions). The LLM receives the grid each step and must output the next action. Success = complete at least 1 level within 30 steps.

### Running Locally

Local runs require the Kaggle Model Proxy. Configure a `.env` file in the repo root:

```env
MODEL_PROXY_URL=https://mp-staging.kaggle.net/models/openapi
MODEL_PROXY_API_KEY=your_token
LLM_DEFAULT=google/gemini-2.5-flash
```

Then run from the repo root:

```bash
uv run python -m benchmarks.kaggle.arc_ez01_task
```

To verify the wrapper without the Kaggle proxy (mock LLM, always moves up):

```bash
uv run python -m benchmarks.run_task_test
```

### Publishing to Kaggle

1. Go to [Kaggle Benchmarks](https://www.kaggle.com/benchmarks) and click **Create benchmark** or **Create task**.
2. Create a new task notebook at [tasks/new](https://www.kaggle.com/benchmarks/tasks/new).
3. Copy the task code from `benchmarks/kaggle/arc_ez01_task.py` and the wrapper from `benchmarks/arc_game_wrapper.py` into the notebook (or attach the repo as a dataset).
4. Ensure `environment_files` (or the required game files) are available in the notebook environment.

See [Kaggle Benchmarks documentation](https://www.kaggle.com/docs/benchmarks) for full details.

## Adding More Tasks

Use `arc_game_wrapper.run_game_with_llm()` with different `game_id` values (e.g. `sk01-v1`, `tb01-v1`) and adjust `grid_size` and `max_steps` per game. Add new `@kbench.task` functions in `benchmarks/kaggle/`.
