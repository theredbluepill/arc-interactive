---
name: check-arc-game-discoverable
description: >-
  Judges whether an ARC game is discoverable by play (goals/rules learned in
  the env); co-requires fair shared observation/actions for humans and AIs.
  Use when reviewing stems for discovery-through-play or remediation.
---

# Check ARC game discoverability by play (no prior)

## Soul of this skill

Assume a **participant** (human or AI) who has **never seen this task**, has **not** been trained on it, and receives **no tutorial text, no labeled rule sheet, and no external description** of goals or what each action “means.”

**That is by design.** In benchmark-style play, **goals, rules, and action semantics are meant to be hidden** from the game taker at the start. Participants are expected to **figure them out themselves during play**—by trying actions, watching what changes, hitting win/lose, and iterating.

**Solvable** here means exactly that: **solvable by discovery through play**—not “everything was explained or drawn on the HUD up front.” A stem **passes** if a reasonable participant **can** converge on enough of the goal and mechanics to win **from experience alone** (same observation and action channel an agent gets). It **fails** if, **even while playing**, the information or feedback needed to win **never** becomes available, or the space is so flat that learning cannot get off the ground.

If a human **can** do that, it is the **foundation** for claiming an AI **without task-specific prior** could in principle do the same under the **same** interface: the task must be **learnable from interaction**, not from documentation.

### Human first, AI co-required

Under ARC-style benchmarking, **human-solvable (in this skill’s sense) and AI-solvable under the official interface are meant to co-exist**:

1. **Human first** — Primary gate: can a cold-start participant **learn** goal, critical state, and action effects **through play** (observation + legal actions + consequences)? Review that **discovery path**, not whether the author pasted rules on screen.

2. **AI co-required** — **Benchmark intent: human-solvable ⇒ AI-solvable (in principle)** under the **same** official observation and action interface. Passing the human bar **implies** the task is **fair for an agent** that sees that channel: no extra win-critical information for humans only, levels **mechanically winnable** under the game’s actual logic, and no reliance on prose outside the env. It does **not** guarantee a particular model will win—only that the **spec** is not rigged against an honest AI relative to the human.

3. **Order of work** — Judge **whether discovery-through-play is tractable** first; then confirm **mechanical** AI-facing soundness (winnable levels, obs/action parity). If the participant could never learn enough from play, fix **in-world feedback and dynamics** first—not `GAMES.md` copy.

This skill is **not** about whether `GAMES.md`, `metadata.json`, or operator docs are clear. Those do **not** count toward this criterion. A game that is only understandable after reading prose **fails** this skill, even if the prose is excellent.

## In scope vs out of scope

| In scope (must support discovery-through-play) | Out of scope for this skill |
|------------------------------------------------|-----------------------------|
| What changes when the participant acts; win/lose / level advance feedback | `GAMES.md` one-liners |
| Whether goals and rules become **inferable** over time from layout + consequences | `metadata.json` `description` |
| Distinct sprites, motion, HUD bits that **reward hypothesis testing** | Notebook / API explanatory text |
| Level shape that makes the **first discoveries** easier (still without spelling rules) | Action ID naming in docs |

## Core requirement

Both must hold; **human-facing criteria are listed first**:

1. **Discoverable by play (human first)** — Over the course of playing (trying actions, seeing outcomes), a participant can **infer** what they are trying to achieve and how actions affect state **without** external copy. Upfront labels are **not** required; **persistent blindness** (win depends on facts that never appear in observation **during** play) **is** a failure.

2. **Solvable under the shared interface (human + AI)** — There exists a winning trajectory under real constraints (budgets, static levels, exposed actions) that an agent using the **same** observation and action API could in principle execute **once** the rules have been learned through play—no win logic that depends on fields that **never** influence what the participant can see.

**Implications:**

- **Goal** — May start **unknown**; must become **workably knowable** from board, motion, win/lose, or consistent feedback—not from a sentence in a file the participant never sees.
- **Parameters** — May be learned gradually; they must **enter** the observation stream **through play** (e.g. meters, pattern changes, rejection signals)—not live only in `level.data` with **no** rendered or behavioral footprint.
- **Actions** — Participants learn by **doing**; each action that matters should produce **discernible** outcomes when relevant. Truly indistinguishable no-ops with no way to learn they are inert widen the search space unfairly.
- **Sparse win-only reward** — If the only strong positive is clearing a level, early play must still give **enough differentiated feedback** that exploration is not astronomically blind.

## Review checklist (playtest mentally as a tabula rasa)

Ask these **as if** the participant may **not** know the goal or rules until they probe. “Figured out” means **after some play**, not **before the first keypress**.

