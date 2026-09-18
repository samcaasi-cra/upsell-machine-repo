import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { CrTrackerBoard, CrTrackerFirm } from "../types";
import { SpinnerBlock } from "./Spinner";
import "./CrTrackerView.css";

/* Cyber Rescue's own account tracking -- internal, not customer-facing.

   Reads the team's working spreadsheet from outside the repository. Contact names and
   email addresses in that file are never loaded. */

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

export function CrTrackerView() {
  const [board, setBoard] = useState<CrTrackerBoard | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [active, setActive] = useState<ListKey>("upcoming");

  useEffect(() => {
    api
      .getCrTracker()
      .then(setBoard)
      .catch((e) => setError(e instanceof Error ? e.message : "Couldn't load the tracker."));
  }, []);

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

  const rows: CrTrackerFirm[] = board[active];

  return (
    <div className="cr">
      <header className="cr-head">
        <div>
          <h2>Cyber Rescue account tracking</h2>
          <p className="cr-sub">
            {board.counts.firms.toLocaleString()} firms · {board.counts.with_meeting_history} with meeting history ·{" "}
            {board.counts.upcoming_events.toLocaleString()} calendar entries ahead
          </p>
        </div>
        <span className="cr-private">Internal · local file, never in the repo</span>
      </header>

      <div className="cr-tabs" role="tablist">
        {LISTS.map((l) => (
          <button
            key={l.key}
            type="button"
            role="tab"
            aria-selected={active === l.key}
            className="cr-tab"
            onClick={() => setActive(l.key)}
          >
            <span className="cr-tab-count">{total(l.key).toLocaleString()}</span>
            <span className="cr-tab-title">{l.title}</span>
          </button>
        ))}
      </div>

      <p className="cr-blurb">{LISTS.find((l) => l.key === active)?.blurb}</p>

      <table className="cr-table">
        <thead>
          <tr>
            <th>Firm</th>
            <th>Owner</th>
            <th>Relationship</th>
            {active === "upcoming" && <th>Next meeting</th>}
            {active === "longest_gap" && <th>Last meeting</th>}
            {active === "longest_gap" && <th>Days</th>}
            {active !== "no_next_action" && <th>Next action</th>}
            {active === "no_next_action" && <th>Renewal</th>}
          </tr>
        </thead>
        <tbody>
          {rows.map((f) => (
            <tr key={f.firm}>
              <td className="cr-firm">{f.firm}</td>
              <td>{f.owner || "—"}</td>
              <td>{f.relationship || "—"}</td>
              {active === "upcoming" && <td className="cr-date">{f.next_meeting}</td>}
              {active === "longest_gap" && <td className="cr-date">{f.last_meeting}</td>}
              {active === "longest_gap" && <td className="cr-days">{f.days_since}</td>}
              {active !== "no_next_action" && <td className="cr-action">{f.next_action || "— none —"}</td>}
              {active === "no_next_action" && <td className="cr-date">{f.renewal_date || "—"}</td>}
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length < total(active) && (
        <p className="cr-more">
          Showing {rows.length} of {total(active).toLocaleString()}.
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
