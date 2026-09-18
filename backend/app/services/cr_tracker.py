"""Cyber Rescue's own customer tracker: who hasn't been called, and who is overdue.

Internal view, not a customer-facing one. It answers four questions a CR account lead
asks every week:

  * which customers have we never had a call with?
  * which meetings are coming up?
  * who has gone longest without a meeting?
  * who has gone longest without a planned next action?

The source is the team's working spreadsheet, which holds client names, owners and
meeting history -- either a local export, or the live Google Sheet itself. Rules follow
from that either way:

  * **Nothing derived from it is written to disk.** Local mode reads from
    `backend/private/`, which is gitignored, or from wherever CR_TRACKER_PATH points.
    Live mode holds the fetched values in memory only. Either way results are cached
    in process, not as a second copy on disk.
  * **Contact names and email addresses are not read at all.** The spreadsheet has
    columns for both. This module skips them, because none of the four questions needs
    them, and data you never load is data you cannot spill.

Live mode (set CR_TRACKER_SHEET_ID) reads the sheet straight over the Sheets API using a
service account, so it's never more than _LIVE_CACHE_TTL_SECONDS stale. Local mode falls
back to parsing the xlsx zip directly -- openpyxl can't open this particular workbook (a
pivot cache whose XML fails a strict parse) -- to get row values in the same shape the
Sheets API already returns them in, so everything downstream of "get rows" is shared by
both paths.
"""

import json
import os
import re
import time
import zipfile
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

import requests

from .. import config

# Sheets we read. Everything else in the workbook (pivot tables, summaries, the
# 72-column tracker) is ignored.
_TRACKER_SHEET = "3 - Customer Tracker for 2023"
_EVENTS_SHEET = "All_Calendar_Event"

# Columns we deliberately never read, by header text.
_SKIP_HEADER_PREFIXES = ("names of all contacts", "emails of all contacts")

_EXCEL_EPOCH = date(1899, 12, 30)  # Excel's day 0, accounting for its 1900 leap-year bug
_LIVE_CACHE_TTL_SECONDS = 300

_cache: dict = {}
_cache_stamp: Optional[float] = None


def tracker_path() -> Path:
    override = os.getenv("CR_TRACKER_PATH")
    if override:
        return Path(override)
    return config.BACKEND_DIR / "private" / "cr_tracker.xlsx"


def sheet_id() -> Optional[str]:
    return os.getenv("CR_TRACKER_SHEET_ID") or None


def is_configured() -> bool:
    return bool(sheet_id()) or tracker_path().exists()


# -- Google Sheets reading (live mode) -------------------------------------------


def _google_credentials():
    from google.oauth2 import service_account

    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    inline = os.getenv("CR_TRACKER_GOOGLE_CREDENTIALS_JSON")
    if inline:
        return service_account.Credentials.from_service_account_info(json.loads(inline), scopes=scopes)
    key_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if key_path:
        return service_account.Credentials.from_service_account_file(key_path, scopes=scopes)
    raise RuntimeError(
        "CR_TRACKER_SHEET_ID is set but no service-account credentials were found. Set "
        "GOOGLE_APPLICATION_CREDENTIALS to the key file's path (recommended: drop it in "
        "backend/private/, which is gitignored), or CR_TRACKER_GOOGLE_CREDENTIALS_JSON to "
        "the key's contents directly, for deployments where a file path isn't convenient. "
        "The service account's email also needs Viewer access on the sheet itself."
    )


def _fetch_google_sheet_values(sid: str, sheet_names: list[str]) -> dict[str, list[list]]:
    """One batched call for every tab we need. UNFORMATTED_VALUE + SERIAL_NUMBER keeps
    dates as Excel-style serials, so `_excel_date` works unchanged for both this and
    the local-file path -- everything past this function is shared code."""
    from google.auth.transport.requests import Request

    creds = _google_credentials()
    creds.refresh(Request())
    resp = requests.get(
        f"https://sheets.googleapis.com/v4/spreadsheets/{sid}/values:batchGet",
        params=[("ranges", name) for name in sheet_names]
        + [("valueRenderOption", "UNFORMATTED_VALUE"), ("dateTimeRenderOption", "SERIAL_NUMBER")],
        headers={"Authorization": f"Bearer {creds.token}"},
        timeout=15,
    )
    resp.raise_for_status()
    out: dict[str, list[list]] = {}
    for vr in resp.json().get("valueRanges", []):
        out[vr["range"].split("!")[0].strip("'")] = vr.get("values", [])
    return out


def _index_to_col(i: int) -> str:
    """0-based column index -> spreadsheet letters (0->A, 26->AA, ...), matching what
    `_col_letters` produces from the local xlsx path."""
    letters = ""
    i += 1
    while i:
        i, rem = divmod(i - 1, 26)
        letters = chr(65 + rem) + letters
    return letters


def _rows_from_values(values: list[list]) -> list[dict]:
    """Sheets API rows (lists, trailing blanks dropped) -> the same {column letter:
    value} shape `_rows` yields from the xlsx zip, so header matching and column
    lookup don't need to know which source they're reading."""
    return [{_index_to_col(i): ("" if v is None else str(v).strip()) for i, v in enumerate(row)} for row in values]


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


_DATE_LINE = re.compile(r"(?m)^(?=\d{1,4}[/-]\d{1,2}[/-]\d{2,4})")


