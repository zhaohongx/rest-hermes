#!/usr/bin/env python3
"""
Beta dogfood health check — daily automated inspection.

Usage:
  python ci/beta-health-check.py                 # Check today
  python ci/beta-health-check.py --date 2026-05-22  # Check specific date
  python ci/beta-health-check.py --window 7      # Cumulative from beta start

Exit codes:
  0 = healthy (green)
  1 = warning (yellow, needs attention)
  2 = red line (requires immediate response)
  3 = no data or script error
"""
import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# ============ Configuration ============

BETA_START = datetime(2026, 5, 16)
BETA_EVAL_DATE = datetime(2026, 5, 30)
BETA_HARD_DEADLINE = datetime(2026, 6, 15)

DOGFOOD_TEAM_SIZE = 1  # Replace with actual team size

ROOT = Path(__file__).resolve().parent.parent
DAILY_DIR = ROOT / "docs" / "beta-program" / "daily"
REPORT_DIR = ROOT / "docs" / "beta-program" / "health-checks"

# Staged thresholds (startup D3-D6 is 30% wider than D7 mid-term)
STAGE_THRESHOLDS = {
    "startup": {
        "min_daily_calls": 3,
        "max_misclass_rate": 0.20,
        "min_satisfaction": 3.0,
        "max_p0": 0,
        "max_ec_001_002_daily": 3,
    },
    "midterm": {
        "min_cumulative_calls": 20,
        "max_misclass_rate": 0.12,
        "min_satisfaction": 3.5,
        "max_p0": 0,
        "max_ec_001_002_cumulative": 4,
        "min_participation_rate": 0.60,
    },
    "evaluation": {
        "min_cumulative_calls": 50,
        "max_misclass_rate": 0.08,
        "min_satisfaction": 4.0,
        "max_p0": 0,
        "max_ec_001_002_cumulative": 5,
        "min_participation_rate": 0.75,
    },
}

RED_LINE = {
    "max_misclass_rate": 0.15,
    "min_satisfaction": 3.0,
    "max_p0": 1,
    "max_consecutive_zero_days": 2,
}


# ============ Data Collection ============

@dataclass
class DailyMetrics:
    date: str
    calls: int = 0
    feedbacks: int = 0
    misclassified: int = 0
    p0: int = 0
    ec_001: int = 0
    ec_002: int = 0
    satisfaction_sum: float = 0.0
    satisfaction_count: int = 0
    confidence_sum: float = 0.0
    confidence_count: int = 0
    unique_users: set = field(default_factory=set)

    @property
    def avg_satisfaction(self) -> Optional[float]:
        if self.satisfaction_count == 0:
            return None
        return self.satisfaction_sum / self.satisfaction_count

    @property
    def avg_confidence(self) -> Optional[float]:
        if self.confidence_count == 0:
            return None
        return self.confidence_sum / self.confidence_count

    @property
    def misclass_rate(self) -> Optional[float]:
        if self.feedbacks == 0:
            return None
        return self.misclassified / self.feedbacks


def fetch_issues_via_gh(start: datetime, end: datetime) -> list[dict]:
    """Pull beta-feedback issues from GitHub via gh CLI."""
    try:
        result = subprocess.run(
            ["gh", "issue", "list",
             "--label", "beta-feedback",
             "--state", "all",
             "--json", "number,title,body,labels,createdAt,author",
             "--limit", "500"],
            capture_output=True, text=True, check=True, timeout=30,
        )
        all_issues = json.loads(result.stdout)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return []

    filtered = []
    for i in all_issues:
        created = datetime.fromisoformat(
            i["createdAt"].replace("Z", "+00:00")
        ).replace(tzinfo=None)
        if start <= created <= end:
            filtered.append(i)
    return filtered


def parse_feedback_body(body: str) -> dict:
    """Extract structured fields from feedback template."""
    fields = {}
    m = re.search(r"satisfaction[:\s]+(\d+(?:\.\d+)?)", body, re.IGNORECASE)
    if m:
        fields["satisfaction"] = float(m.group(1))
    m = re.search(r"confidence[:\s]+(\d+(?:\.\d+)?)", body, re.IGNORECASE)
    if m:
        fields["confidence"] = float(m.group(1))
    return fields


