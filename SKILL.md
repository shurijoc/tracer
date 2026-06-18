---
name: tracer
description: >
  定量ゴール駆動の自律改善ループを PM として運用するスキル。打つコマンドは `/tracer` の 1 本だけ。
  skill が state を読み、init / roadmap 作成 / 巡回 / 顧問 escalation / 完了報告 のいずれかを
  自動で実行する。どの repo でも使える (state は各 repo の .claude/goals/ に置く)。毎サイクル末に
  HTML ダッシュボードを更新し、それを見て介入判断する。
  「tracer」「ゴールループ」「PM 巡回」などと言われたら使う。
---

# tracer — 定量ゴール駆動の自律改善ループ (PM ハブ)

打ち方は **`/tracer` の 1 本だけ**。skill が現在 state を読んで、必要な action を 1 つ実行する。
複雑なフェーズ判定や autonomy 制御は skill 内に閉じる。skill は global、**state は実行時の repo に置く**
(repo を跨いで state を共有しない)。

## 用語

- **improvement**: 改善対象 1 つ (旧 `role`)。metric (数値) で測れる仕事のまとまり。
  例: `bugfix` / `perf` / `kpi`。**並走前提**。autonomy は repo × improvement 単位

## 並走原則 (重要)

improvement は**並走前提**で設計する。1 active 原則は採らない。

- 同一 repo 内に複数 improvement が active でよい (例: `web` repo なら `latency` と `signup` を並走)
- state ファイル (goal file / dashboard / decisions / activity) は improvement 毎に分離し、
  別セッション同時実行でも書き込み競合が起きない構造にする
- 新規 improvement の init を「前任 improvement の完了/pause」で待たない。
  ユーザーが新規追加を依頼したらそのまま init する

## 設計原則 (変更禁止の芯)

1. **定量ゴール必須**: 検証可能な報酬を 2 層持つ
   - micro `eval`: Issue 単位の合否ゲート (決定論的コマンド、exit 0 = 合格)
   - macro `metric`: ゴール指標。**フェーズ/ゴール完了は Issue 消化数でなく metric 改善で判定**
2. **context 非依存**: state は goal file / Issue / git / `_pm/*.md` のみに置く。
   毎サイクル冒頭にゼロから読み直す。PM session は `/clear` されても巡回が壊れないこと
3. **reward hacking 防止**: `eval:` / `metric:` 定義の変更は autonomy level に関わらず
   **ユーザー承認必須**。PM が自分で報酬関数を緩めてはならない。
   防御はプロンプトの禁止文に頼らず機械チェックで行う: goal file の `repo.protected_paths`
   (計測/gate/validation コード・truth 等) への diff は自動 escalation (tamper check)、
   worker の eval 自己申告は別 subagent の再実行で独立検証 (verifier 分離)
4. **PM は読み専 + 代筆者**: 実装しない。ユーザーの決定を goal file に書き戻すのが書き込み権の根拠

## ファイル配置 (実行時の repo root 基準)

state は **improvement 毎に分離**する。共通ファイルは持たない (別セッション並走時の書き込み競合回避)。

```
<repo>/.claude/goals/<improvement>.md                    # improvement 毎の goal file (正本 state)
<repo>/.claude/goals/c4.json                             # repo 共通の C4 モデル (improvement 横断・1 ファイル)
<repo>/.claude/goals/_pm/decisions-<improvement>.md      # improvement 毎の PM 推奨 vs 実決定突合ログ
<repo>/.claude/goals/_pm/activity-<improvement>.md       # improvement 毎の PM 巡回ログ
<repo>/.claude/goals/_pm/dashboard-<improvement>.html    # improvement 毎の現在地ダッシュボード
```

`c4.json` だけは improvement 毎でなく **repo 共通の 1 ファイル** (アーキテクチャは improvement 横断の repo 資産)。
各 improvement dashboard はこの同じモデルを表示し、その improvement が触る node を強調する (後述 Step 3)。

初回 init 時に存在しなければ、この skill ディレクトリの `templates/` から複製して作る。
git repo でない場所では動かさない (state の監査性が成立しないためユーザーに報告して停止)。

