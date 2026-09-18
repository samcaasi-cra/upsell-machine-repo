import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import type { PartnerFitBoard } from "../types";
import { InfoPopover } from "./InfoPopover";
import { SpinnerBlock } from "./Spinner";
import "./PartnerFitView.css";

/* Which customers look ready for a SecurityScorecard partner product, and why.

   The signals are the same ones the board already detects -- this view answers a
   different question with them: not "what changed at this account" but "which partner
   conversation does that change justify". The rules are printed on screen so a CSM can
   disagree with the ranking rather than take it on trust -- as a compact legend with the
   reasoning a click away, not a wall of text, matching how the rest of the app handles
   "short by default, detail on demand" everywhere else. */

type SortBy = "fit" | "name";

export function PartnerFitView() {
  const [board, setBoard] = useState<PartnerFitBoard | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [openRow, setOpenRow] = useState<string | null>(null);
  const [copied, setCopied] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<SortBy>("fit");

  const copy = async (id: string, text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(id);
      window.setTimeout(() => setCopied(null), 2000);
    } catch {
      setCopied(null);
    }
  };

  useEffect(() => {
    api
      .getPartnerFit()
      .then(setBoard)
      .catch((e) => setError(e instanceof Error ? e.message : "Couldn't load partner fit."));
  }, []);

  const rows = useMemo(() => {
    if (!board) return [];
    if (sortBy === "name") return [...board.rows].sort((a, b) => a.customer_name.localeCompare(b.customer_name));
    return board.rows; // already fit-score sorted by the backend
  }, [board, sortBy]);

  if (error) return <p className="pf-error">{error}</p>;
  if (!board) return <SpinnerBlock minHeight={200} />;

  const cytactic = board.partners.find((p) => p.status === "live");
  const upcoming = board.partners.filter((p) => p.status === "upcoming");

  return (
    <div className="pf">
      <header className="pf-head">
        <div>
          <h2>
            {board.rows.length} customers look ready for {cytactic?.name ?? "a partner"}
          </h2>
          <p className="pf-sub">{cytactic?.sells}</p>
        </div>
        <div className="pf-partners">
          {upcoming.map((p) => (
            <span className="pf-partner-stub" key={p.id}>
              {p.name} · upcoming
            </span>
          ))}
        </div>
      </header>

      <div className="pf-legend">
        <span className="pf-legend-label">Scoring signals:</span>
        {board.rules.map((r) => (
          <span className="pf-legend-chip" key={r.signal}>
            {r.signal}
            <b>{r.weight}</b>
            <InfoPopover label={`Why "${r.signal}" counts`} align="left">
              <span className="opp-source-pop-head">{r.signal}</span>
              {r.why}
            </InfoPopover>
          </span>
        ))}
        <InfoPopover label="How the total is calculated" align="left">
          <span className="opp-source-pop-head">Scoring</span>
          {board.scoring_note}
        </InfoPopover>
      </div>

      <div className="pf-sort" role="group" aria-label="Sort by">
        <span className="pf-legend-label">Sort:</span>
        {(["fit", "name"] as SortBy[]).map((s) => (
          <button key={s} type="button" className="pf-sort-btn" aria-pressed={sortBy === s} onClick={() => setSortBy(s)}>
            {s === "fit" ? "Fit score" : "Name"}
          </button>
        ))}
      </div>

      <ol className="pf-rows">
        {rows.map((row) => (
          <li className="pf-row" key={row.customer_id}>
            <span className="pf-fit" title="Fit score — higher means more reasons, weighted">
              <b>{row.fit_score}</b>
              fit
            </span>
            <div className="pf-body">
              <div className="pf-row-head">
                <h3>{row.customer_name}</h3>
              </div>
              <ul className="pf-reasons">
                {row.reasons.map((r) => (
                  <li key={r.text}>
                    <span className={`pf-tier pf-tier-${r.tier}`}>{r.tier}</span>
                    <span className="pf-reason-text">{r.text}</span>
                    <span className="pf-source">{r.source}</span>
                  </li>
                ))}
              </ul>
              <p className="pf-track">
                <strong>Talk track:</strong> {row.talk_track}
              </p>

              <div className="pf-actions">
                <button
                  type="button"
                  className="pf-btn pf-btn-primary"
                  aria-expanded={openRow === row.customer_id}
                  onClick={() => setOpenRow(openRow === row.customer_id ? null : row.customer_id)}
                >
                  {openRow === row.customer_id ? "Hide draft" : "Draft the intro"}
                </button>
                <span className="pf-recipient">
                  to <strong>{row.recipient_role}</strong>
                </span>
              </div>

              {openRow === row.customer_id && (
                <div className="pf-draft">
                  <p className="pf-draft-subject">
                    <strong>Subject:</strong> {row.subject}
                  </p>
                  <pre className="pf-draft-body">{row.body}</pre>
                  <div className="pf-actions">
                    <button
                      type="button"
                      className="pf-btn"
                      onClick={() => copy(row.customer_id, `Subject: ${row.subject}\n\n${row.body}`)}
                    >
                      {copied === row.customer_id ? "Copied" : "Copy email"}
                    </button>
                    <span className="pf-note">Template, not generated — a CSM edits and sends it.</span>
                  </div>
                </div>
              )}
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
