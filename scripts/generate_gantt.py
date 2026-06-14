#!/usr/bin/env python3
"""Projects v2の計画/予定フィールド + issue依存関係 + 打刻実績から
予実比較ガントチャート（PlantUML）を生成する。"""
import json
import subprocess
from pathlib import Path

OWNER, REPO_NAME = "harukikiya", "rp2040-temp-monitor"
PROJECT_NUMBER = 1      # gh project list で確認した番号に合わせる
OUT = Path("diagrams/generated/progress_gantt.puml")

QUERY = """
query($login: String!, $number: Int!) {
    user(login: $login) {
        projectV2(number: $number) {
            items(first: 100) {
                nodes {
                    content { ... on Issue {number title state } }
                    fieldValues(first: 20) {
                        nodes {
                            ... on ProjectV2FieldDateValue {
                                date
                                field { ... on ProjectV2FieldCommon { name } }
                            }
                        }
                    }
                }
            }
        }
    }
}
"""

def graphql(query: str, **vars_) -> dict:
    cmd = ["gh", "api", "graphql", "-f", f"query={query}"]
    for k, v in vars_.items():
        flag = "-F" if isinstance(v, int) else "-f"
        cmd += [flag, f"{k}={v}"]
    r = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(r.stdout)

def blocked_by(issue_number: int) -> list[int]:
    r = subprocess.run(
        ["gh", "api",
         f"repos/{OWNER}/{REPO_NAME}/issues/{issue_number}/dependencies/blocked_by",
         "--jq", "[.[].number]"],
         capture_output=True, text=True,
    )
    return json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else []

def main() -> None:
    data = graphql(QUERY, login=OWNER, number=PROJECT_NUMBER)
    items = data["data"]["user"]["projectV2"]["items"]["nodes"]

    tasks = []
    for it in items:
        c = it.get("content") or {}
        if "number" not in c:
            continue
        dates = {fv["field"]["name"]: fv["data"]
                 for fv in it["fieldValues"]["nodes"] if fv.get("date")}
        tasks.append({
            "num": c["number"], "title": c["title"], "state": c["state"],
            "plan": (dates.get("計画開始"), dates.get("計画終了")),
            "fcst": (dates.get("予定開始"), dates.get("予定終了")),
            "deps": blocked_by(c["number"]),
        })

    starts = [d for t in tasks for d in (*t["plan"], *t["fcst"]) if d]
    origin = min(starts) if starts else "2026-06-01"

    L = ["@startgantt", "projectscale weekly", f"Project starts {origin}", ""]
    for t in sorted(tasks, key=lambda t: t["fcst"][0] or t["plan"][0] or "9999"):
        name = f"#{t['num']} {t['title']}"
        ps, pe = t["plan"]
        fs, fe = t["fcst"]
        if ps and pe:       # 計画（ベースライン）バー: グレー
            L.append(f"[{name} （計画）] starts {ps} and ends {pe}")
            L.append(f"[{name} （計画）] is colored in LightGray")
        if fs and fe:       # 予定/実績バー: 状態で色分け
            L.append(f"[{name}] starts {fs} and ends {fe}")
            if t["state"] == "CLOSED":
                L.append(f"[{name}] is colored in MediumSeaGreen")
            elif pe and fe > pe:    # 計画終了より遅延
                L.append(f"[{name}] is colored in Tomato")
        for dep in t["deps"]:       # 依存矢印（純正Roadmapが描けない部分）
            dep_task = next((x for x in tasks if x["num"] == dep), None)
            if dep_task and fs:
                L.append(f"[{name}] starts at [#{dep} {dep_task['title']}]' s end")
        L.append("")
    L.append("@endgantt")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(L), encoding="utf-8")
    print(f"wrote {OUT} ({len(tasks)} tasks)")

if __name__ == "__main__":
    main()
