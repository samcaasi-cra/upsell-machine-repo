import { useEffect, useRef, useState, type FormEvent } from "react";
import { api } from "../api/client";
import "./OpportunityBoard.css";

type Turn = {
  role: "user" | "assistant";
  content: string;
  toolCalls?: { tool: string; arguments: Record<string, unknown> }[];
  tokens?: { prompt: number; completion: number };
};

const SUGGESTIONS = [
  "Which 3 accounts should I prioritise this week and why?",
  "Who has supplier risk I should know about?",
  "Which accounts have no CSM assigned but look healthy enough to upsell?",
  "Draft an intro email for the newest decision-maker we've found.",
];

export function AgentChat() {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<{ enabled: boolean; provider: string | null } | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.getAgentStatus().then(setStatus).catch(() => setStatus({ enabled: false, provider: null }));
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns, busy]);

  async function send(question: string) {
    if (!question.trim() || busy) return;
    const nextTurns: Turn[] = [...turns, { role: "user", content: question }];
    setTurns(nextTurns);
    setInput("");
    setBusy(true);
    setError(null);
    try {
      const result = await api.agentChat(nextTurns.map((t) => ({ role: t.role, content: t.content })));
      setTurns([
        ...nextTurns,
        { role: "assistant", content: result.reply, toolCalls: result.tool_calls, tokens: result.tokens },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  if (status && !status.enabled) {
    return (
      <div className="opp-board" style={{ padding: 24 }}>
        <h2 style={{ marginTop: 0 }}>Ask</h2>
        <p style={{ color: "var(--slate)", fontSize: 14 }}>
          The agent needs a model configured. Set <code>ANTHROPIC_API_KEY</code> or{" "}
          <code>OPENAI_API_KEY</code> in <code>backend/.env</code> and restart the backend.
        </p>
      </div>
    );
  }

  return (
    <div className="opp-board" style={{ display: "flex", flexDirection: "column", height: "calc(100vh - 190px)" }}>
      <header className="opp-topbar">
        <div>
          <h2>Ask</h2>
        </div>
        <div className="opp-topbar-meta">
          <span className="opp-illustrative-badge">
            {status?.provider ? `Agent · ${status.provider}` : "Agent"}
          </span>
          <span style={{ fontSize: "0.68rem", color: "var(--slate)" }}>
            Answers from live data — it chooses which tools to call
          </span>
        </div>
      </header>

      <div style={{ flex: 1, overflowY: "auto", padding: "16px 20px" }}>
        {turns.length === 0 && (
          <div>
            <p style={{ fontSize: 13, color: "var(--slate)", marginTop: 0 }}>
              Ask about the portfolio in plain English. Try:
            </p>
            <div style={{ display: "grid", gap: 8, maxWidth: 560 }}>
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  className="opp-btn"
                  style={{ textAlign: "left", fontWeight: 400 }}
                  onClick={() => send(s)}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {turns.map((turn, i) => (
          <div key={i} style={{ marginBottom: 18 }}>
            {turn.role === "user" ? (
              <div style={{ display: "flex", justifyContent: "flex-end" }}>
                <div
                  style={{
                    background: "var(--petrol)",
                    color: "#fff",
                    padding: "9px 13px",
                    borderRadius: 10,
                    maxWidth: "80%",
                    fontSize: 14,
                  }}
                >
                  {turn.content}
                </div>
              </div>
            ) : (
              <div>
                {/* The tool trace is the point: it shows the agent decided what to look at --
                    and, distinctly, when it decided to act rather than just read. */}
                {turn.toolCalls && turn.toolCalls.length > 0 && (
                  <div style={{ marginBottom: 8, display: "flex", flexWrap: "wrap", gap: 6, alignItems: "center" }}>
                    <span style={{ fontSize: "0.62rem", color: "var(--slate)", textTransform: "uppercase", letterSpacing: 0.5 }}>
                      Agent called
                    </span>
                    {turn.toolCalls.map((tc, j) => {
                      const isAction = tc.tool === "queue_outreach";
                      return (
                        <span
                          key={j}
                          className="opp-sample-tag"
                          style={{
                            borderStyle: "solid",
                            borderColor: isAction ? "var(--moss)" : "var(--petrol)",
                            color: isAction ? "var(--moss)" : "var(--petrol)",
                          }}
                          title={
                            isAction
                              ? `Reflected: ${tc.arguments.reasoning}\n\nSubject: ${tc.arguments.subject}`
                              : JSON.stringify(tc.arguments)
                          }
                        >
                          {isAction ? "✓ queue_outreach" : tc.tool}
                          {typeof tc.arguments.customer_id === "string" ? `(${tc.arguments.customer_id})` : "()"}
                        </span>
                      );
                    })}
                  </div>
                )}
                <div
                  style={{
                    background: "var(--surface)",
                    border: "1px solid var(--border)",
                    borderRadius: 10,
                    padding: "12px 14px",
                    fontSize: 14,
                    lineHeight: 1.55,
                    whiteSpace: "pre-wrap",
                  }}
                >
                  {turn.content}
                </div>
                {turn.tokens && (
                  <div style={{ fontSize: "0.62rem", color: "var(--slate)", marginTop: 5 }}>
                    {turn.tokens.prompt + turn.tokens.completion} tokens ({turn.tokens.prompt} in,{" "}
                    {turn.tokens.completion} out)
                  </div>
                )}
              </div>
            )}
          </div>
        ))}

        {busy && (
          <div style={{ fontSize: 13, color: "var(--slate)", display: "flex", alignItems: "center", gap: 8 }}>
            <span
              style={{
                width: 12,
                height: 12,
                border: "2px solid var(--border)",
                borderTopColor: "var(--petrol)",
                borderRadius: "50%",
                display: "inline-block",
                animation: "opp-spin 0.8s linear infinite",
              }}
            />
            Thinking — surveying the portfolio, then drilling into what matters…
          </div>
        )}
        {error && <p style={{ color: "var(--amber-ink)", fontSize: 13 }}>{error}</p>}
        <div ref={endRef} />
      </div>

      <form
        onSubmit={(e: FormEvent) => {
          e.preventDefault();
          send(input);
        }}
        style={{ display: "flex", gap: 8, padding: "12px 20px", borderTop: "1px solid var(--border)" }}
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about your customers…"
          disabled={busy}
          style={{
            flex: 1,
            padding: "9px 12px",
            borderRadius: 8,
            border: "1px solid var(--border-strong)",
            background: "var(--surface-2)",
            color: "var(--ink)",
            fontSize: 14,
          }}
        />
        <button type="submit" className="opp-btn opp-btn-primary" disabled={busy || !input.trim()}>
          Ask
        </button>
      </form>
    </div>
  );
}