**旧形式互換**: `_pm/decisions.md` / `_pm/activity.md` / `_pm/dashboard.html` (improvement suffix なし) が
残っている repo では、新規読み書きは improvement 毎 path に固定する。旧 md は履歴として touch せず残し、
旧 dashboard.html は次回再生成時に削除して improvement 毎 dashboard に置き換える。

## repo 固有機構の検出 (init 時に確認し goal file に記録)

- **worktree 機構**: repo の Makefile に `wt-start`/`wt-end` があればそれを使う。
  なければ汎用 fallback:
  `git worktree add ../<reponame>-wt-<branch> -b <branch>` / 完了後 `git worktree remove`
- **実装フロー skill**: repo に issue-implement 系 skill があれば subagent にそれを踏襲させる。
  なければ汎用フロー: Issue 読む → worktree で実装 → eval 合格まで反復 → PR 作成
- 検出結果は goal file の `repo:` セクションに書き、巡回時はそれに従う (毎回再検出しない)

---

## 実行: `/tracer` 1 本だけ

毎サイクル、improvement 毎に independently 判定し、**improvement 毎に最初にマッチした action を 1 つ実行**して終了する。
複数 improvement が active なら、同一サイクルで improvement A は通常巡回、B は顧問 escalation、C は完了報告、を並列実行してよい。

### Step 0: state 復元 (毎回必ず)

`<repo>/.claude/goals/*.md` 全件 + `_pm/decisions-*.md` を読む (旧形式の `_pm/decisions.md` も残っていれば読む)。
会話履歴の記憶に頼らない。git repo 外 / gh 未認証なら巡回せずユーザーに報告して停止。

### Step 1: action 判定 (improvement 毎、優先順)

各 improvement について、以下を上から順に判定し最初にマッチした action を採用する。

| 条件 | action |
|---|---|
| A. `<repo>/.claude/goals/` が空 or improvement file 0 件 | **init モード** (repo 全体で 1 回) |
| B. improvement file あるが `## Phases` が空 or 全 Issue 未起票 | **roadmap モード** |
| C. metric Log が **5 サイクル以上**記録されていて、**その直近 5 点が期待方向に動いていない (改善 0)** | **顧問 escalation モード** |
| D. (C に該当しない =stall していない) **open Issue がまだある** | **通常巡回モード** |
| E. target 達成済 | **完了報告モード** |

A だけは repo 全体で 1 回 (init は新規 improvement 追加のため)。B〜E は improvement 毎に独立判定し、
**同一サイクルで複数 improvement を異なる action で並列実行する**。

ユーザーの確認単位は「improvement 毎の短報」で担保する (action を 1 個に絞らない)。

### Step 2: action 実行

#### A. init モード

skill 概要を 10 行程度で説明 (3 モード + 2 層報酬の考え方) し、improvement 名を聞く。
例を添える: `bugfix` (エラー件数削減) / `perf` (応答速度改善) / `kpi` (プロダクト指標達成)。
improvement 名は自由だが「metric が数値で取れる仕事」であることが条件、と伝える。
図解ドキュメント: `~/.claude/skills/tracer/index.html` を open するコマンドを提示してよい。

以下が揃うまで init 完了扱いしない:

1. **persona**: improvement の専門性と禁止事項 (例: 対症療法 patch 禁止)
2. **metric.measure**: 決定論的に数値 1 つを stdout に吐くコマンド
   - **実際に実行して動作確認するまで init を閉じない**
   - 現状値が機械的に取れないなら「計測スクリプト整備」を P0 フェーズとして先頭に置く
3. **metric.baseline**: measure を今実行した実測値 + 計測日
4. **metric.target / deadline**: 数値目標と期限。定性的な目標は却下し、数値化を求める
5. **eval**: Issue 単位の合否コマンド (repo のテスト/lint 実行コマンドを検出して提案)

`templates/goal-template.md` を複製して `<repo>/.claude/goals/<improvement>.md` を作成。
方針提示時は懸念 1〜2 個を添える (ユーザーに判断・承認を求めるときは具体的な懸念点を 1〜2 個添える。
「これで良いか」だけの質問は避ける)。

