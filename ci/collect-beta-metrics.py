#!/usr/bin/env python3
"""
Daily beta metrics collector. Run once per day during dogfood period.

Output: docs/beta-program/daily/YYYY-MM-DD.md
"""
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DAILY_DIR = ROOT / "docs" / "beta-program" / "daily"


def collect_from_gh() -> dict:
    """Pull beta feedback issues from GitHub."""
    try:
        result = subprocess.check_output(
            [
                "gh", "issue", "list",
                "--label", "beta-feedback",
                "--json", "number,title,labels,createdAt",
                "--limit", "200",
            ],
            text=True,
        )
        return json.loads(result)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []


def main():
    today = datetime.now().strftime("%Y-%m-%d")
    DAILY_DIR.mkdir(parents=True, exist_ok=True)
    out = DAILY_DIR / f"{today}.md"

    issues = collect_from_gh()

    today_issues = [i for i in issues if i.get("createdAt", "").startswith(today)]
    misclassified = sum(
        1 for i in today_issues
        if any(l["name"] == "misclassified" for l in i.get("labels", []))
    )
    p0 = sum(
        1 for i in today_issues
        if any(l["name"] == "p0" for l in i.get("labels", []))
    )

    n_today = len(today_issues)
    n_total = len(issues)

    report = f"""# Beta Daily Report - {today}

## Summary
- Today feedback entries: {n_today}
- Cumulative feedback: {n_total}
- Today misclassifications: {misclassified}
- Today P0 incidents: {p0}
- Misclassification rate (today): {misclassified / max(n_today, 1) * 100:.1f}%
- Misclassification rate (cumulative): {misclassified / max(n_total, 1) * 100:.1f}%

## Notes
<!-- Add qualitative observations here -->

"""
    out.write_text(report)
    print(f"OK: Daily report saved to {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
