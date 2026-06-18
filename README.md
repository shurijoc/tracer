# tracer

定量ゴール (North Star Metric) に向かって**自律改善ループ**を PM として回す Claude Code skill。
打つコマンドは `/tracer` の 1 本だけ。skill が現在の state を読んで、init / roadmap / 顧問 escalation / 通常巡回 / 完了報告 のいずれかを自動で実行する。毎サイクル末に improvement 毎の HTML ダッシュボードを再生成し、人間はそれを見て介入判断する。

## 📊 設計解説 (HTML)

設計思想の図解は **self-contained HTML** にまとまっている (依存なし・JS ゼロ)。

- GitHub Pages: <https://shurijoc.github.io/tracer/docs/overview.html> (Pages 有効時)
- リポジトリ内: [`docs/overview.html`](docs/overview.html) (ローカルで開く)

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

## インストール (symlink)

```bash
git clone https://github.com/shurijoc/tracer.git
ln -s "$(pwd)/tracer" ~/.claude/skills/tracer   # リンク名は tracer 固定 (frontmatter name と一致させる)
```

symlink にしておくと `git pull` で skill が自動更新される。

## クイックスタート

改善したい repo のルートで `/tracer` を実行すると init モードに入り、改善対象 (improvement) の persona / metric (計測コマンド) / eval (合否コマンド) を対話で収集する。次回以降の `/tracer` は state を読んで roadmap → 通常巡回 → 完了報告 を自動で進める。

## 機能一覧

- `/tracer` 1 コマンドで 5 状態 (init / roadmap / 顧問 escalation / 通常巡回 / 完了報告) を自動判定・実行
- improvement (改善対象) の**並走**サポート (state は improvement 毎に分離)
- repo 共通の C4 アーキテクチャモデル (`c4.json`) を Mermaid → mmdc で SVG 化し、dashboard にインライン
- metric 5 サイクル停滞時の顧問 escalation (opus + effort max)
- worktree 隔離での Issue 実装フロー dispatch、独立検証 (tamper check + verifier 分離)

## ディレクトリ構成

```
SKILL.md                       # skill 本体
docs/overview.html             # 設計解説 (HTML が主役)
scripts/c4-to-section.py       # c4.json → C4 セクション HTML フラグメント生成
templates/                     # goal / dashboard / c4 / activity / decisions の雛形
```

## License

[MIT](LICENSE)
