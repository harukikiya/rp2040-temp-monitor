#!/usr/bin/env python3
"""issueコメントの打刻マーカーから作業時間を集計し、Markdownを生成する。

WORK_START / WORK_END を作業者ごとにペアリングし、
issue別・作業者別の作業時間表を docs/common/progress/worklog.md に出力する。
"""
import json
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

JST = ZoneInfo("Asia/Tokyo")

REPO = "harukikiya/rp2040-temp-monitor"
OUT = Path("docs/common/progress/worklog.md")
START, END = "WORK_START", "WORK_END"

def gh_api(path: str) -> list:
    """gh api --paginate でJSON配列を取得する。"""
    r = subprocess.run(
        ["gh", "api", "--paginate", path],
        capture_output=True, text=True, check=True,
    )
    # --paginate は複数のJSON配列を連結して返すことがあるため連結処理
    out, items = r.stdout.strip(), []
    dec = json.JSONDecoder()
    idx = 0
    while idx < len(out):
        obj, end = dec.raw_decode(out, idx)
        items.extend(obj)
        idx = end
        while idx < len(out) and out[idx] in " \n\r\t":
            idx += 1
    return items

def parse_ts(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))

def fmt_hours(seconds: float) -> str:
    h, m = int(seconds // 3600), int(seconds % 3600 // 60)
    return f"{h}h{m:02d}m"

def main() -> None:
    # TODO: issue数が100を超えたら gh_api 側で pageInfo/Link ヘッダによるページング対応が必要
    issues = gh_api(f"repos/{REPO}/issues?state=all&per_page=100")
    rows = []       # (issue番号, タイトル, 作業者, 回数, 合計秒)
    warnings = []   # 閉じられていない打刻

    for issue in issues:
        if "pull_request" in issue:     # PRを除外
            continue
        num, title = issue["number"], issue["title"]
        # TODO: issue数が100を超えたら gh_api 側で pageInfo/Link ヘッダによるページング対応が必要
        comments = gh_api(f"repos/{REPO}/issues/{num}/comments?per_page=100")
        open_start = {}                 # 作業者 -> 開始時刻
        totals = defaultdict(lambda: [0, 0.0])  # 作業者 -> [回数, 合計秒]

        for c in sorted(comments, key=lambda c: c["created_at"]):
            body_head = c["body"].strip().splitlines()[0] if c["body"].strip() else ""
            user, ts = c["user"]["login"], parse_ts(c["created_at"])
            if START in body_head and END not in body_head:
                if user in open_start:
                    warnings.append(f"#{num}: {user}のWORK_STARTが二重（{ts.astimezone(JST):%Y-%m-%d %H:%M}）")
                open_start[user] = ts
            elif END in body_head:
                if user in open_start:
                    dur = (ts - open_start.pop(user)).total_seconds()
                    totals[user][0] += 1
                    totals[user][1] += dur
                else:
                    warnings.append(f"#{num}: {user} のWORK_ENDに対応するSTARTが無い")

        for user, start_ts in open_start.items():
            warnings.append(f"#{num}: {user} の作業が未終了（{start_ts.astimezone(JST):%Y-%m-%d %H:%M} 開始）")
        for user, (n, sec) in totals.items():
            rows.append((num, title, user, n, sec))

    now = datetime.now(JST).strftime("%Y-%m-%d %H:%M JTC")
    lines = [
        "# 作業時間レポート",
        "",
        f"> 本ページはCIが打刻コメントから自動生成する（最終更新: {now}）。手で編集しないこと。",
        "",
        "| issue | タイトル | 作業者 | セッション数 | 合計時間 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for num, title, user, n , sec in sorted(rows):
        lines.append(f"| [#{num}](https://github.com/{REPO}/issues/{num}) "
                     f"| {title} | {user} | {n} | {fmt_hours(sec)} |")

    by_user = defaultdict(float)
    for *_, user, _n, sec in rows:
        by_user[user] += sec
    lines += ["", "## 作業者合計", "",
              "| 作業者 | 合計時間 |", "| --- | --- |"]
    lines += [f"| {u} | {fmt_hours(s)} |" for u, s in sorted(by_user.items())]

    if warnings:
        lines += ["", "## ⚠️ 打刻の不整合", ""]
        lines += [f"- {w}" for w in warnings]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT} ({len(rows)} rows, {len(warnings)} warnings)")

if __name__ == "__main__":
    main()
