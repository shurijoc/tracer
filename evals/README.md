# evals/

The eval suite for tracer's harness. Full process: [`../HARNESS.md`](../HARNESS.md).

```bash
python evals/run.py det                 # deterministic c4-to-section.py tests (no model/network)
python evals/run.py list                # list golden cases
python evals/run.py prompts             # emit per-case prompts for a fresh agent
python evals/run.py grade answers.json  # grade {id: label} or evals/baseline.json vs expected
```

## Layout

```
run.py                       # runner (deterministic tests + behavioral grading)
baseline.json                # last behavioral run: model-produced answers + open findings
cases/action-selection.json  # golden cases for Step 1 action judgment (A-E)
cases/triggering.json        # golden cases for skill triggering (YES/NO)
```

## How it works

- **Deterministic layer**: code tests over `scripts/c4-to-section.py`. The invariant under test — bad input (missing/broken/empty) → exit 0 + fallback fragment — must never regress.
- **Behavioral layer**: each case answer is a discrete label. A fresh model reads the real `SKILL.md` and produces the label; `run.py grade` checks it by exact match against the human-owned `expected`. Discrete labels → code-based grading → no LLM-judge → no oracle problem.

Ground truth is `expected` in `cases/*.json` and is **human-owned**. `baseline.json` holds model answers, not ground truth — never copy answers into `expected` to force green.

## Adding a case

Append to the relevant `cases/*.json`:

```json
{
  "id": "as-...",
  "kind": "action-selection",
  "tags": ["positive", "patrol"],
  "expected": "D",
  "rationale": "why this is the correct label (for humans)",
  "prompt": "instructions that point the agent at skills/tracer/SKILL.md and ask for ONE label"
}
```

Keep prompts unambiguous (two readers reach the same `expected`) and source them from real failures.
