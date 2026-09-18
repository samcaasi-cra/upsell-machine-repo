import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import type { CrTrackerBoard, CrTrackerFirm } from "../types";
import { SpinnerBlock } from "./Spinner";
import "./CrTrackerView.css";

/* Cyber Rescue's own account tracking -- internal, not customer-facing.

   Reads the team's working spreadsheet from outside the repository. Contact names and
   email addresses in that file are never loaded. Firms marked "Frozen" are dropped by
   the backend before this ever sees them. */

type ListKey = "never_met" | "upcoming" | "longest_gap" | "no_next_action";

const LISTS: { key: ListKey; title: string; blurb: string }[] = [
  {
    key: "upcoming",
    title: "Meetings coming up",
    blurb: "Matched from the calendar export, soonest first.",
  },
  {
    key: "longest_gap",
    title: "Longest since a meeting",
    blurb: "From the tracker's Previous Webex column, longest gap first.",
  },
  {
    key: "never_met",
    title: "No meeting recorded",
    blurb: "No previous meeting logged, and nothing upcoming matched.",
  },
  {
    key: "no_next_action",
    title: "No planned next action",
    blurb: "The tracker's next-actions column is empty.",
  },
];

type SortKey = "firm" | "owner" | "relationship" | "days_since" | "next_meeting" | "renewal_date";
type SortDir = "asc" | "desc";

const SORTERS: Record<SortKey, (f: CrTrackerFirm) => string | number> = {
  firm: (f) => f.firm.toLowerCase(),
  owner: (f) => (f.owner || "").toLowerCase(),
  relationship: (f) => (f.relationship || "").toLowerCase(),
  days_since: (f) => f.days_since ?? -1,
  next_meeting: (f) => f.next_meeting || "",
  renewal_date: (f) => f.renewal_date || "",
};

const ENTRIES_COLLAPSED = 3;

