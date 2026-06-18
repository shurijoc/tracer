# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## このリポジトリの性質

これはアプリではなく **Claude Code skill `tracer` 本体のリポジトリ**。成果物は「Claude が実行時に読む仕様 (`SKILL.md`) + 補助スクリプト + テンプレート + 設計解説 HTML」。ビルド/lint/テストのパイプラインは存在しない。

**配布は symlink**: `~/.claude/skills/tracer` がこの repo を指す。よってここの `SKILL.md` / `templates/` / `scripts/` への編集は、インストール済み skill の挙動に即時反映される (`git pull` = skill 更新)。frontmatter の `name: tracer` と symlink 名・skill 名は一致させること。

## 唯一の実行可能コード: `scripts/c4-to-section.py`

`c4.json` → Mermaid → `mmdc` で SVG 化 → タブ付き自己完結 HTML フラグメントを stdout に出す。dashboard の `{{C4_SECTION}}` に差し込む用途。

```bash
python3 scripts/c4-to-section.py <c4.json path> [<improvement name>]
```

検証方法 (専用テストは無いので手動実行で確認):
- 異常系: 存在しない path / 壊れた JSON / `npx` 不在 / `mmdc` 失敗 — **いずれも exit 0 + フォールバック断片**を返す契約。巡回を壊さないため。この不変条件を壊す変更は禁止。
- 正常系には Node.js (`npx -y -p @mermaid-js/mermaid-cli mmdc` で都度取得) が必要。第 2 引数の improvement 名に一致する `node.improvements` の node が青枠ハイライトされる。

## 状態の置き場所 (重要な境界)

skill が運用時に作る state (`<対象repo>/.claude/goals/`) は **この repo ではなく改善対象 repo 側**に置かれる。ここの `.gitignore` は `.claude/goals/` を無視しているので、開発中に手元で生成された state を誤ってコミットしない。state の正本フォーマットは `templates/` の雛形が定義する。

## アーキテクチャ (SKILL.md が実体)

`SKILL.md` が "プログラム" 本体で、`/tracer` 起動時に Claude がこれを読んで 1 action を実行する。設計の芯 (変更時に壊してはいけない不変条件):

- **5 状態マシン**: 毎サイクル冒頭で state をゼロから読み直し (context 非依存)、improvement 毎に init / roadmap / 顧問 escalation / 通常巡回 / 完了報告 のうち最初にマッチした 1 つを実行。複数 improvement は並走前提 (1 active 原則は採らない)。
- **2 層報酬**: micro `eval` (Issue 単位の決定論的合否, exit 0) と macro `metric` (ゴール指標)。**フェーズ/ゴール完了は Issue 消化数でなく metric 改善で判定**する。
- **reward hacking 防止**: `eval:` / `metric:` 定義の変更は autonomy に関わらずユーザー承認必須。`repo.protected_paths` への diff は tamper check で自動 escalation、worker の自己申告は別 subagent の再実行で独立検証 (verifier 分離)。
- **autonomy L0→L1→L2**: `_pm/decisions-<improvement>.md` の連続 5 回一致 + ユーザー承認で 1 段昇格。autonomy は repo × improvement 単位。合格基準 (eval/metric) は永久にユーザーのもの。
- **HTML dashboard**: 毎サイクル末に improvement 毎に再生成。人間はこれを見て介入判断する。

`templates/` ↔ `SKILL.md` ↔ `scripts/c4-to-section.py` は密結合: テンプレートのプレースホルダ名 (`{{C4_SECTION}}` 等)、`goal-template.md` の frontmatter キー (`protected_paths` 等)、`c4-template.json` のスキーマ (`levels`/`node.improvements`/`kind`) を変えるときは 3 者を揃えて直す。

## ドキュメントの二重化

対外ドキュメントは **英語を base、日本語を `.ja` 中置の変種** にする命名規約に統一している:

- `README.md` (英語・base) ↔ `README.ja.md` (日本語)
- `index.html` (英語・base) ↔ `index.ja.html` (日本語) — どちらも依存ゼロ・JS なしの設計解説、GitHub Pages 公開

**設計の中身は HTML に一本化している** (「md は読みづらい / HTML が楽」が tracer の主張なので、README をそれに従わせている)。README は薄いランチャー (タイトル + HTML への CTA + install/quickstart のみ) に保ち、設計思想・状態マシン・報酬モデル等を README に書き戻さないこと (書くと主張と矛盾し HTML と重複する)。よって設計の芯を変えたら直すのは原則 `index.html` + `index.ja.html` の 2 つ。README は導線が壊れていないかだけ確認する。`SKILL.md` と `templates/` は運用仕様・skill トリガー語の都合で日本語のまま (英語化すると skill 挙動に影響するため触らない)。

GitHub Pages は `main` ブランチの **root** (`/`) を公開ソースにしている (`gh api repos/<owner>/tracer/pages` の `source.path` が `/`)。`https://shurijoc.github.io/tracer/` → `index.html` (英語)、`.../index.ja.html` → 日本語。
