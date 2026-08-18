import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import "./OpportunityBoard.css";
import "./SuccessPlanView.css";
import { InfoPopover } from "./InfoPopover";
import { LiveIcon, MockupIcon, ResearchedIcon, SampleIcon } from "./icons";
import { SpinnerBlock } from "./Spinner";
import type { DataSource, SuccessPlan, SuccessPlanChange } from "../types";

function SourceIcon({ source }: { source: DataSource }) {
  if (source === "live") return <LiveIcon style={{ color: "var(--moss)" }} />;
  if (source === "researched") return <ResearchedIcon style={{ color: "var(--petrol)" }} />;
  if (source === "sample") return <SampleIcon style={{ color: "var(--slate)" }} />;
  return <MockupIcon style={{ color: "var(--petrol)" }} />;
}

function fmt(iso: string): string {
  const d = new Date(iso + "T00:00:00");
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
}

function ChangeRow({ change }: { change: SuccessPlanChange }) {
  return (
    <li className="sp-change" data-direction={change.direction}>
      <span className="sp-change-cat">{change.category}</span>
      <span className="sp-change-body">
        <span className="sp-change-headline">{change.headline}</span>
        <span className="sp-change-detail">{change.detail}</span>
      </span>
      <span className="sp-change-source" onClick={(e) => e.stopPropagation()}>
        <SourceIcon source={change.data_source} />
        {change.source_detail && <InfoPopover label="Where this came from">{change.source_detail}</InfoPopover>}
      </span>
    </li>
  );
}

/**
 * The joint success plan: what the customer said they were trying to fix, the number
 * both sides agreed to be judged on, and everything that has moved since.
 *
 * The plan half is mocked -- a CRM owns it and we have no Salesforce access, so it's
 * tagged as a mockup wherever it appears. The changes underneath are real, from the
 * same sources the board uses, which is the point: the agreement is the only part
 * we're inventing.
 */
