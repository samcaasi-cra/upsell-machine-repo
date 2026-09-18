"""Cyber Rescue's own customer tracker: who hasn't been called, and who is overdue.

Internal view, not a customer-facing one. It answers four questions a CR account lead
asks every week:

  * which customers have we never had a call with?
  * which meetings are coming up?
  * who has gone longest without a meeting?
  * who has gone longest without a planned next action?

The source is the team's working spreadsheet, which holds client names, owners and
meeting history. Two rules follow from that:

  * **The file never enters the repository.** It is read from `backend/private/`, which
    is gitignored, or from wherever CR_TRACKER_PATH points. Nothing derived from it is
    written back to disk -- the results are computed per request and cached in memory,
    so there is no second copy to leak.
  * **Contact names and email addresses are not read at all.** The spreadsheet has
    columns for both. This module skips them, because none of the four questions needs
    them, and data you never load is data you cannot spill.

openpyxl cannot open this particular workbook -- it carries a pivot cache whose XML
fails a strict parse -- so the two sheets we need are read straight from the xlsx zip.
"""

import os
import re
import zipfile
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

from .. import config

# Sheets we read. Everything else in the workbook (pivot tables, summaries, the
# 72-column tracker) is ignored.
_TRACKER_SHEET = "3 - Customer Tracker for 2023"
_EVENTS_SHEET = "All_Calendar_Event"

# Columns we deliberately never read, by header text.
_SKIP_HEADER_PREFIXES = ("names of all contacts", "emails of all contacts")

_EXCEL_EPOCH = date(1899, 12, 30)  # Excel's day 0, accounting for its 1900 leap-year bug

_cache: dict = {}
_cache_stamp: Optional[float] = None


def tracker_path() -> Path:
    override = os.getenv("CR_TRACKER_PATH")
    if override:
        return Path(override)
    return config.BACKEND_DIR / "private" / "cr_tracker.xlsx"


def is_configured() -> bool:
    return tracker_path().exists()


# -- xlsx reading ---------------------------------------------------------------


def _col_letters(ref: str) -> str:
    return "".join(ch for ch in ref if ch.isalpha())


