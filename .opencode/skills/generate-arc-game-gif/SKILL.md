# Skill: Generate ARC game preview GIFs (`assets/{stem}.gif`)

Use this skill when adding or refreshing **64×64** registry GIFs in `assets/`, or when checking whether a game’s HUD is suitable for markdown previews.

## What a registry GIF must show

Preview GIFs are not random motion clips. They should tell a human (and an agent reading the table) **how the game progresses** and **how you lose or fail a check**.

1. **Advancing levels** — The capture should include **multiple levels** where the game has them (e.g. early level(s) cleared, then **at least one harder / later** level so difficulty ramps). Level changes must read clearly on the **final 64×64 frame**: HUD updates (`RenderableUserDisplay.update`), optional brief hold/pause in capture timing via **`registry_gif_overrides.json`** / `registry_gif_lib`—not by faking pixels outside the game.
2. **One or two failed cases** — Include **1–2** segments that show **failure**: `GAME_OVER`, a wasted resource (e.g. checks/blurs/steps hitting zero), a **failed** test with visible HUD feedback, wrong flag, etc. Failures must be **visible in the shipped game UI** (colors, bars, icons drawn in `render_interface`), not only as a caption or external annotation.
3. **Everything reads through `RenderableUserDisplay`** — Cursors, pings, “bad” states, counters, and lose-adjacent feedback live in the game’s **`RenderableUserDisplay`** (and whatever `step()` passes into `update`). The recorder (`render_arc_game_gif.py` → `registry_gif_lib`) only **steps** the env and saves frames; it does not replace a missing HUD.

If the stock recorder cannot yet hit “late level + two fails” for a stem, **first** ensure the UI exposes those states clearly, then extend **`registry_gif_overrides.json`** / shared **`registry_*_gif.py`** / **`registry_gif_lib`** so the **same script** still drives the GIF.

## Single script (repo)

All capture flows go through **`scripts/render_arc_game_gif.py`**:

| Mode | Command |
|------|---------|
| **Registry** (multi-level + fails when configured) | `uv run python scripts/render_arc_game_gif.py --stem wl01` |
| Batch in `GAMES.md` order | `uv run python scripts/render_arc_game_gif.py --from pb01 --through bn03` |
| **Pending** (quick motion only; not a full registry spec) | `uv run python scripts/render_arc_game_gif.py --pending --pending-all` |
| Pending + one stem | `uv run python scripts/render_arc_game_gif.py --pending --pending-game ju01` |
| Fill `GAMES.md` preview column after pending | add `--fill-games-md` |

**Note:** Pending mode is for **placeholder motion**. For **`GAMES.md` registry quality**, prefer **registry** mode after the UI meets the section above.

Implementation detail: registry mode calls `registry_gif_lib.record_registry_gif` and reads **`scripts/registry_gif_overrides.json`**. Some families use **`registry_*_gif.py`** helpers imported by `registry_gif_lib`. Do **not** add new **`scripts/render_<stem>_gif.py`** entrypoints.

## Is this game’s `RenderableUserDisplay` GIF-ready?

Audit the game’s **`RenderableUserDisplay`** (and `step()` driving `update`). The final frame is always **64×64**.

### Checklist

1. **Level progression** — HUD reflects level index, remaining objectives, or budget so **level advance** is obvious without sound or prose.
2. **Failure legibility** — At least one distinct **palette / bar / icon** state for “wrong” or “out of budget” or **game over** (whatever your rules use), drawn in `render_interface` for several frames where possible.
3. **HUD / state** — Counters and modes update via `update(...)`; avoid a static strip for the whole GIF.
4. **ACTION6 / clicks** — If used, show **where** the player clicked for multiple frames in **final frame pixel space** (letterboxed). Reference: **`environment_files/mm01/63be02fb/mm01.py`** (`Mm01UI.set_click`, top bar).
5. **Letterboxing** — Match `Camera` math for grid ↔ frame (`display_to_grid` / `_grid_to_frame_pixel` patterns in **`AGENTS.md`**).
6. **No recorder-only FX** — Do not rely on scripts to draw ripples or failure tints; implement them in **`RenderableUserDisplay`** so any capture path sees them.

## Author workflow

1. Implement **`RenderableUserDisplay`** so **wins, level-ups, and 1–2 fail types** read clearly on frame.
2. Tune capture in **`registry_gif_overrides.json`** (and shared lib/helpers if needed) so **`render_arc_game_gif.py --stem <stem>`** produces: **advance levels + 1–2 fails**.
3. Add **`![stem](assets/stem.gif)`** in **`GAMES.md`** when the asset exists.

## Tech notes

- `arc.make(..., include_frame_data=True)` inside `registry_gif_lib`; pending mode uses a lighter loop.
- Palette → RGB: **`scripts/gif_common.py`**.
- Full `game_id`: **`scripts/env_resolve.full_game_id_for_stem("wl01")`**.

## Related docs

- **`AGENTS.md`** — camera/UI patterns, palette.
- **`skills/create-arc-game/SKILL.md`** — game structure.
- **`skills/play-arc-game/SKILL.md`** — running and stepping envs.