export function SuccessPlanView() {
  const [plans, setPlans] = useState<SuccessPlan[] | null>(null);
  const [selectedId, setSelectedId] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .listSuccessPlans()
      .then((data) => {
        setPlans(data);
        if (data.length) setSelectedId((prev) => prev || data[0].customer_id);
      })
      .catch((err) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false));
  }, []);

  const plan = useMemo(
    () => plans?.find((p) => p.customer_id === selectedId) ?? null,
    [plans, selectedId]
  );

  if (loading) return <SpinnerBlock />;
  if (error) return <p style={{ color: "var(--status-critical)" }}>Failed to load: {error}</p>;
  if (!plan || !plans) return null;

  const m = plan.metric;
  const needsAttention = plan.changes.filter((c) => c.direction === "down");
  // Importance, not category, drives order -- items needing attention float to the
  // top regardless of whether they're a Score, Supplier, or People change; positive
  // movement comes next; flat/neutral items last.
  const importanceRank: Record<SuccessPlanChange["direction"], number> = { down: 0, up: 1, flat: 2 };
  const sortedChanges = [...plan.changes].sort(
    (a, b) => importanceRank[a.direction] - importanceRank[b.direction]
  );

  return (
    <div className="opp-board sp-view">
      <header className="sp-head">
        <div>
          <h2 className="sp-title">Joint success plan with the customer</h2>
          <p className="sp-sub">
            What they're trying to fix, what we agreed to measure, and everything that has moved in the
            last 30 days.
          </p>
        </div>
        <label className="sp-picker">
          <span>Customer</span>
          <select value={selectedId} onChange={(e) => setSelectedId(e.target.value)}>
            {plans.map((p) => (
              <option key={p.customer_id} value={p.customer_id}>
                {p.customer_name}
              </option>
            ))}
          </select>
        </label>
      </header>

      <div className="sp-summary">
        <h3 className="sp-summary-heading">Executive Summary</h3>
        <p className="sp-summary-text">{plan.summary}</p>
      </div>

      <div className="sp-grid">
        {/* --- the agreement --- */}
        <section className="sp-card">
          <div className="sp-card-head">
            <h3>The problem they are paying SSC to solve</h3>
            <span className="sp-src">
              <MockupIcon style={{ color: "var(--petrol)" }} />
              <InfoPopover label="Where this came from">{plan.plan_source_detail}</InfoPopover>
            </span>
          </div>
          <p className="sp-objective">{plan.objective}</p>
          <p className="sp-scope">{plan.scope}</p>
          <dl className="sp-meta">
            <dt>Sponsor</dt>
            <dd>{plan.sponsor}</dd>
            <dt>Owner</dt>
            <dd>{plan.owner}</dd>
            <dt>Agreed</dt>
            <dd>{fmt(plan.agreed_on)}</dd>
            <dt>Next review</dt>
            <dd>{fmt(plan.next_review)}</dd>
          </dl>
        </section>

        {/* --- how success is measured --- */}
        <section className="sp-card">
          <div className="sp-card-head">
            <h3>How we agreed to measure success</h3>
            <span className="sp-src">
              <MockupIcon style={{ color: "var(--petrol)" }} />
              <InfoPopover label="Where this came from">
                The agreed baseline, target and date are mocked — Salesforce owns these. The current
                score beside them is live from the SecurityScorecard API.
              </InfoPopover>
            </span>
          </div>
          <p className="sp-metric-label">{m.label}</p>

          {(() => {
            const exceeded = m.current !== null && m.current > m.target;
            const belowBaseline = m.current !== null && m.current < m.baseline;
            const currentNote = exceeded ? " · exceeded target" : belowBaseline ? " · below baseline" : "";
            const current = (
              <span className="sp-num sp-num-now" data-ontrack={m.on_track}>
                <b>{m.current ?? "—"}</b>
                <em>today · live{currentNote}</em>
              </span>
            );
            const baseline = (
              <span className="sp-num">
                <b>{m.baseline}</b>
                <em>baseline</em>
              </span>
            );
            const target = (
              <span className="sp-num">
                <b>{m.target}</b>
                <em>target</em>
              </span>
            );
            // "Current" always moves to whichever outer edge it has passed, with
            // whatever it passed taking the middle slot -- makes an overshoot in
            // either direction (past the target, or back below the starting point)
            // visually obvious instead of reading as "still on the way there."
            return (
              <div className="sp-numbers">
                {belowBaseline ? (
                  <>
                    {current}
                    {baseline}
                    {target}
                  </>
                ) : exceeded ? (
                  <>
                    {baseline}
                    {target}
                    {current}
                  </>
                ) : (
                  <>
                    {baseline}
                    {current}
                    {target}
                  </>
                )}
              </div>
            );
          })()}

          <div className="sp-bar" role="img" aria-label={`${m.progress_pct}% of the way to target`}>
            <span className="sp-bar-fill" data-ontrack={m.on_track} style={{ width: `${m.progress_pct}%` }} />
          </div>
          <p className="sp-bar-foot">
            <span>{m.progress_pct}% of the way there</span>
            <span className={m.on_track ? "sp-ontrack" : "sp-behind"}>
              {m.on_track ? "On track" : "Behind plan"} · due {fmt(m.due_date)}
            </span>
          </p>
        </section>
      </div>

      {/* --- what actually changed --- */}
      <section className="sp-card sp-changes-card">
        <div className="sp-card-head">
          <h3>
            What changed in the last 30 days
            <span className="sp-count">
              {plan.changes.length}
              {needsAttention.length > 0 && <em> · {needsAttention.length} to watch</em>}
            </span>
          </h3>
          <span className="sp-src-note">Every item below is real — icons show the source</span>
        </div>
        {plan.changes.length === 0 ? (
          <p className="sp-empty">Nothing moved at this account in the window.</p>
        ) : (
          <ul className="sp-changes">
            {sortedChanges.map((c, i) => (
              <ChangeRow key={`${c.category}-${i}`} change={c} />
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
