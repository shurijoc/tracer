# tracer

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Claude Code skill](https://img.shields.io/badge/Claude_Code-skill-7c5cff.svg)](https://claude.com/claude-code)

**English** | [日本語](README.ja.md)

> **Drive your repo toward a measurable goal on autopilot.** A [Claude Code](https://claude.com/claude-code) skill that acts as PM — picks the next move, files Issues, and tracks progress against a North Star Metric. You only type `/tracer`.

## 📖 The docs are an HTML page, not this README

Markdown is tiring to read. The design — the 5-state machine, the two-layer reward, reward-hacking prevention, autonomy levels — is laid out in a **self-contained HTML page** (zero dependencies, zero JS) that's far easier to skim. **That page is the real documentation. This README is just a launcher.**

### 👉 [Read the design doc](https://shurijoc.github.io/tracer/) &nbsp;·&nbsp; [日本語版](https://shurijoc.github.io/tracer/index.ja.html)

## Install

In Claude Code:

```
/plugin marketplace add shurijoc/tracer
/plugin install tracer@tracer
```

Update with `/plugin update tracer@tracer`. Requires `gh auth login`; Node.js optional (C4 diagrams only). For local development: `claude --plugin-dir /path/to/tracer`.

## Quick start

Run `/tracer` at the root of the repo you want to improve. First run sets up the target (persona / metric / eval) interactively; later runs advance the loop on their own. **Watch the regenerated dashboard and step in when it stalls** — the rest is in the [design doc](https://shurijoc.github.io/tracer/).

## License

[MIT](LICENSE)
