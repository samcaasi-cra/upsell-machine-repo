#!/usr/bin/env python
"""Demo safety net: snapshot a known-good data state and restore it in seconds.

Live research is non-deterministic and rate-limited, so a demo can't rely on
re-running it. Capture a state you're happy with, then restore instantly if
something goes sideways mid-presentation.

    python demo.py snapshot        # save the current data/ as the demo baseline
    python demo.py restore         # put that baseline back
    python demo.py status          # what's in the live state and the baseline
    python demo.py restore --fresh # baseline, minus caches -- to demo research live

Only touches backend/data/. Never touches .env or any credentials.
"""

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
SNAPSHOT_DIR = DATA_DIR / "_demo_snapshot"
MANIFEST = SNAPSHOT_DIR / "_manifest.json"

# Everything the app persists, relative to data/.
TRACKED_FILES = ["customers.json", "research_schedule.json"]
TRACKED_DIRS = ["news_events", "decision_makers", "usage_individuals"]

# Caches that `--fresh` clears, so you can demo research populating from empty.
CACHE_DIRS = ["news_events", "decision_makers"]


def _counts(root: Path) -> dict:
    if not root.exists():
        return {}
    out = {}
    for name in TRACKED_FILES:
        if (root / name).exists():
            out[name] = 1
    for name in TRACKED_DIRS:
        d = root / name
        out[name] = len(list(d.glob("*.json"))) if d.exists() else 0
    return out


def _describe(root: Path, label: str) -> None:
    counts = _counts(root)
    if not counts:
        print(f"  {label}: (nothing)")
        return
    customers = "-"
    cfile = root / "customers.json"
    if cfile.exists():
        try:
            customers = str(len(json.loads(cfile.read_text(encoding="utf-8"))))
        except (json.JSONDecodeError, OSError):
            customers = "unreadable"
    print(f"  {label}:")
    print(f"    customers           {customers}")
    print(f"    news_events         {counts.get('news_events', 0)} cached")
    print(f"    decision_makers     {counts.get('decision_makers', 0)} cached")
    print(f"    usage_individuals   {counts.get('usage_individuals', 0)} tracked")


def snapshot() -> int:
    if not DATA_DIR.exists():
        print("No data/ directory yet — start the backend at least once first.")
        return 1

    if SNAPSHOT_DIR.exists():
        shutil.rmtree(SNAPSHOT_DIR)
    SNAPSHOT_DIR.mkdir(parents=True)

    for name in TRACKED_FILES:
        src = DATA_DIR / name
        if src.exists():
            shutil.copy2(src, SNAPSHOT_DIR / name)
    for name in TRACKED_DIRS:
        src = DATA_DIR / name
        if src.exists():
            shutil.copytree(src, SNAPSHOT_DIR / name)

    MANIFEST.write_text(
        json.dumps({"created_at": datetime.now(timezone.utc).isoformat(), "counts": _counts(DATA_DIR)}, indent=2),
        encoding="utf-8",
    )
    print("Snapshot saved.")
    _describe(SNAPSHOT_DIR, "baseline")
    return 0


def restore(fresh: bool = False) -> int:
    if not SNAPSHOT_DIR.exists():
        print("No snapshot found. Run `python demo.py snapshot` while the data looks good.")
        return 1

    for name in TRACKED_FILES:
        target = DATA_DIR / name
        src = SNAPSHOT_DIR / name
        if src.exists():
            shutil.copy2(src, target)
        elif target.exists():
            target.unlink()

    for name in TRACKED_DIRS:
        target = DATA_DIR / name
        if target.exists():
            shutil.rmtree(target)
        src = SNAPSHOT_DIR / name
        if fresh and name in CACHE_DIRS:
            target.mkdir(parents=True, exist_ok=True)  # deliberately empty
        elif src.exists():
            shutil.copytree(src, target)
        else:
            target.mkdir(parents=True, exist_ok=True)

    if fresh:
        # Let the scheduler consider today's run due again.
        sched = DATA_DIR / "research_schedule.json"
        if sched.exists():
            sched.unlink()
        print("Restored baseline with research caches cleared — ready to demo research live.")
    else:
        print("Restored baseline.")

    _describe(DATA_DIR, "live state")
    print("\nRestart the backend so it picks up the restored files.")
    return 0


def status() -> int:
    print("Data state")
    _describe(DATA_DIR, "live state")
    if MANIFEST.exists():
        try:
            created = json.loads(MANIFEST.read_text(encoding="utf-8")).get("created_at", "unknown")
            print(f"\n  baseline taken: {created}")
        except (json.JSONDecodeError, OSError):
            pass
    _describe(SNAPSHOT_DIR, "baseline")
    if not SNAPSHOT_DIR.exists():
        print("\n  No baseline yet — run `python demo.py snapshot`.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("snapshot", help="save the current data/ as the demo baseline")
    p_restore = sub.add_parser("restore", help="restore the demo baseline")
    p_restore.add_argument(
        "--fresh",
        action="store_true",
        help="restore customers but clear research caches, to demo research populating live",
    )
    sub.add_parser("status", help="show the live state and the baseline")

    args = parser.parse_args()
    if args.command == "snapshot":
        return snapshot()
    if args.command == "restore":
        return restore(fresh=args.fresh)
    if args.command == "status":
        return status()
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
