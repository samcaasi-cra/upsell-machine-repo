import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import "./OpportunityBoard.css";
import type { ViewMode } from "./BoardControls";
import { OpportunityTicket, type TicketData } from "./OpportunityTicket";

type Briefing = Awaited<ReturnType<typeof api.getToday>>;
type Priority = Briefing["priorities"][number];

function actionBadge(p: Priority, status: "approved" | "dismissed" | undefined): string | null {
  if (!p.action_id) return null;
  if (status === "approved") return "✓ Approved";
  if (status === "dismissed") return "Dismissed";
  return "✓ Queued by agent";
}

/** Adapts one of the agent's freely-drafted priorities into the same card shape the
 * Opportunities board renders, so a CSM sees the same kind of card wherever it shows
 * up. There's no single real data_source for a synthesized worklist item -- it's the
 * agent's own reasoning over several sources -- so "researched" (assembled by us, not
 * returned by one API) is the closest honest fit. */
function toTicketData(p: Priority, index: number, status: "approved" | "dismissed" | undefined): TicketData {
  return {
    customer_name: p.customer,
    data_source: "researched",
    source_detail:
      "Synthesized by the Today agent from live SSC scores, sample usage data, and researched " +
      "news/decision-maker signals in one pass -- see the tool-call trace below for exactly what " +
      "it looked at.",
    concept_trigger: null,
    badge: actionBadge(p, status),
    value: `#${index + 1}`,
    label: p.headline,
    sentiment: "watch",
    description: p.action,
    detail: p.why,
    detected_at: new Date().toISOString().slice(0, 10),
  };
}

/**
 * The landing screen, and the point of the whole thing.
 *
 * The Opportunities board shows every signal and leaves the CSM to scan, filter and
 * decide. This asks the agent to do that reasoning and hand back three things to do
 * today, in order, with the outreach already drafted -- approve or skip rather than
 * work it out yourself.
 */
export function TodayView({ viewMode, onSeeAll }: { viewMode: ViewMode; onSeeAll: () => void }) {
  const [briefing, setBriefing] = useState<Briefing | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [openIndex, setOpenIndex] = useState<number | null>(null);
  const [copied, setCopied] = useState<number | null>(null);
  const [actionStatus, setActionStatus] = useState<Record<string, "approved" | "dismissed">>({});

  const load = useCallback(async (refresh = false) => {
    if (refresh) setRefreshing(true);
    else setLoading(true);
    setError(null);
    try {
      setBriefing(await api.getToday(refresh));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function copyEmail(i: number, subject: string, body: string) {
    await navigator.clipboard.writeText(`Subject: ${subject}\n\n${body}`);
    setCopied(i);
    setTimeout(() => setCopied(null), 1600);
  }

  async function approve(actionId: string) {
    await api.approveAction(actionId);
    setActionStatus((prev) => ({ ...prev, [actionId]: "approved" }));
  }

  async function dismiss(actionId: string) {
    await api.dismissAction(actionId);
    setActionStatus((prev) => ({ ...prev, [actionId]: "dismissed" }));
  }

  return (
    <div className="opp-board">
      <header className="opp-topbar">
        <div>
          <h2>Today</h2>
        </div>
        <div className="opp-topbar-meta">
          {briefing?.pseudonymised && (
            <span className="opp-illustrative-badge">Identities masked before model call</span>
          )}
          <span style={{ fontSize: "0.68rem", color: "var(--slate)", display: "flex", gap: 8, alignItems: "center" }}>
            {briefing?.tokens && (
              <>{briefing.tokens.prompt + briefing.tokens.completion} tokens · once per day</>
            )}
            <button
              className="opp-btn"
              style={{ fontSize: "0.68rem", padding: "3px 8px" }}
              onClick={() => load(true)}
              disabled={refreshing || loading}
            >
              {refreshing ? "Rebuilding…" : "Refresh"}
            </button>
          </span>
        </div>
      </header>

      <div style={{ padding: "18px 20px 24px" }}>
        {loading && (
          <p style={{ color: "var(--slate)", fontSize: 14 }}>
            The agent is reviewing the portfolio — surveying every account, then drilling into what
            matters…
          </p>
        )}

        {error && <p style={{ color: "var(--amber-ink)", fontSize: 14 }}>{error}</p>}

        {briefing?.error && (
          <p style={{ color: "var(--amber-ink)", fontSize: 14 }}>
            {briefing.error} Try Refresh.
          </p>
        )}

        {!loading && briefing && briefing.priorities.length > 0 && (
          <>
            <p style={{ margin: "0 0 16px", fontSize: 14, color: "var(--slate)" }}>
              The agent reviewed all your accounts and picked the {briefing.priorities.length} worth
              your time today.
            </p>

            <div style={{ display: "grid", gap: 12 }}>
              {briefing.priorities.map((p, i) => (
                <div key={i}>
                  <OpportunityTicket
                    card={toTicketData(p, i, p.action_id ? actionStatus[p.action_id] : undefined)}
                    domain=""
                    viewMode={viewMode}
                    actioned={p.action_id ? actionStatus[p.action_id] === "approved" : false}
                    onOpen={() => setOpenIndex(openIndex === i ? null : i)}
                  />

                  {openIndex === i && (
                    <div
                      style={{
                        marginTop: -1,
                        border: "1px solid var(--border)",
                        borderTop: "none",
                        borderRadius: "0 0 6px 6px",
                        padding: "14px 16px 16px",
                        background: "var(--surface)",
                      }}
                    >
                      <div style={{ fontSize: "0.75rem", color: "var(--slate)", marginBottom: 4 }}>
                        Subject
                      </div>
                      <div style={{ fontWeight: 600, fontSize: "0.87rem", marginBottom: 10 }}>
                        {p.email_subject}
                      </div>
                      <div className="opp-drawer-email-body" style={{ fontSize: "0.85rem" }}>
                        {p.email_body}
                      </div>
                      {p.reflection && (
                        <p style={{ margin: "10px 0 0", fontSize: "0.76rem", color: "var(--petrol)", lineHeight: 1.5 }}>
                          <strong>Agent's own check before queuing:</strong> {p.reflection}
                        </p>
                      )}
                      <div style={{ display: "flex", gap: 8, marginTop: 10, flexWrap: "wrap" }}>
                        <button
                          className="opp-btn opp-btn-primary"
                          style={{ fontSize: "0.75rem", padding: "6px 12px" }}
                          onClick={() => copyEmail(i, p.email_subject, p.email_body)}
                        >
                          {copied === i ? "Copied" : "Copy email"}
                        </button>
                        {p.action_id && !actionStatus[p.action_id] && (
                          <>
                            <button
                              className="opp-btn"
                              style={{ fontSize: "0.75rem", padding: "6px 12px" }}
                              onClick={() => approve(p.action_id!)}
                            >
                              Approve & send
                            </button>
                            <button
                              className="opp-btn"
                              style={{ fontSize: "0.75rem", padding: "6px 12px" }}
                              onClick={() => dismiss(p.action_id!)}
                            >
                              Dismiss
                            </button>
                          </>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>

            <div style={{ marginTop: 18, display: "flex", alignItems: "center", gap: 10 }}>
              <button className="opp-btn" onClick={onSeeAll}>
                See every signal →
              </button>
              <span style={{ fontSize: "0.72rem", color: "var(--slate)" }}>
                {briefing.tool_calls.length} tool calls · agent chose which accounts to examine
              </span>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
