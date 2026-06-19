#!/usr/bin/env python3
"""
tracer harness eval runner.

Two layers (see HARNESS.md):

  1. deterministic  — code-based tests for scripts/c4-to-section.py.
                      Runs anywhere, no model, no network. CI-able.
  2. behavioral     — golden cases (evals/cases/*.json) whose answer is a
                      DISCRETE LABEL (an action letter A-E, or YES/NO). A fresh
                      model produces the labels; this script grades them by exact
                      match against the human-owned `expected`. Because the
                      output is a label, grading is code-based — no LLM judge,
                      so we sidestep the oracle problem.

usage:
  python evals/run.py det                 # run deterministic c4 tests
  python evals/run.py prompts [--kind K]  # emit per-case prompts for a fresh agent
  python evals/run.py grade answers.json  # grade {id: label} against expected
  python evals/run.py list                # list cases

exit code is non-zero on any failure, so this gates a release (regression suite).
"""
import sys, os, io, re, json, glob, importlib.util, contextlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES_DIR = os.path.join(ROOT, "evals", "cases")
C4 = os.path.join(ROOT, "skills", "tracer", "scripts", "c4-to-section.py")
SKILL_MD = os.path.join(ROOT, "skills", "tracer", "SKILL.md")
GOAL_TEMPLATE = os.path.join(ROOT, "skills", "tracer", "templates", "goal-template.md")


# ---------- load the c4 module (filename has a hyphen) ----------
def load_c4():
    spec = importlib.util.spec_from_file_location("c4_to_section", C4)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_main(mod, argv):
    """Call c4 main() with argv and capture stdout."""
    buf = io.StringIO()
    old = sys.argv
    sys.argv = argv
    try:
        with contextlib.redirect_stdout(buf):
            mod.main()
    finally:
        sys.argv = old
    return buf.getvalue()