def aggregate_daily(issues: list[dict]) -> dict[str, DailyMetrics]:
    """Aggregate issues by date."""
    by_date: dict[str, DailyMetrics] = {}
    for issue in issues:
        created = datetime.fromisoformat(
            issue["createdAt"].replace("Z", "+00:00")
        ).replace(tzinfo=None)
        date_key = created.strftime("%Y-%m-%d")
        if date_key not in by_date:
            by_date[date_key] = DailyMetrics(date=date_key)
        m = by_date[date_key]
        m.feedbacks += 1
        m.calls += 1
        label_names = {lab["name"] for lab in issue.get("labels", [])}
        if "misclassified" in label_names:
            m.misclassified += 1
        if "p0" in label_names:
            m.p0 += 1
        if "ec-001" in label_names:
            m.ec_001 += 1
        if "ec-002" in label_names:
            m.ec_002 += 1
        author = issue.get("author", {}).get("login", "unknown")
        m.unique_users.add(author)
        parsed = parse_feedback_body(issue.get("body", ""))
        if "satisfaction" in parsed:
            m.satisfaction_sum += parsed["satisfaction"]
            m.satisfaction_count += 1
        if "confidence" in parsed:
            m.confidence_sum += parsed["confidence"]
            m.confidence_count += 1
    return by_date


# ============ Health Assessment ============

def determine_stage(today: datetime) -> str:
    days = (today - BETA_START).days
    if days <= 6:
        return "startup"
    elif days <= 10:
        return "midterm"
    else:
        return "evaluation"


