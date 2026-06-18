# tracer

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Claude Code skill](https://img.shields.io/badge/Claude_Code-skill-7c5cff.svg)](https://claude.com/claude-code)

> 定量ゴール (North Star Metric) に向かって**自律改善ループ**を PM として回す [Claude Code](https://claude.com/claude-code) skill。

打つコマンドは `/tracer` の 1 本だけ。skill が現在の state を読んで、init / roadmap / 顧問 escalation / 通常巡回 / 完了報告 のいずれかを自動で実行する。毎サイクル末に improvement 毎の HTML ダッシュボードを再生成し、人間はそれを見て介入判断する。

## 目次

- [これは何か](#これは何か)
- [設計思想](#設計思想)
- [前提](#前提)
- [インストール](#インストール)
- [クイックスタート](#クイックスタート)
- [機能一覧](#機能一覧)
- [仕組み (設計解説 HTML)](#仕組み-設計解説-html)
- [ディレクトリ構成](#ディレクトリ構成)
- [License](#license)

## これは何か

「数値で測れる改善目標」を 1 つ決めると、tracer がその達成までを PM として回し続ける。

- **対象**: テストのエラー件数、API 応答速度、プロダクト KPI など、決定論的に数値が取れる改善対象 (improvement)
- **やること**: ゴールの分解 (roadmap) → GitHub Issue 起票 → worktree 隔離での実装 dispatch → 合否検証 → metric 計測 → ダッシュボード更新、を `/tracer` 1 本で回す
- **人間の役割**: ダッシュボードを見て、詰まったらフィードバック・テコ入れする。合格基準 (eval / metric) の変更は常に人間の承認が要る

state は実行時の repo の `.claude/goals/` に置かれる。skill 自体はどの repo でも使える。

## 設計思想

- **loop + eval + durable state + gate の分離**: 再発火の器 (loop)、合否ゲート (外部 eval)、git/Issue に置く durable state、報酬関数の保護ゲートをそれぞれ独立に持つ
- **2 層報酬**: micro = Issue 単位の合否 `eval` (決定論的・exit 0)、macro = ゴール指標 `metric`。フェーズ/ゴールの完了は Issue 消化数ではなく **metric の改善**で判定する
- **reward hacking 防止**: `eval` / `metric` 定義の変更はユーザー承認必須。`protected_paths` への diff は tamper check で自動 escalation、worker の自己申告は別 subagent の再実行で独立検証する
- **autonomy L0→L1→L2**: PM の権限は判断一致の実績 (連続 5 回) で段階的に広がる。合格基準だけは永久にユーザーのもの
- **HTML dashboard で介入判断**: 毎サイクル末にダッシュボードを再生成。人間は「ダッシュボードを見て、詰まったら FB・テコ入れする」のが運用

## 前提

- [Claude Code](https://claude.com/claude-code) 導入済み
- `gh auth login` 済み (roadmap モードで GitHub Issue を起票するため)
- C4 図の生成には Node.js (`npx` 経由で mermaid-cli を取得) が必要。無くても巡回は 0 終了で継続する

## インストール

symlink で入れる。`git pull` で skill が自動更新される構成。

```bash
git clone https://github.com/shurijoc/tracer.git
ln -s "$(pwd)/tracer" ~/.claude/skills/tracer   # リンク名は tracer 固定 (frontmatter name と一致させる)
```

## クイックスタート

改善したい repo のルートで `/tracer` を実行する。

1. **初回 (init モード)**: 改善対象 (improvement) の persona / metric (計測コマンド) / eval (合否コマンド) を対話で収集する
2. **2 回目以降**: skill が state を読んで roadmap → 通常巡回 → 完了報告 を自動で進める

```bash
cd path/to/your-repo
# Claude Code で:
/tracer
```

複数の improvement を並走させてよい (state は improvement 毎に分離される)。

## 機能一覧

- `/tracer` 1 コマンドで 5 状態 (init / roadmap / 顧問 escalation / 通常巡回 / 完了報告) を自動判定・実行
- improvement (改善対象) の**並走**サポート (state は improvement 毎に分離)
- repo 共通の C4 アーキテクチャモデル (`c4.json`) を Mermaid → mmdc で SVG 化し、dashboard にインライン
- metric 5 サイクル停滞時の顧問 escalation (opus + effort max)
- worktree 隔離での Issue 実装フロー dispatch、独立検証 (tamper check + verifier 分離)

## 仕組み (設計解説 HTML)

設計思想の図解は **self-contained HTML** にまとまっている (依存なし・JS ゼロ)。

- 🌐 GitHub Pages: <https://shurijoc.github.io/tracer/>
- 📄 リポジトリ内: [`index.html`](index.html) (ローカルで開く)

## ディレクトリ構成

```
SKILL.md                   # skill 本体 (実行時に Claude が読む仕様)
index.html                 # 設計解説 (依存ゼロの self-contained HTML)
scripts/c4-to-section.py   # c4.json → C4 セクション HTML フラグメント生成
templates/                 # goal / dashboard / c4 / activity / decisions の雛形
```

## License

[MIT](LICENSE)
