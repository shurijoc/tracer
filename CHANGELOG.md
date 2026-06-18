# Changelog

Harness (`SKILL.md` / `templates/` / `scripts/`) changes, eval-gated. See [`HARNESS.md`](HARNESS.md).
Each entry: what changed, why, and the eval result at the time (`python evals/run.py det` + `grade`).

## Unreleased

### Added
- Harness engineering operation: [`HARNESS.md`](HARNESS.md) playbook + `evals/` suite (deterministic c4 tests + behavioral golden cases for action selection A–E and triggering).
- First baseline ([`evals/baseline.json`](evals/baseline.json)), answer model `claude-sonnet-4-6`: **deterministic 8/8**, **behavioral 10/12**.

### Changed
- `SKILL.md` Step 1: clarified the C/D action boundary. **C** now requires the metric Log to have **>=5 recorded cycles AND no improvement** across the last 5; **D** explicitly states the "not stalled" precondition. Eval-gated: on **opus** (the model tracer runs on) `as-open-issues-progress` now resolves to **D** (2/2) and `as-new-improvement-added` to **A**. On **sonnet** the open-issues case still mis-picks **C** — a model-capability gap, not a spec gap (see issue).

### Open findings
- `trig-pm-patrol` (medium): the trigger phrase "PM 巡回" does not reliably fire from the description alone (sonnet, 3/3 NO; not re-checked on opus). Tracked in an issue.

### Follow-ups (tracked in issues)
- Re-baseline the suite on **opus** (current baseline used sonnet, which is not the model tracer runs on).
