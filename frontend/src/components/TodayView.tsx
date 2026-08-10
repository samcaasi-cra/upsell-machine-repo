import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import "./OpportunityBoard.css";

type Briefing = Awaited<ReturnType<typeof api.getToday>>;

/**
 * The landing screen, and the point of the whole thing.
 *
 * The Opportunities board shows every signal and leaves the CSM to scan, filter and
 * decide. This asks the agent to do that reasoning and hand back three things to do
 * today, in order, with the outreach already drafted -- approve or skip rather than
 * work it out yourself.
 */
export function TodayView({ onSeeAll }: { onSeeAll: () => void }) {
  const [briefing, setBriefing] = useState<Briefing | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [openIndex, setOpenIndex] = useState<number | null>(null);
  const [copied, setCopied] = useState<number | null>(null);

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

  return (
    <div className="opp-board">
      <header className="opp-topbar">
        <div>
          <span className="opp-eyebrow">SecurityScorecard · Customer Success</span>
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
                <article
                  key={i}
                  style={{
                    background: "var(--surface)",
                    border: "1px solid var(--border)",
                    borderRadius: 4,
                    padding: "16px 18px",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "baseline", gap: 12, marginBottom: 6 }}>
                    <span
                      style={{
                        fontFamily: "var(--font-mono)",
                        fontSize: "1.1rem",
                        fontWeight: 600,
                        color: "var(--amber)",
                      }}
                    >
                      {i + 1}
                    </span>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: "1.02rem" }}>
                        {p.customer}
                      </div>
                      <div style={{ fontSize: "0.78rem", color: "var(--slate)" }}>{p.headline}</div>
                    </div>
                  </div>

                  <p style={{ margin: "0 0 10px", fontSize: "0.87rem", lineHeight: 1.5 }}>{p.why}</p>

                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      gap: 12,
                      flexWrap: "wrap",
                      borderTop: "1px solid var(--border)",
                      paddingTop: 10,
                    }}
                  >
                    <span style={{ fontSize: "0.82rem", fontWeight: 600, color: "var(--petrol)" }}>
                      → {p.action}
                    </span>
                    <button
                      className="opp-btn"
                      style={{ fontSize: "0.75rem", padding: "5px 10px" }}
                      onClick={() => setOpenIndex(openIndex === i ? null : i)}
                    >
                      {openIndex === i ? "Hide draft" : "Review draft email"}
                    </button>
                  </div>

                  {openIndex === i && (
                    <div style={{ marginTop: 12 }}>
                      <div style={{ fontSize: "0.75rem", color: "var(--slate)", marginBottom: 4 }}>
                        Subject
                      </div>
                      <div style={{ fontWeight: 600, fontSize: "0.87rem", marginBottom: 10 }}>
                        {p.email_subject}
                      </div>
                      <div className="opp-drawer-email-body" style={{ fontSize: "0.85rem" }}>
                        {p.email_body}
                      </div>
                      <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
                        <button
                          className="opp-btn opp-btn-primary"
                          style={{ fontSize: "0.75rem", padding: "6px 12px" }}
                          onClick={() => copyEmail(i, p.email_subject, p.email_body)}
                        >
                          {copied === i ? "Copied" : "Copy email"}
                        </button>
                      </div>
                    </div>
                  )}
                </article>
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
