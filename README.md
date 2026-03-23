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
  <tr>
    <td align="center"><img src="assets/sl01.gif" alt="sl01 Permutation / Puzzle — slide puzzle: swap the hole with adjacent tiles until the board matches the goal; step limit." width="64" height="64" /></td>
    <td align="center"><img src="assets/sv03.gif" alt="sv03 Dual shelters" width="64" height="64" /></td>
    <td align="center"><img src="assets/lo02.gif" alt="lo02" width="64" height="64" /></td>
    <td align="center"><img src="assets/ph01.gif" alt="ph01" width="64" height="64" /></td>
    <td align="center"><img src="assets/or01.gif" alt="or01" width="64" height="64" /></td>
    <td align="center"><img src="assets/tt03.gif" alt="tt03 Collector spawns" width="64" height="64" /></td>
    <td align="center"><img src="assets/zq03.gif" alt="zq03" width="64" height="64" /></td>
    <td align="center"><img src="assets/ml01.gif" alt="ml01" width="64" height="64" /></td>
  </tr>
  <tr>
    <td align="center"><code>sl01</code></td>
    <td align="center"><code>sv03</code></td>
    <td align="center"><code>lo02</code></td>
    <td align="center"><code>ph01</code></td>
    <td align="center"><code>or01</code></td>
    <td align="center"><code>tt03</code></td>
    <td align="center"><code>zq03</code></td>
    <td align="center"><code>ml01</code></td>
  </tr>
</table>

<!-- Auto-updated on push to `main` when `GAMES.md` changes (see `.github/workflows/readme-stats.yml`, `devtools/scripts/update_readme_stats.py`). -->
<!-- readme-stats:begin -->

<p align="center">
  <a href="GAMES.md"><img src="https://img.shields.io/badge/249-INTERACTIVE_GAME-58A6FF?style=for-the-badge" alt="249 interactive games in registry" /></a>
  &nbsp;
  <a href="CONTRIBUTING.md#creating-a-new-game"><img src="https://img.shields.io/badge/Contributing-Add_an_interactive_game-238636?style=for-the-badge" alt="Contributing: add an interactive game" /></a>
</p>

<!-- readme-stats:end -->

## What for?

> The intelligence of a system is a measure of its skill-acquisition efficiency over a scope of tasks, with respect to priors, experience, and generalization difficulty.  
> — François Chollet, *[On the Measure of Intelligence](https://arxiv.org/abs/1911.01547)* (2019)

These games are designed to be easy for humans to solve, but very hard for modern AI systems—including frontier large language models. Together they stress reasoning, planning, and interactive control rather than memorized puzzle templates.

## Why use ARC-Interactive?

- **Massive testing ground** — 200+ community games in [`GAMES.md`](GAMES.md) beside the [official ARC-AGI-3 list](https://docs.arcprize.org/available-games); train, test, and evaluate agents on varied unseen tasks for generalization.
- **Fast prototyping** — Local offline `environment_files/`, agent step-through, and **`--mode human`** to learn win conditions by playing.
- **LLM-friendly authoring** — [`AGENTS.md`](AGENTS.md) plus skills under [`.opencode/skills/`](.opencode/skills/) (mirrored at [`skills/`](skills/)): [create-arc-game](.opencode/skills/create-arc-game/SKILL.md), [play-arc-game](.opencode/skills/play-arc-game/SKILL.md).
- **Competition mode** — `uv run python run_game.py --competition` matches the real toolkit ([competition rules](https://docs.arcprize.org/toolkit/competition_mode)) before you submit.
- **Official leaderboard** — With **`ARC_API_KEY`** and **`--online`**, runs can count on **[three.arcprize.org](https://three.arcprize.org/)** (see [API / leaderboard / competition](#api--leaderboard--competition) below).

## Quickstart

Requires [Python 3.12+](https://www.python.org/) and [uv](https://github.com/astral-sh/uv). From the repo root, install dependencies once:

```bash
uv sync
```

Run a game (tutorial **ez01**):

```bash
# Omitting --mode defaults to random-agent (random ACTION1–ACTION5 for --steps); set explicitly below.
# Local play uses environment_files/ by default unless --online / --competition.
uv run python run_game.py \
  --offline \
  --version auto \
  --mode random-agent \
  --game ez01
```

Discover local environments:

```bash
# List local environments; add --offline to pin the listing to local environment_files/.
# For a chosen stem, --version auto picks the sole package under it.
uv run python run_game.py --list
# uv run python run_game.py --offline --list
```

### Human play

With **`--mode human`**, local keys map to abstract actions as in **[Actions](https://docs.arcprize.org/actions)** (WASD + Space, arrows + F; digits `1`–`5` also send ACTION1–5):

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

### Create a game with AI Agent

Example prompt (replace `{game_id}` and the bracketed design):

```
Implement a new ARC-AGI-3 game {game_id} at environment_files/{game_id}/v1/. Follow AGENTS.md and .opencode/skills/create-arc-game/SKILL.md: static levels only, ARCBaseGame + metadata.json, register a row in GAMES.md. Game design: [grid size, entities, win/lose, which actions 1–7 do].
```

**Available skills** (under [`.opencode/skills/`](.opencode/skills/), mirrored at [`skills/`](skills/)):

- **[create-arc-game](.opencode/skills/create-arc-game/SKILL.md)** — End-to-end game design and implementation (`environment_files/`, `ARCBaseGame`, `metadata.json`, `GAMES.md`) aligned with [`AGENTS.md`](AGENTS.md).
- **[play-arc-game](.opencode/skills/play-arc-game/SKILL.md)** — Run and smoke-test local environments with `run_game.py` (list, random agent, human pygame, offline/online flags).
- **[generate-arc-game-gif](.opencode/skills/generate-arc-game-gif/SKILL.md)** — GIF-ready `RenderableUserDisplay` and registry previews via `scripts/render_arc_game_gif.py`.

Full checklist: [CONTRIBUTING.md](CONTRIBUTING.md#creating-a-new-game).