1. **No readme** — Ignore `GAMES.md` and metadata. After **playing** level 1 for a short while, could a participant form a **plausible goal hypothesis** and test it?
2. **Goal parameters** — Every quantity that must be satisfied to win: can it **eventually** be inferred or tracked from what appears or changes **during** play (not required to be printed at start)?
3. **Critical state** — State that matters for win: does it **affect** what the participant sees or what happens when they act, so it can be **discovered**, not only live in code?
4. **Actions** — Do useful actions produce **different** observations or outcomes when tried in relevant contexts? Can inert actions be **learned** as inert (or be removed from the exposed set)?
5. **Budgets** — Time/step/blur limits: can participants **notice** pressure (HUD, behavior, loss) in time to adapt, or do they lose **before** feedback makes the limit learnable?
6. **Level 1** — Is the opening episode **small or structured enough** that trial-and-error can **teach** one mechanic before the search space explodes? (Still **no** requirement to label rules on screen.)

## Anti-patterns (fail this skill)

- Win depends on information that **never** shows up in observation **even as the participant plays**.
- “Solve by reading the repo” — docs replace **learning from the env**.
- **No** differentiated feedback: trying actions does not narrow what is going on.
- Hypothesis space is huge **and** play gives almost no clues (not merely “hard puzzle”—**unlearnable**).

## When discovery fails: propose fixes (in-world only)

If participants **cannot** reasonably figure the task out **through play**, **do not** fix it with longer `GAMES.md` or metadata. Propose **concrete** changes so **interaction** teaches more: clearer **consequences** when you act, salient **state change**, tighter **first level**, honest **reject/lose** signals, etc.

The list below is **remediation when play does not converge**—**not** a requirement that every game pre-label goals or action maps. Many good stems keep rules implicit; they still give **enough** feedback to learn.

### Board + sprites

- **Consequences visible** — When state changes, the frame should reflect it so hypotheses can be tested.
- **Salience** — Distinct sprites for entities that behave differently; consistent color/motion language where it helps **trial-and-error**.
- **Letterboxing-safe** — Overlays in `RenderableUserDisplay` align with `Camera` math (see `AGENTS.md` / **create-arc-game**).

### Action feedback

- **Discernible effects** when an action is legal and matters, or a **consistent** illegal/reject signal when it is not.
- **Coordinate actions** — mapped grid cell feedback (e.g. ripple) so clicks **teach** spatial semantics (`display_to_grid`).

### HUD (`RenderableUserDisplay`)

- Optional **progress** or **budget** pixels when loss conditions are otherwise opaque—only if playtesting shows participants **cannot** infer limits from outcomes alone.

### Level design

- **Smaller or more directed** first level so discovery is tractable **without** a rule card.

### How to write the proposal

For each gap: **symptom** (what play **fails** to teach) → **fix** → **where**. Prefer the smallest change that makes the task **learnable within a session**.

## Related (engineering, not this bar)

- **[`AGENTS.md`](../../AGENTS.md)** — Broader benchmark and implementation notes.
- **[create-arc-game](../create-arc-game/SKILL.md)** — How to build games.
- **`GAMES.md`** — Operator summaries; **not** input to this checklist.

## Verdict policy (keep “unknown” rare)

1. **Static checklist first** — Walk [Review checklist](#review-checklist-playtest-mentally-as-a-tabula-rasa). If **discovery-through-play** is **not** plausible from code + mental simulation (or playtest), default verdict **no**, with gaps and fixes. Do **not** use “unknown” to avoid calling a bad discovery path.

2. **Yes requires a high bar** — **yes** only if **all** hold: (a) checklist satisfied (**human first**), (b) levels **mechanically winnable** and obs/action **parity** (**AI co-required**), **and** (c) trivial confidence on a tiny teaching level **or** a **short playtest** (below) passed. If (a) or (b) fails → **no**.

3. **Unknown (pending playtest)** — Checklist **clean** on review but real cold-start playtest **not** run; note `unknown — schedule playtest`. If the checklist already failed → **no**.

### Short playtest protocol (before publishing **yes**)

- Participant has **not** read `GAMES.md`, `metadata.json`, or repo docs.
- **Level 0/1**, a few minutes of **free play**, then ask: can they **describe** what they think the goal is and what **at least one** meaningful action does, **without** having been told rules upfront?
- Record **pass / fail** in one line.

Automated solvers (e.g. `devtools/verify_level_solvability.py`) complement this: they check **mechanical** solvability; this skill checks whether a participant could **learn** the task **through the same channel**.

## Outcome of a review

- **Solvable by play (no prior) — human first, AI co-bar**: **yes** / **no** / **unknown (pending playtest only)**. **yes** = discovery-through-play is tractable **and** shared-interface mechanical solvability holds.
- **Gaps**: what **play** still fails to teach (required for **no**).
- **Fixes**: **symptom → in-world fix → file/hook** (not doc-only edits).