def check_health(by_date: dict[str, DailyMetrics], today: datetime) -> tuple[int, list[str]]:
    """Returns (exit_code, signals)."""
    signals = []
    stage = determine_stage(today)
    thresholds = STAGE_THRESHOLDS[stage]

    cum_calls = sum(m.calls for m in by_date.values())
    cum_feedbacks = sum(m.feedbacks for m in by_date.values())
    cum_misclass = sum(m.misclassified for m in by_date.values())
    cum_p0 = sum(m.p0 for m in by_date.values())
    cum_ec = sum(m.ec_001 + m.ec_002 for m in by_date.values())
    cum_users = set()
    for m in by_date.values():
        cum_users |= m.unique_users

    sat_sum = sum(m.satisfaction_sum for m in by_date.values())
    sat_cnt = sum(m.satisfaction_count for m in by_date.values())
    avg_sat = sat_sum / sat_cnt if sat_cnt else None

    cum_misclass_rate = cum_misclass / cum_feedbacks if cum_feedbacks else 0
    participation = len(cum_users) / DOGFOOD_TEAM_SIZE

    today_key = today.strftime("%Y-%m-%d")
    today_calls = by_date.get(today_key, DailyMetrics(date=today_key)).calls

    # === Red Line Checks ===
    red_hit = []
    if cum_p0 >= RED_LINE["max_p0"]:
        red_hit.append(
            f"RED: {cum_p0} P0 incidents (red line: 0)"
        )
    if avg_sat is not None and avg_sat < RED_LINE["min_satisfaction"]:
        red_hit.append(
            f"RED: avg satisfaction {avg_sat:.2f} (red line: >= {RED_LINE['min_satisfaction']})"
        )
    if cum_feedbacks >= 5 and cum_misclass_rate > RED_LINE["max_misclass_rate"]:
        red_hit.append(
            f"RED: misclass rate {cum_misclass_rate*100:.1f}% (red line: < {RED_LINE['max_misclass_rate']*100}%)"
        )

    # Consecutive zero-call days (startup phase)
    if stage == "startup":
        max_streak = 0
        zero_streak = 0
        current_date = BETA_START
        while current_date <= today:
            dk = current_date.strftime("%Y-%m-%d")
            if dk not in by_date or by_date[dk].calls == 0:
                zero_streak += 1
                max_streak = max(max_streak, zero_streak)
            else:
                zero_streak = 0
            current_date += timedelta(days=1)
        if max_streak >= RED_LINE["max_consecutive_zero_days"]:
            red_hit.append(
                f"RED: {max_streak} consecutive zero-call days (red line: < {RED_LINE['max_consecutive_zero_days']})"
            )

    # === Warning Checks ===
    yellow_hit = []
    if stage == "startup":
        if today_calls < thresholds["min_daily_calls"]:
            yellow_hit.append(
                f"YELLOW: today calls {today_calls} (warn: >= {thresholds['min_daily_calls']})"
            )
        if cum_feedbacks >= 3 and cum_misclass_rate > thresholds["max_misclass_rate"]:
            yellow_hit.append(
                f"YELLOW: misclass {cum_misclass_rate*100:.1f}% (warn: < {thresholds['max_misclass_rate']*100}%)"
            )
    else:
        if cum_calls < thresholds["min_cumulative_calls"]:
            yellow_hit.append(
                f"YELLOW: cumulative calls {cum_calls} (warn: >= {thresholds['min_cumulative_calls']})"
            )
        if cum_misclass_rate > thresholds["max_misclass_rate"]:
            yellow_hit.append(
                f"YELLOW: misclass {cum_misclass_rate*100:.1f}% (warn: < {thresholds['max_misclass_rate']*100}%)"
            )
        if avg_sat is not None and avg_sat < thresholds["min_satisfaction"]:
            yellow_hit.append(
                f"YELLOW: satisfaction {avg_sat:.2f} (warn: >= {thresholds['min_satisfaction']})"
            )
        if "min_participation_rate" in thresholds and participation < thresholds["min_participation_rate"]:
            yellow_hit.append(
                f"YELLOW: participation {participation*100:.0f}% (warn: >= {thresholds['min_participation_rate']*100}%)"
            )

    # === Summary ===
    day_n = (today - BETA_START).days
    signals.append(f"Beta Health Check - {today.strftime('%Y-%m-%d')} (D{day_n}, stage={stage})")
    signals.append(f"  Cumulative calls: {cum_calls} | feedbacks: {cum_feedbacks} | users: {len(cum_users)}/{DOGFOOD_TEAM_SIZE}")
    signals.append(f"  Misclass rate: {cum_misclass_rate*100:.1f}% | P0: {cum_p0} | EC-001/002: {cum_ec}")
    if avg_sat is not None:
        signals.append(f"  Avg satisfaction: {avg_sat:.2f} (n={sat_cnt})")
    signals.append(f"  Participation: {participation*100:.0f}%")
    signals.append("")

    if red_hit:
        signals.append("=== RED LINE ALERT ===")
        signals.extend(red_hit)
        signals.append("-> Action: trigger incident response, see promotion-checklist.md rollback flow")
        return 2, signals

    if yellow_hit:
        signals.append("=== YELLOW WARNING ===")
        signals.extend(yellow_hit)
        signals.append("-> Action: see mid-term-check-sop.md intervention playbook")
        return 1, signals

    signals.append("=== GREEN: Healthy ===")
    signals.append("-> Action: continue as planned")
    return 0, signals


# ============ Report Generation ============

def save_report(signals: list[str], today: datetime, exit_code: int):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    status = {0: "green", 1: "yellow", 2: "red"}[exit_code]
    out = REPORT_DIR / f"{today.strftime('%Y-%m-%d')}-{status}.md"
    out.write_text("\n".join(signals) + "\n", encoding="utf-8")
    print(f"\nReport saved: {out.relative_to(ROOT)}")


# ============ Main ============

def main():
    parser = argparse.ArgumentParser(description="Beta dogfood health check")
    parser.add_argument("--date", type=str, help="Check date YYYY-MM-DD (default: today)")
    parser.add_argument("--window", type=int, help="Cumulative window in days (default: from beta start)")
    parser.add_argument("--quiet", action="store_true", help="Only output alerts")
    args = parser.parse_args()

    today = datetime.strptime(args.date, "%Y-%m-%d") if args.date else datetime.now()
    start = BETA_START if args.window is None else today - timedelta(days=args.window)

    issues = fetch_issues_via_gh(start, today + timedelta(days=1))

    if not issues:
        print("WARNING: No feedback data. Possible: (1) empty issue tracker (2) gh CLI not configured")
        print("This is expected on D2/D3 before feedback starts flowing.")
        return 3

    by_date = aggregate_daily(issues)
    exit_code, signals = check_health(by_date, today)

    output = "\n".join(signals)
    if not args.quiet or exit_code != 0:
        print(output)

    save_report(signals, today, exit_code)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
