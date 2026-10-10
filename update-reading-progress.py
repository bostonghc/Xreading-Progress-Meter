#!/usr/bin/env python3
"""
Refresh the reading-progress page from a fresh Xreading export.

USAGE
    python3 update-reading-progress.py "Class Reading Data.csv"
    python3 update-reading-progress.py export.csv --week 9 --date "June 21, 2026"

What it does
    Reads the CSV, recomputes the class snapshot (totals, how many students have
    reached each point tier, how many are still on zero, the cohort read speed),
    and rewrites ONLY the block between /* GEN:START */ and /* GEN:END */ in the
    HTML file. Everything else in the page is left untouched.

Edit nothing in the HTML by hand except the "SET ONCE" block (term start/end dates, tiers).
"""

import argparse, csv, datetime as dt, json, re, sys
from pathlib import Path

# ---- set these once to match the page + your term -------------------------
HTML_FILE  = "reading-progress.html"
THRESHOLDS = [10000, 25000, 40000]   # must match the TIERS words in the HTML
TERM_START = dt.date(2026, 9, 14)    # Monday of week 1 — used to auto-fill WEEK_NOW
EXCLUDE_IF = ["Demo Class"]          # drop test/instructor rows whose Classes contains any of these
# ---------------------------------------------------------------------------


def words(row):
    try:
        return int(row["Words Read"].replace(",", "").strip())
    except (ValueError, KeyError, AttributeError):
        return 0

def speed(row):
    try:
        return float(row["Read Speed (Word/Min)"].replace(",", "").strip())
    except (ValueError, KeyError, AttributeError):
        return 0.0


def class_label(row):
    """Collapse repeated class names from the Xreading export."""
    labels, seen = [], set()
    for part in (row.get("Classes") or "").split(","):
        label = " ".join(part.split())
        key = label.casefold()
        if label and key not in seen:
            seen.add(key)
            labels.append(label)
    return ", ".join(labels) or "(no class)"


def main():
    ap = argparse.ArgumentParser(description="Refresh reading-progress.html from an Xreading CSV.")
    ap.add_argument("csv", help="path to the Xreading export")
    ap.add_argument("--html", default=HTML_FILE, help=f"page to update (default: {HTML_FILE})")
    ap.add_argument("--week", type=int, help="override week number (default: computed from TERM_START)")
    ap.add_argument("--date", help='override snapshot date label (default: today, e.g. "June 21, 2026")')
    args = ap.parse_args()

    csv_path = Path(args.csv)
    html_path = Path(args.html)
    for p in (csv_path, html_path):
        if not p.exists():
            sys.exit(f"error: not found: {p}")

    with csv_path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    # drop test/instructor rows
    kept = [r for r in rows if not any(x in (r.get("Classes") or "") for x in EXCLUDE_IF)]
    dropped = len(rows) - len(kept)

    def stats_for(group):
        return {
            "total":   len(group),
            "reached": {t: sum(1 for r in group if words(r) >= t) for t in THRESHOLDS},
            "atZero":  sum(1 for r in group if words(r) == 0),
        }

    # Cohort first, then each normalized class label sorted alphabetically.
    by_class = {}
    for r in kept:
        cls = class_label(r)
        by_class.setdefault(cls, []).append(r)
    groups = {"All classes": stats_for(kept)}
    for cls in sorted(by_class):
        groups[cls] = stats_for(by_class[cls])

    cohort = groups["All classes"]

    speeds  = [speed(r) for r in kept if words(r) > 0 and speed(r) > 0]
    wpm     = round(sum(speeds) / len(speeds)) if speeds else 95

    today = dt.date.today()
    snapshot = args.date or today.strftime("%B %-d, %Y")
    week = args.week if args.week is not None else max(1, (today - TERM_START).days // 7 + 1)

    def group_literal(g):
        pairs = ",".join(f"{t}:{g['reached'][t]}" for t in THRESHOLDS)
        return f"{{ total:{g['total']}, reached:{{{pairs}}}, atZero:{g['atZero']} }}"

    group_lines = ",\n".join(
        f"  {json.dumps(k, ensure_ascii=False)}: {group_literal(v)}" for k, v in groups.items()
    )
    block = (
        "/* GEN:START */\n"
        f'var SNAPSHOT = "{snapshot}";   // date of the export\n'
        f"var WEEK_NOW = {week};                // weeks elapsed\n"
        f"var READ_WPM = {wpm};               // cohort avg read speed (words/min)\n"
        "var GROUPS = {\n"
        f"{group_lines}\n"
        "};\n"
        "/* GEN:END */"
    )

    html = html_path.read_text(encoding="utf-8")
    new_html, n = re.subn(r"/\* GEN:START \*/.*?/\* GEN:END \*/", block, html, count=1, flags=re.DOTALL)
    if n == 0:
        sys.exit("error: could not find the /* GEN:START */ ... /* GEN:END */ block in the HTML.")
    html_path.write_text(new_html, encoding="utf-8")

    print(f"Updated {html_path}")
    print(f"  snapshot {snapshot}  ·  week {week}  ·  {cohort['total']} students"
          + (f"  ({dropped} test rows dropped)" if dropped else ""))
    for t in THRESHOLDS:
        print(f"  >= {t:>6,}: {cohort['reached'][t]:3d} students")
    print(f"  on zero : {cohort['atZero']:3d}   ·   cohort read speed {wpm} wpm")
    print(f"  classes : {len(groups) - 1}  ({', '.join(k for k in groups if k != 'All classes')})")


if __name__ == "__main__":
    main()
