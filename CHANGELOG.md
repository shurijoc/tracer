# Changelog

Versioned per [semver](https://semver.org); the canonical version is in [`.claude-plugin/plugin.json`](.claude-plugin/plugin.json).
Harness (`skills/tracer/SKILL.md` / `templates/` / `scripts/`) changes are eval-gated — see [`HARNESS.md`](HARNESS.md).
Each entry: what changed, why, and the eval result at the time (`python evals/run.py det` + `grade`).

## Unreleased

### Changed
- **Plugin directory submission prep (#6).** Added `author.url` to `plugin.json`. SKILL.md `$TRACER_DIR` find recipe now documents its scope (only Claude Code's own plugin/skill install dirs — not arbitrary user files) so directory reviewers can quickly verify check 3 (no out-of-directory access). `claude plugin validate . --strict` ✔, det 8/8, behavioral 12/12.

## [0.2.1] - 2026-06-18

### Fixed
- **Bundled-file path resolution.** 0.2.0 referenced bundled scripts/templates via `${CLAUDE_PLUGIN_ROOT}`, but a live install smoke test showed that variable is **empty** in the ad-hoc bash the skill runs (it only expands in hooks/MCP/LSP/monitors, not skill-issued bash). SKILL.md now resolves `$TRACER_DIR` once via `find ~/.claude/plugins/cache ~/.claude/skills -path '*/skills/tracer/SKILL.md' | sort -V | tail -1`, working for both plugin install and dev symlink. Design-doc links now point to the GitHub Pages URL instead of a local path. Verified by installing the plugin and running the c4 render end-to-end (exit 0, valid fragment).

## [0.2.0] - 2026-06-18

### Changed (breaking — distribution)
- **Ship as a Claude Code plugin** instead of a symlinked skill. Repo restructured to the plugin layout (`.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json`, skill moved to `skills/tracer/`). Install: `/plugin marketplace add shurijoc/tracer` → `/plugin install tracer@tracer`.
- SKILL.md references bundled files via `${CLAUDE_PLUGIN_ROOT}` (cwd at runtime is the user's repo).

### Removed
- `VERSION` file and `scripts/version-check.sh` + the SKILL.md Step 0 self-update hook. Updates now ride the plugin system (`/plugin update`, or marketplace auto-update); the canonical version lives in `plugin.json`. The bespoke `git pull` self-updater was non-standard.

## [0.1.0] - 2026-06-18

### Added
- Harness engineering operation: [`HARNESS.md`](HARNESS.md) playbook + `evals/` suite (deterministic c4 tests + behavioral golden cases for action selection A–E and triggering).
- First baseline ([`evals/baseline.json`](evals/baseline.json)), answer model `claude-sonnet-4-6`: **deterministic 8/8**, **behavioral 10/12**.
- Versioning + self-update: [`VERSION`](VERSION) + git tags, and `scripts/version-check.sh` run from SKILL.md Step 0 (throttled 24h, fail-open). A clean consumer checkout fast-forwards itself; a maintainer's working clone is only notified, never mutated.

### Changed
- `SKILL.md` Step 1: clarified the C/D action boundary. **C** now requires the metric Log to have **>=5 recorded cycles AND no improvement** across the last 5; **D** explicitly states the "not stalled" precondition. Eval-gated: on **opus** (the model tracer runs on) `as-open-issues-progress` now resolves to **D** (2/2) and `as-new-improvement-added` to **A**. On **sonnet** the open-issues case still mis-picks **C** — a model-capability gap, not a spec gap (see issue).

### Open findings
- `trig-pm-patrol` (medium): the trigger phrase "PM 巡回" does not reliably fire from the description alone (sonnet, 3/3 NO; not re-checked on opus). Tracked in an issue.

### Follow-ups (tracked in issues)
- Re-baseline the suite on **opus** (current baseline used sonnet, which is not the model tracer runs on).