**C4 モデル生成 (repo 初回のみ)**: `<repo>/.claude/goals/c4.json` が無ければ生成する。
**Explore subagent (model: haiku で可、規模が大きければ sonnet)** に repo を走査させ、
`templates/c4-template.json` のスキーマに沿って context(L1)/container(L2)/component(L3) を埋める。

- subagent への指示: コード構造・README・主要 entrypoint・外部依存 (DB/API/SaaS) を読み、
  各 node に `id`(一意・英数) / `name` / `kind`(person|system|external|container|component|db) / `desc` を、
  関係に `edges`(from/to/label) を付ける。`paths` (node が対応する file glob) は分かる範囲で。
  **`name` と `desc` と `edges.label` は日本語で書く** (英語の固有名詞は `tech` に技術名として逃がす。
  例: name "巡回スキル本体" / tech "SKILL.md")。`id` だけ英数の一意キーにする。
  **過剰に細かくしない** (L2 は 5〜10 container、L3 は主要 container 1〜2 個ぶんに留める)
- `node.improvements`: その node を今 init した improvement が触るなら improvement 名を入れる。
  判定は goal file の `repo.protected_paths` / persona / 想定フェーズ範囲から。曖昧なら空でよい
- `updated` に init 日 (YYYY-MM-DD)、`generated_by` に `tracer init (Explore subagent)` を入れる
- 既に c4.json がある repo (2 個目以降の improvement の init): 再生成せず、新 improvement が触る
  既存 node の `improvements` 配列に improvement 名を**追記するだけ**にする (アーキは変えない)

完了したら **次回 `/tracer` で B に進む**。

#### B. roadmap モード

ユーザーと対話してフェーズを全て書き切り、各フェーズで Issue を起票する。

```bash
gh label create "goal:<improvement>" --color 1d76db 2>/dev/null; true
gh issue create --title "..." --label "goal:<improvement>" --body "..."
```

完了したら goal file の `## Phases` に Issue 番号を記録。次回 `/tracer` で D に進む。

#### C. 顧問 escalation モード (metric 5 サイクル停滞)

通常巡回より優先する。stalled improvement に対し:

- **顧問 (opus + effort max)** を 1 回だけ起動。read-only、実装させない
  1. 親セッションを `/effort max` に上げる
  2. 分析 subagent を `model: opus` で起動 (effort は継承)
  3. 終わったら `/effort medium` に戻す
- prompt に必ず含める: goal file の persona/metric、Issue コメントの全試行ログ
  (何を試してどうダメだったか)、metric 推移。丸投げ禁止
- 出力: 原因仮説 + 改善 Issue の起票案
- 起票の可否は autonomy に従う:
  - L0: ユーザーに推奨案 + 懸念 1〜2 個で提案
  - L1+: PM が直接起票し `_pm/decisions-<improvement>.md` に記録、次の短報で事後報告
- 上限: 同一停滞局面につき 1 回 (連発しない)

#### D. 通常巡回モード

active improvement 毎に以下を実行 (**複数 improvement は同一メッセージで並列 dispatch**):

1. **metric 計測**: `metric.measure` を実行し、goal file の `## Log` に追記
   ```
   2026-06-10 metric: 38 (baseline 42 / target <=20)
   ```
2. **dispatch (improvement 毎に 1 Issue)**:
   - 現フェーズの open Issue から 1 件選ぶ (escalation 凍結中の Issue は除外)
   - Agent tool で subagent を起動。prompt に注入するもの:
     - goal file の persona / eval コマンド / `repo:` セクション (worktree 機構・実装フロー)
     - Issue 番号と過去の試行ログ (失敗理由を読んで別アプローチを取れ、と明示)
     - worktree 隔離必須、**AskUserQuestion 禁止・ユーザー確認なしで自走**。eval 合格まで自分で反復し、
       合格したら PR 作成、不合格のまま手詰まりなら理由を Issue コメントに残して終了
     - `repo.protected_paths` に触れる変更は実装せず、必要性を Issue コメントに書いて終了
       (eval/gate/計測コード・truth データの変更はユーザー承認経由のみ)。baseline を差し替える
       flag (例: `--accept-new-baseline`) の使用も禁止
     - 報告は要約のみ (詳細は PR / Issue コメントに書かせる)