export function CrTrackerView() {
  const [board, setBoard] = useState<CrTrackerBoard | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [active, setActive] = useState<ListKey>("upcoming");
  const [query, setQuery] = useState("");
  const [relFilter, setRelFilter] = useState("all");
  const [sort, setSort] = useState<{ key: SortKey; dir: SortDir } | null>(null);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  useEffect(() => {
    api
      .getCrTracker()
      .then(setBoard)
      .catch((e) => setError(e instanceof Error ? e.message : "Couldn't load the tracker."));
  }, []);

  // Filters/sort are per-list state that don't carry over -- switching lists resets them.
  const switchTo = (key: ListKey) => {
    setActive(key);
    setQuery("");
    setRelFilter("all");
    setSort(null);
    setExpanded(new Set());
  };

  const rawRows: CrTrackerFirm[] = board?.[active] ?? [];

  const relationships = useMemo(
    () => Array.from(new Set(rawRows.map((f) => f.relationship).filter(Boolean))).sort(),
    [rawRows],
  );

  const rows = useMemo(() => {
    let out = rawRows;
    if (relFilter !== "all") out = out.filter((f) => f.relationship === relFilter);
    if (query.trim()) {
      const q = query.trim().toLowerCase();
      out = out.filter((f) => f.firm.toLowerCase().includes(q) || (f.owner || "").toLowerCase().includes(q));
    }
    if (sort) {
      const { key, dir } = sort;
      const getter = SORTERS[key];
      out = [...out].sort((a, b) => {
        const av = getter(a);
        const bv = getter(b);
        const cmp = av < bv ? -1 : av > bv ? 1 : 0;
        return dir === "asc" ? cmp : -cmp;
      });
    }
    return out;
  }, [rawRows, relFilter, query, sort]);

  if (error) return <p className="cr-error">{error}</p>;
  if (!board) return <SpinnerBlock minHeight={200} />;
  if (!board.configured) return <p className="cr-error">{board.detail}</p>;

  const total = (key: ListKey) =>
    ({
      never_met: board.never_met_total,
      upcoming: board.upcoming_total,
      longest_gap: board.longest_gap_total,
      no_next_action: board.no_next_action_total,
    })[key];

  const toggleSort = (key: SortKey) =>
    setSort((s) => (s && s.key === key ? (s.dir === "asc" ? { key, dir: "desc" } : null) : { key, dir: "asc" }));

  const sortIndicator = (key: SortKey) => (sort?.key === key ? (sort.dir === "asc" ? " ▲" : " ▼") : "");

  const toggleExpanded = (firm: string) =>
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(firm)) next.delete(firm);
      else next.add(firm);
      return next;
    });

  return (
    <div className="cr">
      <header className="cr-head">
        <div>
          <h2>Cyber Rescue account tracking</h2>
          <p className="cr-sub">
            {board.counts.firms.toLocaleString()} firms · {board.counts.with_meeting_history} with meeting history ·{" "}
            {board.counts.upcoming_events.toLocaleString()} calendar entries ahead ·{" "}
            {board.counts.frozen_excluded.toLocaleString()} frozen (hidden)
          </p>
        </div>
        <span className="cr-private">
          Internal · {board.source.includes("live") ? "live Google Sheet, never stored" : "local file, never in the repo"}
        </span>
      </header>

      <div className="cr-tabs" role="tablist">
        {LISTS.map((l) => (
          <button
            key={l.key}
            type="button"
            role="tab"
            aria-selected={active === l.key}
            className="cr-tab"
            onClick={() => switchTo(l.key)}
          >
            <span className="cr-tab-count">{total(l.key).toLocaleString()}</span>
            <span className="cr-tab-title">{l.title}</span>
          </button>
        ))}
      </div>

      <p className="cr-blurb">{LISTS.find((l) => l.key === active)?.blurb}</p>

      <div className="cr-filters">
        <input
          type="search"
          className="cr-search"
          placeholder="Filter by firm or owner…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        {relationships.length > 0 && (
          <select className="cr-select" value={relFilter} onChange={(e) => setRelFilter(e.target.value)}>
            <option value="all">All relationships</option>
            {relationships.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>
        )}
        {(query || relFilter !== "all" || sort) && (
          <button
            type="button"
            className="cr-clear"
            onClick={() => {
              setQuery("");
              setRelFilter("all");
              setSort(null);
            }}
          >
            Clear
          </button>
        )}
      </div>

      <table className="cr-table">
        <thead>
          <tr>
            <th className="cr-sortable" onClick={() => toggleSort("firm")}>
              Firm{sortIndicator("firm")}
            </th>
            <th className="cr-sortable" onClick={() => toggleSort("owner")}>
              Owner{sortIndicator("owner")}
            </th>
            <th className="cr-sortable" onClick={() => toggleSort("relationship")}>
              Relationship{sortIndicator("relationship")}
            </th>
            {active === "upcoming" && (
              <th className="cr-sortable" onClick={() => toggleSort("next_meeting")}>
                Next meeting{sortIndicator("next_meeting")}
              </th>
            )}
            {active === "longest_gap" && <th>Last meeting</th>}
            {active === "longest_gap" && (
              <th className="cr-sortable" onClick={() => toggleSort("days_since")}>
                Days{sortIndicator("days_since")}
              </th>
            )}
            {active !== "no_next_action" && <th>Next action</th>}
            {active === "no_next_action" && (
              <th className="cr-sortable" onClick={() => toggleSort("renewal_date")}>
                Renewal{sortIndicator("renewal_date")}
              </th>
            )}
          </tr>
        </thead>
        <tbody>
          {rows.map((f) => {
            const entries = f.next_action_entries;
            const isOpen = expanded.has(f.firm);
            const shown = isOpen ? entries : entries.slice(0, ENTRIES_COLLAPSED);
            const hidden = entries.length - shown.length;
            return (
              <tr key={f.firm}>
                <td className="cr-firm">{f.firm}</td>
                <td>{f.owner || "—"}</td>
                <td>{f.relationship || "—"}</td>
                {active === "upcoming" && <td className="cr-date">{f.next_meeting}</td>}
                {active === "longest_gap" && <td className="cr-date">{f.last_meeting}</td>}
                {active === "longest_gap" && <td className="cr-days">{f.days_since}</td>}
                {active !== "no_next_action" && (
                  <td className="cr-action">
                    {shown.length === 0 && "— none —"}
                    <div className={isOpen ? "cr-entries cr-entries-scroll" : "cr-entries"}>
                      {shown.map((entry, i) => (
                        <p key={i} className="cr-entry">
                          {entry}
                        </p>
                      ))}
                    </div>
                    {hidden > 0 && (
                      <button type="button" className="cr-expand" onClick={() => toggleExpanded(f.firm)}>
                        +{hidden} more
                      </button>
                    )}
                    {isOpen && entries.length > ENTRIES_COLLAPSED && (
                      <button type="button" className="cr-expand" onClick={() => toggleExpanded(f.firm)}>
                        Show fewer
                      </button>
                    )}
                  </td>
                )}
                {active === "no_next_action" && <td className="cr-date">{f.renewal_date || "—"}</td>}
              </tr>
            );
          })}
        </tbody>
      </table>
      {rows.length === 0 && <p className="cr-more">No firms match this filter.</p>}
      {rows.length < total(active) && (
        <p className="cr-more">
          Showing {rows.length} of {total(active).toLocaleString()}
          {(query || relFilter !== "all") && " (filtered)"}.
        </p>
      )}

      <ul className="cr-caveats">
        {board.caveats.map((c) => (
          <li key={c}>{c}</li>
        ))}
      </ul>
    </div>
  );
}
