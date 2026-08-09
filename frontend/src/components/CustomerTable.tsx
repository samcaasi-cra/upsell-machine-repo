import type { CustomerSummary } from "../types";
import { ScoreBadge } from "./ScoreBadge";
import { SignalBadge } from "./SignalBadge";

export function CustomerTable({
  rows,
  onSelect,
}: {
  rows: CustomerSummary[];
  onSelect: (customerId: string) => void;
}) {
  if (rows.length === 0) {
    return <p style={{ color: "var(--text-secondary)" }}>No customers yet — add one to get started.</p>;
  }

  return (
    <div style={{ overflowX: "auto", border: "1px solid var(--border)", borderRadius: 12 }}>
      <table style={{ width: "100%", borderCollapse: "collapse", background: "var(--surface-1)" }}>
        <thead>
          <tr style={{ textAlign: "left", borderBottom: "1px solid var(--gridline)" }}>
            {[
              { label: "Customer", note: null },
              { label: "CSM", note: "sample" },
              { label: "SSC Score", note: "live" },
              { label: "Usage (7d)", note: "sample" },
              { label: "Decision-makers", note: "researched" },
              { label: "Signal", note: null },
            ].map((h) => (
              <th
                key={h.label}
                style={{
                  padding: "10px 14px",
                  fontSize: 12,
                  textTransform: "uppercase",
                  letterSpacing: 0.4,
                  color: "var(--text-muted)",
                  fontWeight: 600,
                }}
              >
                {h.label}
                {h.note && (
                  <span
                    style={{
                      display: "block",
                      fontSize: 9,
                      fontWeight: 600,
                      letterSpacing: 0.3,
                      marginTop: 2,
                      color: h.note === "live" ? "var(--delta-good)" : "var(--text-muted)",
                    }}
                  >
                    {h.note === "live" ? "● live SSC" : h.note === "researched" ? "◆ researched" : "◇ sample"}
                  </span>
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={row.customer.id}
              onClick={() => onSelect(row.customer.id)}
              style={{ borderBottom: "1px solid var(--gridline)", cursor: "pointer" }}
            >
              <td style={{ padding: "12px 14px" }}>
                <div style={{ fontWeight: 600 }}>{row.customer.name}</div>
                <div style={{ fontSize: 12, color: "var(--text-muted)" }}>{row.customer.domain}</div>
              </td>
              <td style={{ padding: "12px 14px" }}>
                {row.customer.csm ? (
                  row.customer.csm
                ) : (
                  <span
                    style={{
                      fontSize: 12,
                      fontWeight: 600,
                      color: "var(--status-warning)",
                      background: "rgba(250,178,25,0.15)",
                      padding: "2px 8px",
                      borderRadius: 999,
                    }}
                  >
                    Unassigned
                  </span>
                )}
              </td>
              <td style={{ padding: "12px 14px" }}>
                <ScoreBadge
                  score={row.current_score}
                  grade={row.current_grade}
                  delta30d={row.delta_30d}
                  error={row.score_error}
                />
              </td>
              <td style={{ padding: "12px 14px", fontSize: 13, color: "var(--text-secondary)" }}>
                {row.usage.slots_filled_7d} slots · {row.usage.reports_generated_7d} reports
              </td>
              <td style={{ padding: "12px 14px", fontSize: 13, color: "var(--text-secondary)" }}>
                {row.decision_maker_count > 0 ? `${row.decision_maker_count} tracked` : "Not researched"}
              </td>
              <td style={{ padding: "12px 14px" }}>
                <SignalBadge level={row.signal.level} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
