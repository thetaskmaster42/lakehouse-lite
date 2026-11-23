#!/usr/bin/env python3
"""Daily tracker status for notes/tracker.md.

Usage:
  scripts/progress.py today            # today's open items + overdue items
  scripts/progress.py status           # per-week and overall progress
  scripts/progress.py today --date 2026-11-25   # pretend it's another day
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

TRACKER = Path(__file__).resolve().parent.parent / "notes" / "tracker.md"
START, END = dt.date(2026, 11, 23), dt.date(2026, 12, 18)

DAY_RE = re.compile(r"^## (Day \d+) — (\d{4}-\d{2}-\d{2}) (.*)$")
WEEK_RE = re.compile(r"^# (Week \d+.*|Buffer.*|Playbooks run.*|Readiness.*)$")
BOX_RE = re.compile(r"^- \[( |x|X)\] (.*)$")


def parse():
    weeks, days = [], []
    week = day = None
    for line in TRACKER.read_text().splitlines():
        if m := WEEK_RE.match(line):
            week = {"name": m.group(1), "boxes": []}
            weeks.append(week)
            day = None
        elif m := DAY_RE.match(line):
            day = {"name": m.group(1), "date": dt.date.fromisoformat(m.group(2)),
                   "title": m.group(3), "boxes": []}
            days.append(day)
        elif m := BOX_RE.match(line):
            box = (m.group(1).lower() == "x", m.group(2))
            if week is not None:
                week["boxes"].append(box)
            if day is not None:
                day["boxes"].append(box)
    return weeks, days


def bar(done, total, width=24):
    filled = round(width * done / total) if total else 0
    return f"[{'#' * filled}{'.' * (width - filled)}] {done}/{total} ({100 * done // max(total, 1)}%)"


def cmd_status(today):
    weeks, days = parse()
    allb = [b for w in weeks for b in w["boxes"]]
    print(f"Interview refresher — {today:%a %b %d}  ·  "
          f"{max((END - today).days, 0)} study days left (ends Fri Dec 18)\n")
    for w in weeks:
        if w["boxes"]:
            d = sum(b[0] for b in w["boxes"])
            print(f"  {w['name'][:44]:<44} {bar(d, len(w['boxes']))}")
    print(f"\n  {'OVERALL':<44} {bar(sum(b[0] for b in allb), len(allb))}")

    past = [d for d in days if d["date"] < today]
    expected = sum(len(d["boxes"]) for d in past)
    done_past = sum(b[0] for d in past for b in d["boxes"])
    if expected:
        behind = expected - done_past
        print(f"\n  Schedule: {done_past}/{expected} items due before today are done"
              + (f" — {behind} behind" if behind else " — on track ✅"))
    specs = re.findall(r"\*\*(S\d+)\b", TRACKER.read_text())
    print(f"  Specs in plan: {len(set(specs))}  ·  Days: {len(days)}")


def cmd_today(today):
    _, days = parse()
    todays = [d for d in days if d["date"] == today]
    if today < START:
        print(f"Plan starts Mon Nov 23 ({(START - today).days} days away).")
    elif not todays:
        print(f"{today:%a %b %d}: no scheduled day (buffer/after plan). Run `make status`.")
    for d in todays:
        open_ = [t for ok, t in d["boxes"] if not ok]
        done = len(d["boxes"]) - len(open_)
        print(f"{d['name']} — {today:%b %d} · {d['title']}   {bar(done, len(d['boxes']))}\n")
        for t in open_:
            print(f"  [ ] {t}")
        if not open_:
            print("  All done for today 🎉")
    overdue = [(d, t) for d in days if d["date"] < today for ok, t in d["boxes"] if not ok]
    if overdue:
        print(f"\nOverdue ({len(overdue)}):")
        for d, t in overdue:
            print(f"  [ ] {d['name']} ({d['date']:%b %d}): {t}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=["today", "status"], nargs="?", default="today")
    p.add_argument("--date", type=dt.date.fromisoformat, default=dt.date.today())
    a = p.parse_args()
    {"today": cmd_today, "status": cmd_status}[a.cmd](a.date)


if __name__ == "__main__":
    sys.exit(main())
