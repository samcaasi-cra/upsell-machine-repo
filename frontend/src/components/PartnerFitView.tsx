import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { PartnerFitBoard } from "../types";
import { SpinnerBlock } from "./Spinner";
import "./PartnerFitView.css";

/* Which customers look ready for a SecurityScorecard partner product, and why.

   The signals are the same ones the board already detects -- this view answers a
   different question with them: not "what changed at this account" but "which partner
   conversation does that change justify". The rules are printed on screen so a CSM can
   disagree with the ranking rather than take it on trust. */

export function PartnerFitView() {
  const [board, setBoard] = useState<PartnerFitBoard | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getPartnerFit()
      .then(setBoard)
      .catch((e) => setError(e instanceof Error ? e.message : "Couldn't load partner fit."));
  }, []);

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

      <details className="pf-rules">
        <summary>How this list is ranked</summary>
        <ul>
          {board.rules.map((r) => (
            <li key={r}>{r}</li>
          ))}
        </ul>
        <p>
          No new data is collected for this view. It re-reads the signals already on the board and asks which partner
          conversation they justify.
        </p>
      </details>

      <ol className="pf-rows">
        {board.rows.map((row, i) => (
          <li className="pf-row" key={row.customer_id}>
            <span className="pf-rank">{i + 1}</span>
            <div className="pf-body">
              <div className="pf-row-head">
                <h3>{row.customer_name}</h3>
                <span className="pf-fit" title="Higher means more reasons, weighted">
                  fit {row.fit_score}
                </span>
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
              <p className="pf-recipient">
                Send to: <strong>{row.recipient_role}</strong>
              </p>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
