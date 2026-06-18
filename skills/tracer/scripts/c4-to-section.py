#!/usr/bin/env python3
"""
c4.json -> tracer dashboard 用の C4 セクション HTML フラグメントを生成する。

各 level (context/container/component) を Mermaid flowchart にし、mmdc で SVG 化して
インラインする。レイアウトは dagre が担うので node/edge が潰れない。出力は JS ゼロ・
自己完結 (CSS の :checked タブのみ)・file:// で動く。

usage:  c4-to-section.py <c4.json path> [<improvement name>]
stdout: C4 セクションの HTML フラグメント (dashboard の {{C4_SECTION}} に差し込む)
        c4.json 無し / 壊れ / mmdc 失敗でも 0 終了し、その旨のフォールバック断片を出す。
"""
import sys, os, re, json, html, subprocess, tempfile, shutil

LEVELS = [("context", "L1 Context"), ("container", "L2 Container"), ("component", "L3 Component")]


def esc(s):
    return html.escape(str(s if s is not None else ""), quote=True)


def sid(s):
    # mermaid node id は英数_ のみ安全
    return "n_" + re.sub(r"[^A-Za-z0-9_]", "_", str(s))


def mlabel(text):
    # mermaid の "..." ラベル内に入れる文字を無害化 (htmlLabels 前提で <br/> は自分で足す)
    t = str(text if text is not None else "")
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    return t


def fragment(inner):
    return '<div class="c4-host">' + inner + "</div>"


def note(msg):
    return fragment('<div class="c4-empty">' + esc(msg) + "</div>")


def build_mermaid(level, improvement):
    nodes = level.get("nodes") or []
    edges = level.get("edges") or []
    lines = ["flowchart LR"]
    hl_ids = []
    for n in nodes:
        nid = sid(n.get("id"))
        name = mlabel(n.get("name") or n.get("id") or "?")
        tech = n.get("tech")
        label = name + ("<br/><small>[" + mlabel(tech) + "]</small>" if tech else "")
        kind = (n.get("kind") or "system").lower()
        if kind == "person":
            shape = '(["' + label + '"])'
        elif kind == "db":
            shape = '[("' + label + '")]'
        else:
            shape = '["' + label + '"]'
        lines.append("  " + nid + shape)
        cls = []
        if kind == "external":
            cls.append("ext")
        if kind == "db":
            cls.append("db")
        if kind == "person":
            cls.append("person")
        if cls:
            lines.append("  class " + nid + " " + " ".join(cls) + ";")
        if improvement and improvement in (n.get("improvements") or []):
            hl_ids.append(nid)
    for e in edges:
        a, b = sid(e.get("from")), sid(e.get("to"))
        lbl = e.get("label")
        if lbl:
            lines.append("  " + a + ' -->|"' + mlabel(lbl) + '"| ' + b)
        else:
            lines.append("  " + a + " --> " + b)
    # classDef (neutral テーマ + 白背景前提の色)
    lines.append("  classDef ext stroke-dasharray:5 5,fill:#f4f4f2;")
    lines.append("  classDef db fill:#fdf3e0,stroke:#9a6700;")
    lines.append("  classDef person fill:#f2ecff,stroke:#7c5cff;")
    lines.append("  classDef hl fill:#eaf1fe,stroke:#2f6fed,stroke-width:3px;")
    if hl_ids:
        lines.append("  class " + ",".join(hl_ids) + " hl;")
    return "\n".join(lines)


def render_svg(mmd, workdir):
    src = os.path.join(workdir, "d.mmd")
    out = os.path.join(workdir, "d.svg")
    with open(src, "w") as f:
        f.write(mmd)
    try:
        subprocess.run(
            ["npx", "-y", "-p", "@mermaid-js/mermaid-cli", "mmdc",
             "-i", src, "-o", out, "-t", "neutral", "-b", "transparent"],
            check=True, capture_output=True, text=True, timeout=240,
        )
    except Exception as e:
        return None, str(getattr(e, "stderr", "") or e)
    with open(out) as f:
        svg = f.read()
    # <?xml?> / <!DOCTYPE> / 前置コメントを剥がし <svg...> 本体だけ残す
    m = re.search(r"<svg[\s\S]*</svg>", svg)
    return (m.group(0) if m else None), None


def main():
    if len(sys.argv) < 2:
        print(note("c4.json path 未指定"))
        return
    path = sys.argv[1]
    improvement = sys.argv[2] if len(sys.argv) > 2 else ""
    if not os.path.exists(path):
        print(note("C4 未生成。.claude/goals/c4.json が無い。次回 /tracer で生成される。"))
        return
    try:
        model = json.load(open(path))
    except Exception as e:
        print(note("c4.json が壊れている: " + str(e)))
        return
    levels = model.get("levels") or {}
    present = [(k, lbl) for k, lbl in LEVELS if levels.get(k) and (levels[k].get("nodes"))]
    if not present:
        print(note("C4 の node が空。"))
        return
    if not shutil.which("npx"):
        print(note("npx が無く mmdc を実行できない。node 環境を用意すると C4 図が出る。"))
        return

    updated = model.get("updated", "")
    work = tempfile.mkdtemp(prefix="tracer-c4-")
    radios, labels, panes = [], [], []
    try:
        for i, (key, lbl) in enumerate(present):
            mmd = build_mermaid(levels[key], improvement)
            svg, err = render_svg(mmd, work)
            rid = "c4tab_%s_%d" % (re.sub(r"[^a-z]", "", key), i)
            checked = " checked" if i == 0 else ""
            radios.append('<input type="radio" name="c4tabs" id="%s" class="c4-radio"%s>' % (rid, checked))
            labels.append('<label for="%s" class="c4-tab">%s</label>' % (rid, esc(lbl)))
            body = svg if svg else (
                '<div class="c4-empty">この level の図のレンダリングに失敗。<pre>%s</pre></div>' % esc((err or "")[:400]))
            panes.append('<div class="c4-pane">%s</div>' % body)
    finally:
        shutil.rmtree(work, ignore_errors=True)

    stale = ""
    if updated:
        stale = '<div class="c4-stale">C4 更新: %s</div>' % esc(updated)

    inner = (
        "".join(radios)
        + stale
        + '<div class="c4-tabbar">' + "".join(labels) + "</div>"
        + '<div class="c4-panes">' + "".join(panes) + "</div>"
        + '<div class="c4-legend"><span style="color:#2f6fed">青枠=この improvement が触る</span>'
        '<span style="color:#7c5cff">person</span><span style="color:#9a6700">db</span>'
        '<span style="color:#636c76">external(破線)</span></div>'
    )
    print(fragment(inner))


if __name__ == "__main__":
    main()
