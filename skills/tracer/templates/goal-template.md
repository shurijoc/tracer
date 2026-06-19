---
improvement: <improvement 名 (例: bugfix)>
status: active            # active | inactive (target 達成 or ユーザー指示で inactive)
persona: >
  <専門性と禁止事項。例: テスト駆動で根本原因を直す bug fix エンジニア。対症療法 patch 禁止>
eval: <Issue 単位の合否コマンド。exit 0 = 合格。例: npm test && npm run lint>
metric:
  measure: <数値 1 つを stdout に吐く決定論的コマンド。init 時に動作確認必須>
  baseline: <init 時の実測値> (<計測日>)
  target: "<比較式。例: <= 20>"
  deadline: <YYYY-MM-DD>
escalate_after: 5
autonomy: L0              # L0 | L1 | L2 (昇格は decisions.md の連続一致 5 回 + ユーザー承認)
repo:
  worktree: <make wt-start/wt-end | git worktree (汎用)>
  impl_flow: <repo の issue-implement 系 skill 名 | 汎用フロー>
  protected_paths: <eval/metric の計算に関わる path の grep -E 正規表現。worker が触れたら自動 escalation (SKILL.md Step 4 tamper check)>
---

## Phases

<!-- init で全フェーズを書き切る。各 Issue は起票済み番号で記録。
     完了/未完は GitHub Issue の open/closed が正本 (md にチェックボックスを持たない)。 -->
- P1: <フェーズ名> (#xx #yy)
- P2: <フェーズ名> (#zz)

<!-- 凍結中 Issue は GitHub の `escalated` label が正本。md には持たない。
     一覧: gh issue list --label escalated --label goal:<improvement> -->

## Log

<!-- 巡回毎に追記。metric 計測値 / Issue の進捗 / フェーズ判定 -->
<!-- 例: 2026-06-10 metric: 38 (baseline 42 / target <=20) | #14 merge 済 -->
