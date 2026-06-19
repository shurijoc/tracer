# tracer

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Claude Code skill](https://img.shields.io/badge/Claude_Code-skill-7c5cff.svg)](https://claude.com/claude-code)

[English](README.md) | **日本語**

> **計測可能なゴールに向けて repo 改善を自動で回す。** PM として動く [Claude Code](https://claude.com/claude-code) skill — 次の打ち手を選び、Issue を起票し、North Star Metric への進捗を追う。打つコマンドは `/tracer` の 1 本だけ。

## 📖 ドキュメントは README ではなく HTML

md は読むのが疲れる。設計の中身 — 5 状態マシン・2 層報酬・reward hacking 防止・autonomy — は、ずっと読みやすい **self-contained HTML** (依存ゼロ・JS ゼロ) にまとめてある。**そっちが本体。この README は入口だけ。**

### 👉 [設計解説を読む](https://shurijoc.github.io/tracer/index.ja.html) &nbsp;·&nbsp; [English](https://shurijoc.github.io/tracer/)

## インストール

Claude Code 内で:

```
/plugin marketplace add shurijoc/tracer
/plugin install tracer@tracer
```

更新は `/plugin update tracer@tracer`。`gh auth login` が前提。Node.js は任意 (C4 図のみ)。開発時はローカル checkout を読み込む: `claude --plugin-dir /path/to/tracer`。

## クイックスタート

改善したい repo のルートで `/tracer` を実行する。初回は改善対象 (persona / metric / eval) を対話で設定、2 回目以降は state を読んで自動で進む。あとは **再生成されるダッシュボードを見て、詰まったらテコ入れする** — 残りは[設計解説](https://shurijoc.github.io/tracer/index.ja.html)に。

## License

[MIT](LICENSE)
