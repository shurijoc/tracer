# tracer

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Claude Code skill](https://img.shields.io/badge/Claude_Code-skill-7c5cff.svg)](https://claude.com/claude-code)

**English** | [日本語](README.ja.md)

> A [Claude Code](https://claude.com/claude-code) skill that runs an **autonomous improvement loop** as a PM, driving toward a quantitative goal (a North Star Metric).

You only ever type `/tracer`. The skill reads the current state and automatically runs one of five actions — init, roadmap, advisor escalation, routine patrol, or completion report. At the end of every cycle it regenerates a per-improvement HTML dashboard, and you intervene based on what you see there.

## Table of Contents

- [What is this?](#what-is-this)
- [Design principles](#design-principles)
- [Requirements](#requirements)
- [Installation](#installation)
- [Quick start](#quick-start)
- [Features](#features)
- [How it works (design docs)](#how-it-works-design-docs)
- [Repository layout](#repository-layout)
- [License](#license)

## What is this?

Pick one improvement target that can be measured as a number, and tracer keeps working toward it as a PM until the goal is met.

- **Targets** — anything with a deterministic numeric measure: test error counts, API latency, product KPIs (an *improvement*).
- **What it does** — decomposes the goal (roadmap) → files GitHub Issues → dispatches implementation in isolated worktrees → verifies pass/fail → measures the metric → updates the dashboard, all from a single `/tracer`.
- **Your role** — watch the dashboard and step in with feedback when things stall. Changing the acceptance criteria (`eval` / `metric`) always requires your approval.

State lives in the target repo's `.claude/goals/`. The skill itself works in any repo.

## Design principles

- **Separation of loop + eval + durable state + gate** — the re-entry vehicle (loop), the pass/fail gate (external eval), the durable state in git/Issues, and the reward-function guard gate are each held independently.
- **Two-layer reward** — micro = per-Issue pass/fail `eval` (deterministic, exit 0); macro = the goal `metric`. Phase/goal completion is judged by **metric improvement**, not by the number of Issues closed.
- **Reward-hacking prevention** — changes to `eval` / `metric` definitions require user approval. Diffs touching `protected_paths` auto-escalate via a tamper check, and a worker's self-reported result is independently re-verified by a separate subagent.
- **Autonomy L0→L1→L2** — the PM's authority widens in stages based on a track record of agreement (5 consecutive matches). The acceptance criteria stay yours forever.
- **Intervene via the HTML dashboard** — the dashboard is regenerated every cycle. The operating model is "look at the dashboard, and give feedback / unblock when it gets stuck."

## Requirements

- [Claude Code](https://claude.com/claude-code) installed
- `gh auth login` completed (the roadmap mode files GitHub Issues)
- Node.js for C4 diagram generation (mermaid-cli is fetched via `npx`). Without it, patrols still exit 0 and continue.

## Installation

Install via symlink so that `git pull` keeps the skill up to date.

```bash
git clone https://github.com/shurijoc/tracer.git
ln -s "$(pwd)/tracer" ~/.claude/skills/tracer   # the link name must be "tracer" (match the frontmatter name)
```

## Quick start

Run `/tracer` from the root of the repo you want to improve.

1. **First run (init mode)** — interactively collects the improvement's persona / metric (measurement command) / eval (pass-fail command).
2. **Subsequent runs** — the skill reads the state and automatically advances through roadmap → routine patrol → completion report.

```bash
cd path/to/your-repo
# In Claude Code:
/tracer
```

You can run multiple improvements in parallel (state is separated per improvement).

## Features

- A single `/tracer` command auto-detects and runs one of five states (init / roadmap / advisor escalation / routine patrol / completion report)
- **Parallel** improvements (state is separated per improvement)
- A repo-wide C4 architecture model (`c4.json`) rendered to SVG via Mermaid → mmdc and inlined into the dashboard
- Advisor escalation (opus + effort max) when the metric stalls for 5 cycles
- Issue implementation dispatched in isolated worktrees, with independent verification (tamper check + separate verifier)

## How it works (design docs)

The design rationale is laid out in a **self-contained HTML** page (no dependencies, zero JS).

- 🌐 GitHub Pages: <https://shurijoc.github.io/tracer/>
- 📄 In the repo: [`index.html`](index.html) (open locally)

> The HTML design doc and the operational spec (`SKILL.md`) are currently written in Japanese.

## Repository layout

```
SKILL.md                   # the skill itself (the spec Claude reads at runtime)
index.html                 # design docs (self-contained HTML, zero dependencies)
scripts/c4-to-section.py   # generates the C4 section HTML fragment from c4.json
templates/                 # templates for goal / dashboard / c4 / activity / decisions
```

## License

[MIT](LICENSE)
