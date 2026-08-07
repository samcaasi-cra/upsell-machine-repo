import type { CSSProperties } from "react";
import type { DecisionMakerRecord } from "../types";

export function DecisionMakerPanel({
  record,
  onOpenResearch,
}: {
  record: DecisionMakerRecord;
  onOpenResearch: () => void;
}) {
  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
        <div style={{ fontSize: 13, color: "var(--text-secondary)" }}>
          {record.imported_at
            ? `Last researched ${new Date(record.imported_at).toLocaleString()}`
            : "Not researched yet"}
        </div>
        <button onClick={onOpenResearch} style={buttonStyle}>
          {record.people.length > 0 ? "Refresh research" : "Research decision-makers"}
        </button>
      </div>

      {record.people.length === 0 ? (
        <p style={{ fontSize: 13, color: "var(--text-muted)" }}>
          No decision-makers tracked yet for this customer.
        </p>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ textAlign: "left", borderBottom: "1px solid var(--gridline)" }}>
              {["Name", "Title", "Function", ""].map((h) => (
                <th
                  key={h}
                  style={{ padding: "6px 8px", fontSize: 11, color: "var(--text-muted)", fontWeight: 600 }}
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {record.people.map((p) => (
              <tr key={p.name} style={{ borderBottom: "1px solid var(--gridline)" }}>
                <td style={{ padding: "6px 8px", fontWeight: 600 }}>
                  {p.linkedin_url ? (
                    <a href={p.linkedin_url} target="_blank" rel="noreferrer">
                      {p.name}
                    </a>
                  ) : (
                    p.name
                  )}
                  {p.is_ciso_or_biso && (
                    <span
                      style={{
                        marginLeft: 6,
                        fontSize: 10,
                        fontWeight: 700,
                        color: "var(--series-1)",
                        border: "1px solid var(--series-1)",
                        borderRadius: 4,
                        padding: "0 4px",
                      }}
                    >
                      CISO/BISO
                    </span>
                  )}
                  {p.status === "new" && (
                    <span
                      style={{
                        marginLeft: 6,
                        fontSize: 10,
                        fontWeight: 700,
                        color: "var(--status-good)",
                        border: "1px solid var(--status-good)",
                        borderRadius: 4,
                        padding: "0 4px",
                      }}
                    >
                      NEW
                    </span>
                  )}
                </td>
                <td style={{ padding: "6px 8px", fontSize: 13 }}>{p.title}</td>
                <td style={{ padding: "6px 8px", fontSize: 13, color: "var(--text-secondary)" }}>
                  {p.primary_focus}
                </td>
                <td />
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

const buttonStyle: CSSProperties = {
  fontSize: 13,
  fontWeight: 600,
  padding: "6px 12px",
  borderRadius: 8,
  border: "1px solid var(--border)",
  background: "var(--surface-2)",
  color: "var(--text-primary)",
  cursor: "pointer",
};
