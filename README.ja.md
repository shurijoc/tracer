# tracer

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Claude Code skill](https://img.shields.io/badge/Claude_Code-skill-7c5cff.svg)](https://claude.com/claude-code)

[English](README.md) | **日本語**

> 定量ゴール (North Star Metric) に向かって**自律改善ループ**を PM として回す [Claude Code](https://claude.com/claude-code) skill。打つコマンドは `/tracer` の 1 本だけ。

## 📖 ドキュメントは README ではなく HTML

md は読むのが疲れる。設計の中身 — 5 状態マシン・2 層報酬・reward hacking 防止・autonomy — は、ずっと読みやすい **self-contained HTML** (依存ゼロ・JS ゼロ) にまとめてある。**そっちが本体。この README は入口だけ。**

### 👉 [設計解説を読む](https://shurijoc.github.io/tracer/index.ja.html) &nbsp;·&nbsp; [English](https://shurijoc.github.io/tracer/)

(ローカルなら [`index.ja.html`](index.ja.html) / [`index.html`](index.html) を開く)

## インストール

```bash
git clone https://github.com/shurijoc/tracer.git
ln -s "$(pwd)/tracer" ~/.claude/skills/tracer   # リンク名は tracer 固定 (frontmatter と一致)
```

[Claude Code](https://claude.com/claude-code) と `gh auth login` が前提。Node.js は任意 (C4 図のみ)。

## クイックスタート

改善したい repo のルートで `/tracer` を実行する。初回は改善対象 (persona / metric / eval) を対話で設定し、2 回目以降は state を読んでループを自動で進める。あとは **再生成されるダッシュボードを見て、詰まったらテコ入れする**だけ — 残りは[設計解説](https://shurijoc.github.io/tracer/index.ja.html)に。

## License

[MIT](LICENSE)
