# Harness engineering playbook

How to evolve tracer's harness (`SKILL.md`, `templates/`, `scripts/`) safely and on a repeatable cadence. tracer is itself an agent harness — *loop + external eval + durable state + gate* — so changing it deserves the same discipline tracer imposes on the repos it improves: **don't advance on a self-report; advance on a graded result.**

This file is the maintainer's operating manual. It is not loaded by the skill at runtime (kept out of `SKILL.md` to protect runtime context).

## The core rule: evals are the source of truth

Treat `evals/` like code. A change to `SKILL.md` is "done" when the eval suite is green or every red is a *documented, accepted* finding — never when it merely "looks right." ([Anthropic — skill best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices): *build evaluations BEFORE writing extensive documentation; evals are your source of truth.*)

## The two eval layers

Run from the repo root.

```bash
python evals/run.py det                 # deterministic: code tests for scripts/c4-to-section.py
python evals/run.py list                # list golden cases
python evals/run.py prompts             # emit per-case prompts for a FRESH agent
python evals/run.py grade answers.json  # grade {id: label} (or evals/baseline.json) vs expected
```

1. **Deterministic layer** — pure code tests over the only executable artifact (`c4-to-section.py`). No model, no network, fully reproducible. This is the CI-able regression backstop; its central invariant (every bad input → exit 0 + fallback fragment) must never regress.
2. **Behavioral layer** — golden cases in `evals/cases/*.json` whose answer is a **discrete label** (an action letter `A`–`E`, or `YES`/`NO`). A fresh model produces the labels by reading the *actual* `SKILL.md`; `run.py grade` checks them by exact match against the human-owned `expected`.

Why discrete labels: because the output is a label, grading is **code-based** — no LLM-as-judge, so we sidestep the *oracle problem* (an LLM judge tends to bless the current behavior rather than the intended behavior). ([Anthropic — demystifying evals](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents); [pragmatic guide to evals](https://newsletter.pragmaticengineer.com/p/evals): *never let the agent write its own ground truth.*)

### Running the behavioral layer end-to-end

The runner can't call a model itself. The loop is:

1. `python evals/run.py prompts` → a bundle of self-contained prompts, one per case.
2. Hand each prompt to a **fresh agent** (a clean Claude with no eval context, ideally the model tracer runs on). In Claude Code: spawn one `Agent` per case so they're independent. **Never show the answering agent the `expected` value.**
3. Collect answers as `{ "<case-id>": "<label>" }` and `python evals/run.py grade answers.json`.
4. Save the run to `evals/baseline.json` (it stores model-produced answers + open findings, not ground truth).

**Reference model**: `evals/baseline.json` is graded against **claude-opus-4-8** (the model tracer's main loop runs on). sonnet answers are kept in `sonnet_reference` as a weak-model robustness reference only — they are not the eval gate.

## The change procedure (every SKILL.md edit)

1. **Reproduce the gap first.** Find a real failure (a wrong action choice, a mis-fire) and write it as a golden case *before* editing `SKILL.md`. Establish the baseline (the current red). ([skill best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices): identify gaps → create evals → baseline → minimal edit → iterate.)
2. **Make the minimal edit** to `SKILL.md` / `templates/`.
3. **Re-run both layers.** `det` must stay green. The new case must flip to green, and **no previously-green case may go red** (regression gate — `run.py grade` exits non-zero on any red or missing answer).
4. **Re-baseline.** Update `evals/baseline.json` and bump `CHANGELOG.md`.
5. **Resample divergences.** A label that flips between runs is variance, not signal — resample 3× before trusting it (see the `as-target-hit` noise note in the baseline). ([demystifying evals](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents): repetition stability.)
6. **Read the transcripts.** Don't trust the scorecard blindly — skim *why* the agent chose what it did. This catches eval bugs and ambiguous fixtures.

### Two changes that are never silent

- **Reward-definition changes** (the `eval:` / `metric:` semantics, `protected_paths`) require explicit owner approval — same rule tracer enforces on workers. Don't loosen the suite to make a red go green.
- **Ground truth** (`expected` in `cases/*.json`) is human-owned. If a case is wrong, fix it deliberately and say so in the changelog — don't retrofit `expected` to whatever the model happened to output.

## Authoring golden cases

- **Source from real failures**, not imagined ones. 20–50 good cases beat a large synthetic set. ([demystifying evals](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents).)
- **Unambiguous**: two readers must independently reach the same `expected`. If a case is flaky because the *prompt* is vague (not the model), tighten the prompt — that's eval hygiene, not gaming. (See `as-open-issues-progress`, clarified after the first run still diverged.)
- **Positive and negative cases.** Triggering needs both "should fire" and "must not fire," or you optimize one-sidedly.
- The prompt must point the agent at the **real artifact** (`skills/tracer/SKILL.md`), so the eval measures the spec, not a paraphrase of it.

## Releasing & updates

tracer ships as a Claude Code **plugin**, so updates ride the plugin system — no bespoke updater. The canonical version is `version` in [`.claude-plugin/plugin.json`](.claude-plugin/plugin.json) ([semver](https://semver.org)). Bumping it is what makes installs update — via `/plugin update tracer@tracer`, or automatically if the user enabled `autoUpdate` for the marketplace.

To release:

1. Both eval layers green (`run.py det` + `grade`), or every red is a documented, accepted finding.
2. Bump `version` in `.claude-plugin/plugin.json` (patch = fixes, minor = new behavior, major = breaking spec changes). Keep `metadata.version` in `.claude-plugin/marketplace.json` in sync.
3. Move `## Unreleased` in [`CHANGELOG.md`](CHANGELOG.md) to `## [x.y.z] - <date>` and start a fresh empty `## Unreleased`.
4. Validate, commit, tag, publish:
   ```bash
   claude plugin validate . --strict          # schema + manifest agreement
   git push origin main
   claude plugin tag .                         # creates the tracer--vX.Y.Z tag (checks plugin.json/marketplace agree)
   git push origin --tags
   gh release create tracer-vX.Y.Z --title "tracer vX.Y.Z" --notes "<changelog section>"
   ```
5. Users pick up the new version with `/plugin update tracer@tracer` (or automatically with marketplace auto-update).

Never tag a release whose eval suite is red without a recorded reason — the version is a claim that the harness behaves as documented.

## Harness design principles tracer already follows

When editing, preserve these — they're why the harness survives `/clear` and resists reward hacking:

- **Durable state in files + git, re-read from scratch each cycle** (fresh-context restore). State files structured and guarded against corruption. ([Anthropic — effective harnesses](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents); [context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents).)
- **A separate verifier from the doer** — a fresh agent refutes/re-checks rather than the worker grading itself. ([effective harnesses](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents).)
- **Outcome over trajectory** — judge what was produced (metric moved, eval passed), not the path taken.
- **Concise SKILL.md, appropriate degrees of freedom, one-level-deep references, consistent terminology, no time-sensitive info.** Keep the body well under 500 lines. ([skill best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices).)

## Anti-patterns

| Anti-pattern | Instead |
|---|---|
| "Looks right, ship it" | Gate on `run.py` green / accepted findings |
| LLM judges its own output as ground truth | Discrete labels + code grading + human `expected` |
| Loosen the suite to clear a red | Fix the harness, or document the finding as accepted |
| Trust a single sample | Resample 3× on any divergence |
| Pile up synthetic cases | Source cases from real failures |
| Big-bang SKILL.md rewrite | One minimal, eval-gated edit at a time |

## Sources

- [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
- [Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [A pragmatic guide to LLM evals](https://newsletter.pragmaticengineer.com/p/evals)
