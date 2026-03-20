## Summary

<!-- What does this PR change and why? Link related issues. -->

## Type of change

<!-- Check all that apply. -->

- [ ] New game or new `environment_files/{game_id}/{version}/` content
- [ ] Fix or tweak to an existing game
- [ ] Docs only (README, CONTRIBUTING, AGENTS.md, …)
- [ ] Tooling / CI / scripts
- [ ] Other: <!-- brief note -->

## Checklist

<!-- Use [CONTRIBUTING.md](CONTRIBUTING.md) for commands and structure. -->

- [ ] I ran **`uv run python run_game.py --game <id> --version <v>`** for every game touched (or N/A — explain below)
- [ ] **`GAMES.md`** updated for new/renamed games or materially changed metadata users care about (or N/A)
- [ ] **`metadata.json`** present and valid for new/changed game packages (or N/A)
- [ ] No unintended changes outside the scope above (or I’ve called out exceptions in “Notes”)

## Notes for reviewers

<!-- Optional: risk areas, follow-ups, screenshots/GIFs, agent-assisted workflow notes. -->

```text
# Example test command (replace game/version)
uv run python run_game.py --game ez01 --version v1
```