def _shared_strings(z: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in z.namelist():
        return []
    xml = z.read("xl/sharedStrings.xml").decode("utf8", "ignore")
    return [re.sub(r"<[^>]+>", "", si) for si in re.findall(r"<si>(.*?)</si>", xml, re.S)]


def _sheet_part(z: zipfile.ZipFile, wanted: str) -> Optional[str]:
    wb = z.read("xl/workbook.xml").decode("utf8", "ignore")
    rels = z.read("xl/_rels/workbook.xml.rels").decode("utf8", "ignore")
    rmap = dict(re.findall(r'Id="([^"]+)"[^>]*Target="([^"]+)"', rels))
    for name, rid in re.findall(r'<sheet[^>]*name="([^"]+)"[^>]*r:id="([^"]+)"', wb):
        if name != wanted:
            continue
        target = rmap.get(rid, "")
        for candidate in (target, "xl/" + target.lstrip("/"), "xl/" + target.replace("xl/", "", 1)):
            if candidate in z.namelist():
                return candidate
    return None


def _rows(z: zipfile.ZipFile, part: str, shared: list[str], limit: Optional[int] = None):
    """Yield each row as {column letter: value}. Cells carry their own column
    reference, so blank cells can't shift the row out of alignment."""
    xml = z.read(part).decode("utf8", "ignore")
    for n, row in enumerate(re.findall(r"<row[^>]*>(.*?)</row>", xml, re.S)):
        if limit and n >= limit:
            return
        out: dict[str, str] = {}
        for cell in re.findall(r"<c[^>]*/>|<c[^>]*>.*?</c>", row, re.S):
            ref = re.search(r'r="([A-Z]+\d+)"', cell)
            if not ref:
                continue
            t = re.search(r't="([^"]+)"', cell)
            v = re.search(r"<v>(.*?)</v>", cell, re.S)
            if v is None:
                inline = re.search(r"<is>(.*?)</is>", cell, re.S)
                value = re.sub(r"<[^>]+>", "", inline.group(1)) if inline else ""
            elif t and t.group(1) == "s":
                i = int(v.group(1))
                value = shared[i] if i < len(shared) else ""
            else:
                value = v.group(1)
            out[_col_letters(ref.group(1))] = value.strip()
        yield out


def _excel_date(value: str) -> Optional[date]:
    try:
        serial = float(value)
    except (TypeError, ValueError):
        return None
    if serial <= 0:
        return None
    return _EXCEL_EPOCH + timedelta(days=int(serial))


def _norm(name: str) -> str:
    """A firm name reduced to something matchable against a free-text meeting title."""
    n = name.lower()
    n = re.sub(r"[^a-z0-9 ]+", " ", n)
    for suffix in (" group", " ltd", " limited", " plc", " inc", " llc", " uk", " holdings", " the "):
        n = n.replace(suffix, " ")
    return " ".join(n.split())


# -- building the view ----------------------------------------------------------


def _header_map(rows: list[dict]) -> dict:
    """Column letter -> lowercased header text, minus the contact columns."""
    if not rows:
        return {}
    return {
        col: (val or "").strip().lower()
        for col, val in rows[0].items()
        if val and not (val or "").strip().lower().startswith(_SKIP_HEADER_PREFIXES)
    }


def _find_col(header: dict, prefix: str) -> Optional[str]:
    """Headers in this workbook are long instructions, so match their opening words."""
    for col, text in header.items():
        if text.startswith(prefix):
            return col
    return None


def build(force: bool = False) -> dict:
    """Read the tracker and answer the four questions. Cached until the file changes."""
    global _cache, _cache_stamp
    path = tracker_path()
    if not path.exists():
        return {
            "configured": False,
            "detail": (
                "No tracker found. Put the spreadsheet at backend/private/cr_tracker.xlsx "
                "(that folder is gitignored) or set CR_TRACKER_PATH."
            ),
        }

    stamp = path.stat().st_mtime
    if _cache and _cache_stamp == stamp and not force:
        return _cache

    today = date.today()
    firms: list[dict] = []
    events: list[dict] = []

    with zipfile.ZipFile(path) as z:
        shared = _shared_strings(z)

        part = _sheet_part(z, _TRACKER_SHEET)
        if part:
            rows = list(_rows(z, part, shared))
            header = _header_map(rows)
            col = {
                "firm": _find_col(header, "firm"),
                "website": _find_col(header, "website"),
                "relationship": _find_col(header, "relationship"),
                "renewal": _find_col(header, "date of renewal"),
                "next_action": _find_col(header, "planned next actions"),
                "status": _find_col(header, "renewal status"),
                "owner": _find_col(header, "cr owner of relationship"),
                "last_meeting": _find_col(header, "previous webex"),
            }
            for row in rows[1:]:
                name = row.get(col["firm"] or "", "")
                if not name:
                    continue
                last = _excel_date(row.get(col["last_meeting"] or "", ""))
                firms.append(
                    {
                        "firm": name,
                        "website": row.get(col["website"] or "", ""),
                        "relationship": row.get(col["relationship"] or "", ""),
                        "status": row.get(col["status"] or "", ""),
                        "owner": row.get(col["owner"] or "", ""),
                        "next_action": row.get(col["next_action"] or "", ""),
                        "renewal_date": str(_excel_date(row.get(col["renewal"] or "", "")) or ""),
                        "last_meeting": str(last or ""),
                        "days_since": (today - last).days if last else None,
                    }
                )

        part = _sheet_part(z, _EVENTS_SHEET)
        if part:
            rows = list(_rows(z, part, shared))
            header = _header_map(rows)
            title_col = _find_col(header, "event title")
            start_col = _find_col(header, "start time")
            for row in rows[1:]:
                title = row.get(title_col or "", "")
                when = _excel_date(row.get(start_col or "", ""))
                if title and when and when >= today:
                    events.append({"title": title, "date": when})

    # The calendar export holds titles, not firm ids, so an upcoming meeting is tied to
    # a firm by its name appearing in the title. Imprecise, and labelled as such.
    upcoming = []
    for firm in firms:
        key = _norm(firm["firm"])
        if len(key) < 4:
            continue
        hits = sorted(e["date"] for e in events if key in _norm(e["title"]))
        if hits:
            upcoming.append({**firm, "next_meeting": str(hits[0])})
    upcoming.sort(key=lambda r: r["next_meeting"])
    booked = {r["firm"] for r in upcoming}

    never_met = [f for f in firms if not f["last_meeting"] and f["firm"] not in booked]
    longest_gap = sorted(
        (f for f in firms if f["days_since"] is not None),
        key=lambda f: -f["days_since"],
    )
    no_next_action = [f for f in firms if not f["next_action"]]

    _cache = {
        "configured": True,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source": path.name,
        "counts": {
            "firms": len(firms),
            "with_meeting_history": sum(1 for f in firms if f["last_meeting"]),
            "upcoming_events": len(events),
        },
        "caveats": [
            "Upcoming meetings are matched to a firm by its name appearing in the calendar entry's title, so a differently-titled meeting will be missed.",
            "'No meeting recorded' means the tracker's Previous Webex column is empty and no upcoming meeting was matched -- not proof that no call ever happened.",
        ],
        "never_met": never_met[:60],
        "never_met_total": len(never_met),
        "upcoming": upcoming[:40],
        "upcoming_total": len(upcoming),
        "longest_gap": longest_gap[:40],
        "longest_gap_total": len(longest_gap),
        "no_next_action": no_next_action[:60],
        "no_next_action_total": len(no_next_action),
    }
    _cache_stamp = stamp
    return _cache
