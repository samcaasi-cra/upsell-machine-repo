import { useCallback, useEffect, useState, type ReactNode } from "react";
import { api } from "../api/client";
import type { CustomerOverview } from "../types";
import { DecisionMakerPanel } from "./DecisionMakerPanel";
import { ResearchModal } from "./ResearchModal";
import { ScoreBadge } from "./ScoreBadge";
import { ScoreChart } from "./ScoreChart";
import { SignalBadge } from "./SignalBadge";
import { UsagePanel } from "./UsagePanel";

export function CustomerDetail({ customerId, onBack }: { customerId: string; onBack: () => void }) {
  const [overview, setOverview] = useState<CustomerOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [showResearch, setShowResearch] = useState(false);

  const load = useCallback(() => {
    setLoading(true);
    api
      .getOverview(customerId)
      .then(setOverview)
      .finally(() => setLoading(false));
  }, [customerId]);

  useEffect(() => {
    load();
  }, [load]);

  if (loading || !overview) {
    return <p style={{ color: "var(--text-secondary)" }}>Loading…</p>;
  }

  const { customer, score, usage, decision_makers, signal } = overview;

  return (
    <div>
      <button onClick={onBack} style={{ ...linkButtonStyle, marginBottom: 16 }}>
        ← Back to dashboard
      </button>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <h2 style={{ margin: "0 0 4px" }}>{customer.name}</h2>
          <div style={{ color: "var(--text-muted)", fontSize: 13 }}>
            {customer.domain}
            {score.industry && ` · ${score.industry.replace(/_/g, " ")}`}
          </div>
        </div>
        <SignalBadge level={signal.level} />
      </div>

      {signal.reasons.length > 0 && (
        <ul style={{ marginTop: 10, paddingLeft: 18, fontSize: 13, color: "var(--text-secondary)" }}>
          {signal.reasons.map((r) => (
            <li key={r}>{r}</li>
          ))}
        </ul>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 8, margin: "16px 0" }}>
        <InfoField label="Sponsor" value={customer.sponsor} />
        <InfoField label="CSM" value={customer.csm} placeholder="Unassigned" />
      </div>

      <Section title="SSC Score">
        <div style={{ marginBottom: 10 }}>
          <ScoreBadge score={score.current_score} grade={score.current_grade} delta30d={score.delta_30d} error={score.error} />
          {score.delta_182d !== null && (
            <span style={{ marginLeft: 12, fontSize: 12, color: "var(--text-muted)" }}>
              {score.delta_182d >= 0 ? "+" : ""}
              {score.delta_182d} over 6 months
            </span>
          )}
        </div>
        <ScoreChart history={score.history} />
      </Section>

      <Section title="Platform usage">
        <UsagePanel usage={usage} />
      </Section>

      <Section title="Decision-makers">
        <DecisionMakerPanel record={decision_makers} onOpenResearch={() => setShowResearch(true)} />
      </Section>

      {showResearch && (
        <ResearchModal
          customerId={customer.id}
          customerName={customer.name}
          onClose={() => setShowResearch(false)}
          onImported={load}
        />
      )}
    </div>
  );
}

function InfoField({ label, value, placeholder }: { label: string; value: string | null; placeholder?: string }) {
  return (
    <div>
      <div style={{ fontSize: 11, color: "var(--text-muted)", fontWeight: 600, textTransform: "uppercase" }}>
        {label}
      </div>
      <div style={{ fontSize: 14 }}>{value ?? placeholder ?? "—"}</div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div
      style={{
        background: "var(--surface-1)",
        border: "1px solid var(--border)",
        borderRadius: 12,
        padding: 16,
        marginBottom: 16,
      }}
    >
      <h4 style={{ margin: "0 0 12px" }}>{title}</h4>
      {children}
    </div>
  );
}

const linkButtonStyle = {
  border: "none",
  background: "none",
  color: "var(--series-1)",
  fontSize: 13,
  fontWeight: 600,
  cursor: "pointer",
  padding: 0,
} as const;
