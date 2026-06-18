# tracer

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Claude Code skill](https://img.shields.io/badge/Claude_Code-skill-7c5cff.svg)](https://claude.com/claude-code)

**English** | [日本語](README.ja.md)

> A [Claude Code](https://claude.com/claude-code) skill that runs an **autonomous improvement loop** as a PM, driving toward a quantitative goal (a North Star Metric). You only ever type `/tracer`.

## 📖 The docs are an HTML page, not this README

Markdown is tiring to read. The design — the 5-state machine, the two-layer reward, reward-hacking prevention, autonomy levels — is laid out in a **self-contained HTML page** (zero dependencies, zero JS) that's far easier to skim. **That page is the real documentation. This README is just a launcher.**

### 👉 [Read the design doc](https://shurijoc.github.io/tracer/) &nbsp;·&nbsp; [日本語版](https://shurijoc.github.io/tracer/index.ja.html)

(or open [`index.html`](index.html) / [`index.ja.html`](index.ja.html) locally)

## Install

```bash
git clone https://github.com/shurijoc/tracer.git
ln -s "$(pwd)/tracer" ~/.claude/skills/tracer   # link name must be "tracer" (match the frontmatter)
```

Requires [Claude Code](https://claude.com/claude-code) and `gh auth login`. Node.js is optional (only for C4 diagrams).

## Quick start

Run `/tracer` from the root of the repo you want to improve. The first run interactively sets up an improvement target (persona / metric / eval); every run after that reads the state and advances the loop on its own. Then **just watch the regenerated dashboard and step in when it stalls** — see the [design doc](https://shurijoc.github.io/tracer/) for the rest.

## License

[MIT](LICENSE)
