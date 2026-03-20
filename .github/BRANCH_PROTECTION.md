# Branch protection (maintainers)

GitHub does not store required status checks in this repo file — apply these in the web UI (or org rulesets) so contributors get clear merge gates.

## Suggested required checks for `main`

Enable **Require status checks to pass before merging** and require at least:

| Check (as shown in the PR “Checks” tab) | Workflow |
|----------------------------------------|----------|
| **Registry check** / `registry` | [`pr-registry.yml`](workflows/pr-registry.yml) |
| **PR game smoke** / `smoke` | [`pr-game-smoke.yml`](workflows/pr-game-smoke.yml) |
| **PR Ruff** / `ruff` | [`pr-ruff.yml`](workflows/pr-ruff.yml) |

Optional (often left non-blocking):

- **README statistics** — only runs when `GAMES.md` changes on `main`.
- **Pull Request Labeler** — should not block merges.
- **Welcome first-time contributor** — should not block merges.

## Notes

- Path-filtered workflows may be **skipped** on a PR if no matching files changed. GitHub treats skipped required checks as satisfied in some configurations; if a check stays “pending” when skipped, either widen workflow `paths` or adjust branch rules. When in doubt, use a ruleset that only requires checks that actually ran.
- After adding a new required workflow, merge one PR that touches the relevant paths so the check appears in the branch protection picker.
