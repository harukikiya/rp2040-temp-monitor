---
description: 指定したissueの作業開始を打刻する
allowed-tools: Bash(gh issue comment:*), Bash(gh issue view:*)
---

issue #$ARGUMENTS の作業開始を打刻してください。

手順:

1. `gh issue view $ARGUMENTS --json title,state` でissueの存在と状態を確認する。closedの場合は打刻せず、ユーザーに確認する。
2. 以下のコマンドで打刻コメントを投稿する:

    gh issue comment $ARGUMENTS --body "⏱️ WORK_START"

3. 投稿後、「#$ARGUMENTS（<タイトル>）の作業開始を記録しました」と報告する。
