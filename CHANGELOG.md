# Changelog

Harness (`SKILL.md` / `templates/` / `scripts/`) changes, eval-gated. See [`HARNESS.md`](HARNESS.md).
Each entry: what changed, why, and the eval result at the time (`python evals/run.py det` + `grade`).

## Unreleased

### Added
- Harness engineering operation: [`HARNESS.md`](HARNESS.md) playbook + `evals/` suite (deterministic c4 tests + behavioral golden cases for action selection A–E and triggering).
- First baseline ([`evals/baseline.json`](evals/baseline.json)), answer model `claude-sonnet-4-6`: **deterministic 8/8**, **behavioral 10/12**.

### Open findings (from the first baseline — need owner decision before any SKILL.md change)
- `as-open-issues-progress` (high): the workhorse "open Issues + improving metric" state does not robustly resolve to **D** (routine patrol); models reach **C** (advisor escalation). The C-vs-D boundary is under-specified.
- `trig-pm-patrol` (medium): the trigger phrase "PM 巡回" does not reliably fire from the description alone.

_No `SKILL.md` behavior has been changed yet — only the eval/operation scaffolding was added._