def _split_entries(text: str) -> list[str]:
    """The next-actions cell is a running log, newest entry first, each line starting
    with a date. Split it into individual entries instead of showing the whole blob."""
    if not text:
        return []
    parts = [p.strip() for p in _DATE_LINE.split(text) if p.strip()]
    return parts or [text.strip()]


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


def _read_source() -> tuple[list[dict], list[dict], str, float]:
    """Get both sheets' rows, whichever source is configured, plus a label for the UI
    and a cache-invalidation stamp (file mtime locally; a TTL bucket for live)."""
    sid = sheet_id()
    if sid:
        values = _fetch_google_sheet_values(sid, [_TRACKER_SHEET, _EVENTS_SHEET])
        tracker_rows = _rows_from_values(values.get(_TRACKER_SHEET, []))
        events_rows = _rows_from_values(values.get(_EVENTS_SHEET, []))
        source = "Google Sheet (live)"
        stamp = time.time() // _LIVE_CACHE_TTL_SECONDS
        return tracker_rows, events_rows, source, stamp

    path = tracker_path()
    with zipfile.ZipFile(path) as z:
        shared = _shared_strings(z)
        tracker_part = _sheet_part(z, _TRACKER_SHEET)
        events_part = _sheet_part(z, _EVENTS_SHEET)
        tracker_rows = list(_rows(z, tracker_part, shared)) if tracker_part else []
        events_rows = list(_rows(z, events_part, shared)) if events_part else []
    return tracker_rows, events_rows, path.name, path.stat().st_mtime


def build(force: bool = False) -> dict:
    """Read the tracker and answer the four questions. Cached until the source changes
    (local file) or for _LIVE_CACHE_TTL_SECONDS (live Google Sheet)."""
    global _cache, _cache_stamp
    if not is_configured():
        return {
            "configured": False,
            "detail": (
                "No tracker found. Put the spreadsheet at backend/private/cr_tracker.xlsx "
                "(that folder is gitignored), set CR_TRACKER_PATH, or set CR_TRACKER_SHEET_ID "
                "to read the live Google Sheet instead."
            ),
        }

    # Cheap enough to always recompute the stamp; the expensive fetch only happens on
    # an actual cache miss below.
    sid = sheet_id()
    stamp = (time.time() // _LIVE_CACHE_TTL_SECONDS) if sid else tracker_path().stat().st_mtime
    if _cache and _cache_stamp == stamp and not force:
        return _cache

    today = date.today()
    firms: list[dict] = []
    events: list[dict] = []

    tracker_rows, events_rows, source_name, stamp = _read_source()

    if tracker_rows:
        header = _header_map(tracker_rows)
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
        for row in tracker_rows[1:]:
            name = row.get(col["firm"] or "", "")
            if not name:
                continue
            last = _excel_date(row.get(col["last_meeting"] or "", ""))
            relationship = row.get(col["relationship"] or "", "")
            next_action = row.get(col["next_action"] or "", "")
            firms.append(
                {
                    "firm": name,
                    "website": row.get(col["website"] or "", ""),
                    "relationship": relationship,
                    "status": row.get(col["status"] or "", ""),
                    "owner": row.get(col["owner"] or "", ""),
                    "next_action": next_action,
                    "next_action_entries": _split_entries(next_action),
                    "renewal_date": str(_excel_date(row.get(col["renewal"] or "", "")) or ""),
                    "last_meeting": str(last or ""),
                    "days_since": (today - last).days if last else None,
                    "frozen": relationship.strip().lower() == "frozen",
                }
            )

    if events_rows:
        header = _header_map(events_rows)
        title_col = _find_col(header, "event title")
        start_col = _find_col(header, "start time")
        for row in events_rows[1:]:
            title = row.get(title_col or "", "")
            when = _excel_date(row.get(start_col or "", ""))
            if title and when and when >= today:
                events.append({"title": title, "date": when})

    # A firm marked "Frozen" in the relationship column is off the active list by CR's
    # own account -- surfacing it in "who's overdue" or "no next action" just adds
    # noise, since freezing *is* the current plan for it.
    frozen_total = sum(1 for f in firms if f["frozen"])
    active = [f for f in firms if not f["frozen"]]

    # The calendar export holds titles, not firm ids, so an upcoming meeting is tied to
    # a firm by its name appearing in the title. Imprecise, and labelled as such.
    upcoming = []
    for firm in active:
        key = _norm(firm["firm"])
        if len(key) < 4:
            continue
        hits = sorted(e["date"] for e in events if key in _norm(e["title"]))
        if hits:
            upcoming.append({**firm, "next_meeting": str(hits[0])})
    upcoming.sort(key=lambda r: r["next_meeting"])
    booked = {r["firm"] for r in upcoming}

    never_met = [f for f in active if not f["last_meeting"] and f["firm"] not in booked]
    longest_gap = sorted(
        (f for f in active if f["days_since"] is not None),
        key=lambda f: -f["days_since"],
    )
    no_next_action = [f for f in active if not f["next_action"]]

    _cache = {
        "configured": True,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source": source_name,
        "counts": {
            "firms": len(firms),
            "with_meeting_history": sum(1 for f in firms if f["last_meeting"]),
            "upcoming_events": len(events),
            "frozen_excluded": frozen_total,
        },
        "caveats": [
            "Upcoming meetings are matched to a firm by its name appearing in the calendar entry's title, so a differently-titled meeting will be missed.",
            "'No meeting recorded' means the tracker's Previous Webex column is empty and no upcoming meeting was matched -- not proof that no call ever happened.",
            f"{frozen_total} firms marked 'Frozen' are excluded from every list below.",
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