3. **独立検証 (合格処理の前に必須)**:
   - **tamper check**: `git diff --name-only origin/main...<branch>` を `repo.protected_paths` と突合。
     1 ファイルでもヒットしたら eval 結果に関わらず escalation 扱い
   - **verifier 分離**: 実装 worker とは**別の** subagent に PR branch 上で eval を再実行させ独立確認
4. **結果反映**:
   - **eval 合格 (PR あり)**:
     - L0: PR は merge せずユーザーへの短報に列挙
     - L1+: CI green を確認して merge → Issue クローズ → worktree 削除
     - 該当 Issue に ✅、フェーズ内全消化ならフェーズ判定 (下記) へ
   - **不合格**: Issue コメントに `試行 n/5: <失敗理由>` を記録
   - **試行 5/5 到達 (escalate_after)**: Issue に `escalated` ラベル + 凍結。autonomy に従い処理 (下表)
5. **フェーズ判定** (metric が主、Issue 消化は従):
   - フェーズの Issue 全消化 + metric が期待方向に動いた → 次フェーズへ前進
   - Issue 全消化したのに metric が動かない → 次回サイクルの C (顧問 escalation) でリダイレクトされる
   - target 達成 → improvement を inactive 化 (次回サイクルで E に進む)
   - deadline 超過で未達 → escalation 扱いでユーザーに判断を仰ぐ

| autonomy | escalation 時の挙動 |
|---|---|
| L0 | ユーザーに質問。**必ず PM の推奨案 + 懸念 1〜2 個を添える** |
| L1 | PM が決定して即実行。`_pm/decisions-<improvement>.md` に記録、次の短報で事後報告 (ユーザー拒否権) |
| L2 | 記録のみ。週次サマリに集約 |

#### E. 完了報告モード

全 active improvement が target 達成。ユーザーに報告し、improvement を inactive 化してループから外す。
他に未着手の improvement 候補があれば提案 (新規 init を促す)。

### Step 3: ダッシュボード再生成 (毎サイクル必ず、improvement 毎)

action 実行後、**この巡回で触れた improvement それぞれ**について `<repo>/.claude/goals/_pm/dashboard-<improvement>.html` を再生成する。
雛形: `~/.claude/skills/tracer/templates/dashboard-template.html` (single-improvement 用 1 枚) を読み込んで中身を差し替える。

旧形式の共通 `_pm/dashboard.html` が残っていれば、初回再生成時に削除する。

各 dashboard に必ず含める要素 (1 improvement 1 ページ):

- **今サイクルの現在地**: この improvement に対して走らせた action (A〜E) と判定理由
- **metric 推移**: baseline / 現在 / target + 直近 N 点の sparkline
- **現フェーズと進捗**: Issue 消化率
- **autonomy level (L0/L1/L2)** と直近の判断突合結果 (連続一致 streak)
- **凍結中 Issue 一覧**
- **介入候補セクション**: ユーザーに判断を仰ぎたい項目 (L0 escalation 案、顧問起票案、merge 待ち PR)
- **次回 `/tracer` の予想 action**: 次サイクルでこの improvement に当たりそうな action と理由
- **C4 アーキテクチャ**: 下記の手順で `c4.json` をインライン埋め込み (template の C4 セクションが描画)

**C4 セクションの埋め込み (重要)**: C4 図は **Mermaid を mmdc で SVG 化してインライン**する方式
(自前 JS レンダラは廃止。レイアウトは dagre が担うので node/edge が潰れない・JS ゼロ・`file://` で動く)。
bundled script 1 本で「c4.json → mermaid → mmdc 検証 → SVG インライン → タブ付きフラグメント」が回る:

```bash
python3 ~/.claude/skills/tracer/scripts/c4-to-section.py \
  <repo>/.claude/goals/c4.json <improvement>
```

stdout の HTML フラグメントを dashboard の `{{C4_SECTION}}` にそのまま差し込む。
第 2 引数の improvement 名に一致する `node.improvements` の node が **青枠でハイライト**される。
mmdc は `npx -y -p @mermaid-js/mermaid-cli mmdc` で都度取得 (グローバル不要)。

- c4.json が**無い / 壊れ / npx 不在 / mmdc 失敗**でもスクリプトは 0 終了し、その旨の断片を返す
  (dashboard は壊れない)。無い場合は余力があれば init の C4 生成手順で作る
