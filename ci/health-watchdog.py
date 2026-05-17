#!/usr/bin/env python3
"""
Background health check watchdog — runs beta-health-check daily.
No admin rights needed. Keep this running in a terminal or via startup.

Usage: python ci/health-watchdog.py
"""
import subprocess
import time
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HEALTH_CHECK = ROOT / "ci" / "beta-health-check.py"
LOG_DIR = ROOT / "docs" / "beta-program" / "health-checks"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG_DIR / "watchdog.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


def run_check():
    today = datetime.now().strftime("%Y-%m-%d")
    log(f"Running beta-health-check for {today}")
    try:
        result = subprocess.run(
            [sys.executable, str(HEALTH_CHECK), "--date", today],
            capture_output=True, text=True, timeout=120,
        )
        for line in result.stdout.strip().split("\n"):
            log(f"  {line}")
        if result.returncode == 2:
            log("RED LINE TRIGGERED — check reports immediately!")
        elif result.returncode == 1:
            log("WARNING — review health-check output")
    except Exception as e:
        log(f"ERROR: {e}")


def main():
    log("Health watchdog started.")

    # Run immediately on startup
    run_check()

    last_run = datetime.now().strftime("%Y-%m-%d")

    while True:
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")

        # Run at 09:00 each day (skip if already ran today)
        if now.hour == 9 and last_run != today_str:
            run_check()
            last_run = today_str

        time.sleep(60)


if __name__ == "__main__":
    main()
