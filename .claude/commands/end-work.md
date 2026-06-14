---
description: 指定したissueの作業終了を打刻する（振り返りメモ付き）
allowed-tools: Bash(gh issue comment:*), Bash(gh api:*)
---

issue #$ARGUMENTS の作業終了を打刻してください。

手順:

1. このセッションで行った作業内容を1~3行に要約する
    （段階10の言語比較で使う振り返り材料になるため、躓いた点があれば必ず含める）。
2. 以下の形式で打刻コメントを投稿する:

    gh issue comment $ARGUMENTS --body "⏱️ WORK_END <作業内容の要約>"

3. 直近のWORK_STARTからの経過時間を概算し、「#$ARGUMENTS の作業終了を記録しました（約X時間Y分）」と報告する。