- c4.json が古い (`updated` が 60 日超) と気づいたら短報で再生成を提案 (フラグメントに更新日を表示)
- **アーキ変更を伴う Issue を merge した**サイクルは、Explore subagent に c4.json を差分更新させ
  `updated` を当日に更新してから再生成する (頻繁な再生成は不要。構造が変わった時だけ)

### Step 4: ログ + 短報

- improvement 毎に `_pm/activity-<improvement>.md` に 1〜3 行追記
- ユーザーへの短報 (毎サイクル数行)。**冒頭に improvement 毎の dashboard フルパスを列挙**:

```
=== tracer 巡回 2026-06-10 14:30 ===
dashboards:
  bugfix: <repo>/.claude/goals/_pm/dashboard-bugfix.html
  perf:   <repo>/.claude/goals/_pm/dashboard-perf.html
bugfix: [D 通常巡回] metric 38/42→20 | #14 merge 済 | #15 試行2/5 | 次回予想 D
perf:   [D 通常巡回] metric 310ms/350→200 | #21 PR 待ち (L0: merge 判断ください) | 次回予想 D
介入待ち: perf #21 merge 判断
```

---

## autonomy 昇格ルール

- improvement 毎に `_pm/decisions-<improvement>.md` に「PM 推奨 / 実決定 / 一致したか」を毎回記録
- **連続 5 回一致 → PM が昇格を提案、ユーザー承認で 1 段上げる** (L0→L1→L2)
- 不一致が出たら連続カウントは 0 に戻す
- 昇格しても原則 3 (eval/metric 定義変更の承認必須) は解除されない
- autonomy は repo × improvement 単位 (repo・improvement が違えば実績も別カウント)

`_pm/decisions-<improvement>.md` エントリ形式:

```
## 2026-06-10 #14 escalation
- 状況: 5 回失敗。test_merge が flaky の疑い
- PM 推奨: #14 を「flaky test 修正」と「本体 fix」に分割
- 実決定: 採用 (そのまま)
- 一致: ✅ (連続 3/5)
```

## 自己改善が回る場所 (3 層)

| 層 | 仕組み | 報酬 |
|---|---|---|
| L1 worker | 失敗ログを Issue コメントに蓄積 → 次試行が読んで別アプローチ | eval |
| L2 計画 | metric 停滞 → C 顧問 escalation → Issue 再設計 | metric |
| L3 PM | `_pm/decisions-<improvement>.md` 突合 → autonomy 昇格 / 同型失敗の再発 → persona・フェーズ定義の修正提案 (ユーザー承認) | 判断一致率 |

## Error Handling

| 状況 | 対応 |
|---|---|
| metric.measure が失敗 | その improvement の dispatch をスキップし、計測復旧を escalation (計測なしで作業を進めない) |
| subagent が PR 作成前に異常終了 | Issue コメントに状況記録、試行回数は消費しない。`git worktree list` で残骸確認して削除 |
| 同一 worktree branch 衝突 | 既存 worktree パスを再利用 |
| goal file が手で壊されている | 巡回を止めてユーザーに報告 (推測で修復しない) |
| git repo 外 / gh 未認証 | 巡回せずユーザーに報告 |
| dashboard 雛形が見つからない | 巡回は続行、短報の末尾に「dashboard 未生成」と明示してユーザーに通知 |
| c4.json が無い / 壊れ / mmdc 失敗 | `c4-to-section.py` が 0 終了で「未生成/失敗」断片を返す。それを `{{C4_SECTION}}` に入れる。巡回は止めない。推測で修復しない |

## References

- テンプレート: この skill ディレクトリの `templates/` (`goal-template.md` / `dashboard-template.html` / `c4-template.json` / `activity.md` / `decisions.md`)
- C4 スキーマ: `templates/c4-template.json` (context/container/component の node+edge。`node.improvements` で dashboard 強調)
- C4 レンダラ: `scripts/c4-to-section.py` (c4.json → mermaid → mmdc で SVG 化 → タブ付き自己完結フラグメント。JS ゼロ)
- 図解: `~/.claude/skills/tracer/index.html`