# ---------- deterministic layer ----------
def det_tests():
    """Each test is (name, fn). fn raises AssertionError on failure."""
    mod = load_c4()
    tmp_missing = os.path.join(ROOT, "evals", "_does_not_exist.json")
    broken = os.path.join(ROOT, "evals", "_broken.json")
    empty = os.path.join(ROOT, "evals", "_empty.json")

    def t_fragment_shape():
        out = mod.fragment("x")
        assert out.startswith('<div class="c4-host">') and out.endswith("</div>"), out

    def t_esc_quotes():
        assert mod.esc('a"<b>') == "a&quot;&lt;b&gt;", mod.esc('a"<b>')

    def t_sid_safe():
        assert mod.sid("a b/c") == "n_a_b_c", mod.sid("a b/c")

    def t_missing_path_exit0():
        # contract: missing file -> 0 exit + fallback fragment, never raises
        out = run_main(mod, ["c4", tmp_missing, "imp"])
        assert "c4-host" in out and ("未生成" in out or "無い" in out), out

    def t_broken_json():
        with open(broken, "w") as f:
            f.write("{ not json ")
        try:
            out = run_main(mod, ["c4", broken, "imp"])
            assert "c4-host" in out and "壊れ" in out, out
        finally:
            os.remove(broken)

    def t_empty_nodes():
        with open(empty, "w") as f:
            json.dump({"levels": {"context": {"nodes": []}}}, f)
        try:
            out = run_main(mod, ["c4", empty, "imp"])
            assert "c4-host" in out and "空" in out, out
        finally:
            os.remove(empty)

    def t_build_mermaid_basics():
        level = {
            "nodes": [
                {"id": "u", "name": "User", "kind": "person"},
                {"id": "sys", "name": "Sys", "kind": "system", "improvements": ["perf"]},
                {"id": "db", "name": "DB", "kind": "db"},
                {"id": "ext", "name": "Ext", "kind": "external"},
            ],
            "edges": [{"from": "u", "to": "sys", "label": "uses"}],
        }
        mmd = mod.build_mermaid(level, "perf")
        assert mmd.startswith("flowchart LR"), mmd
        assert "n_sys" in mmd and "n_u" in mmd
        # highlighted improvement node gets the hl class
        assert "class n_sys hl;" in mmd, mmd
        # edge with label present
        assert 'n_u -->|"uses"| n_sys' in mmd, mmd
        # classDefs present
        for cls in ("classDef ext", "classDef db", "classDef person", "classDef hl"):
            assert cls in mmd, cls

    def t_build_mermaid_no_highlight():
        level = {"nodes": [{"id": "a", "name": "A", "kind": "system"}], "edges": []}
        mmd = mod.build_mermaid(level, "perf")  # no improvements -> no hl class line
        assert " hl;" not in mmd, mmd

    # ---- state SoT: completion / freeze derive from gh, not md (issue #10) ----
    def _phases_section(text):
        # extract "## Phases" through the next "## " heading (or EOF)
        m = re.search(r"^## Phases\s*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
        return m.group(1) if m else ""

    def t_goal_template_no_phase_checkbox():
        with open(GOAL_TEMPLATE) as f:
            phases = _phases_section(f.read())
        assert phases, "goal-template.md must have a ## Phases section"
        assert "- [ ]" not in phases and "- [x]" not in phases, (
            "goal-template.md ## Phases must not use checkboxes — completion is gh-derived. Found:\n" + phases
        )

    def t_goal_template_no_frozen_section():
        with open(GOAL_TEMPLATE) as f:
            text = f.read()
        assert not re.search(r"^## Frozen\b", text, re.M), (
            "goal-template.md must not have a ## Frozen section — escalated label is the source of truth"
        )

    def t_skill_marker_completion_from_gh():
        with open(SKILL_MD) as f:
            text = f.read()
        assert "DET-GATE: completion-from-gh" in text, (
            "SKILL.md must mark the completion-from-gh contract with <!-- DET-GATE: completion-from-gh -->"
        )

    def t_skill_marker_dashboard_from_gh():
        with open(SKILL_MD) as f:
            text = f.read()
        assert "DET-GATE: dashboard-derives-from-gh" in text, (
            "SKILL.md must mark the dashboard-derives-from-gh contract with <!-- DET-GATE: dashboard-derives-from-gh -->"
        )

    return [
        ("fragment_shape", t_fragment_shape),
        ("esc_quotes", t_esc_quotes),
        ("sid_safe", t_sid_safe),
        ("missing_path_exit0", t_missing_path_exit0),
        ("broken_json", t_broken_json),
        ("empty_nodes", t_empty_nodes),
        ("build_mermaid_basics", t_build_mermaid_basics),
        ("build_mermaid_no_highlight", t_build_mermaid_no_highlight),
        ("goal_template_no_phase_checkbox", t_goal_template_no_phase_checkbox),
        ("goal_template_no_frozen_section", t_goal_template_no_frozen_section),
        ("skill_marker_completion_from_gh", t_skill_marker_completion_from_gh),
        ("skill_marker_dashboard_from_gh", t_skill_marker_dashboard_from_gh),
    ]


def cmd_det():
    fails = 0
    for name, fn in det_tests():
        try:
            fn()
            print("  PASS  %s" % name)
        except Exception as e:
            fails += 1
            print("  FAIL  %s — %s" % (name, e))
    print("\ndeterministic: %d passed, %d failed" % (len(det_tests()) - fails, fails))
    return 1 if fails else 0


# ---------- behavioral layer ----------
def load_cases(kind=None):
    cases = []
    for path in sorted(glob.glob(os.path.join(CASES_DIR, "*.json"))):
        with open(path) as f:
            data = json.load(f)
        for c in data:
            if kind and c.get("kind") != kind:
                continue
            cases.append(c)
    return cases


def cmd_list():
    for c in load_cases():
        print("  %-28s [%s] expect=%s" % (c["id"], c.get("kind", "?"), c["expected"]))
    print("\n%d cases" % len(load_cases()))
    return 0


def cmd_prompts(kind=None):
    cases = load_cases(kind)
    print("# Hand each prompt below to a FRESH agent (a clean Claude with no")
    print("# memory of this eval). Collect answers as JSON {id: label} and run:")
    print("#   python evals/run.py grade answers.json")
    print("# Do NOT let the answering agent see `expected` — that is the ground truth.\n")
    for c in cases:
        print("=" * 72)
        print("ID: %s   (kind=%s)" % (c["id"], c.get("kind")))
        print("-" * 72)
        print(c["prompt"].strip())
        print()
    print("=" * 72)
    print("%d prompts. Return strictly: {\"<id>\": \"<label>\", ...}" % len(cases))
    return 0


def norm(s):
    return str(s).strip().upper().rstrip(".")


def cmd_grade(answers_path):
    with open(answers_path) as f:
        answers = json.load(f)
    # accept a flat {id: label} map, or a baseline file with an "answers" key
    if isinstance(answers, dict) and "answers" in answers and isinstance(answers["answers"], dict):
        answers = answers["answers"]
    cases = {c["id"]: c for c in load_cases()}
    total = len(cases)
    graded = 0
    passed = 0
    missing = []
    fails = []
    for cid, case in cases.items():
        if cid not in answers:
            missing.append(cid)
            continue
        graded += 1
        got = norm(answers[cid])
        exp = norm(case["expected"])
        if got == exp:
            passed += 1
            print("  PASS  %-28s %s" % (cid, exp))
        else:
            fails.append((cid, exp, got, case.get("rationale", "")))
            print("  FAIL  %-28s expected=%s got=%s" % (cid, exp, got))
    if missing:
        print("\n  MISSING answers for %d case(s): %s" % (len(missing), ", ".join(missing)))
    print("\nbehavioral: %d/%d graded, %d passed" % (graded, total, passed))
    for cid, exp, got, why in fails:
        print("  ↳ %s: %s (expected %s, got %s)" % (cid, why, exp, got))
    # regression gate: missing answers or any failure -> non-zero
    return 0 if (passed == total and not missing) else 1


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    cmd = sys.argv[1]
    if cmd == "det":
        return cmd_det()
    if cmd == "list":
        return cmd_list()
    if cmd == "prompts":
        kind = None
        if "--kind" in sys.argv:
            kind = sys.argv[sys.argv.index("--kind") + 1]
        return cmd_prompts(kind)
    if cmd == "grade":
        if len(sys.argv) < 3:
            print("usage: run.py grade answers.json")
            return 2
        return cmd_grade(sys.argv[2])
    print("unknown command: %s" % cmd)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
