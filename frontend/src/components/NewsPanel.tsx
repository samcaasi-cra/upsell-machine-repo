import type { CSSProperties } from "react";
import type { NewsEventType, NewsRecord } from "../types";

const EVENT_TYPE_LABEL: Record<NewsEventType, string> = {
  acquisition: "Acquisition",
  new_office: "New office",
  product_launch: "Product launch",
};

export function NewsPanel({
  record,
  onOpenResearch,
  onAutoResearch,
  autoResearchAvailable,
  autoResearching,
  autoResearchError,
}: {
  record: NewsRecord;
  onOpenResearch: () => void;
  onAutoResearch: () => void;
  autoResearchAvailable: boolean;
  autoResearching: boolean;
  autoResearchError: string | null;
}) {
  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
        <div style={{ fontSize: 13, color: "var(--text-secondary)" }}>
          {record.imported_at
            ? `Last researched ${new Date(record.imported_at).toLocaleString()}`
            : "Not researched yet"}
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button
            onClick={onAutoResearch}
            disabled={!autoResearchAvailable || autoResearching}
            title={
              autoResearchAvailable
                ? "Search the web and extract results automatically"
                : "Needs an OPENAI_API_KEY in backend/.env"
            }
            style={{
              ...buttonStyle,
              opacity: autoResearchAvailable ? 1 : 0.5,
              cursor: autoResearchAvailable && !autoResearching ? "pointer" : "not-allowed",
            }}
          >
            {autoResearching ? "Researching…" : "Auto-research"}
          </button>
          <button onClick={onOpenResearch} style={buttonStyle}>
            {record.events.length > 0 ? "Refresh research" : "Research news"}
          </button>
        </div>
      </div>

      {autoResearchError && (
        <p style={{ fontSize: 13, color: "var(--status-critical)", marginTop: 0 }}>{autoResearchError}</p>
      )}

      {record.events.length === 0 ? (
        <p style={{ fontSize: 13, color: "var(--text-muted)" }}>
          No news events tracked yet for this customer (acquisitions, new offices, product launches).
        </p>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ textAlign: "left", borderBottom: "1px solid var(--gridline)" }}>
              {["Event", "Headline", "Date"].map((h) => (
                <th key={h} style={{ padding: "6px 8px", fontSize: 11, color: "var(--text-muted)", fontWeight: 600 }}>
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {record.events.map((e) => (
              <tr key={`${e.event_type}-${e.headline}`} style={{ borderBottom: "1px solid var(--gridline)" }}>
                <td style={{ padding: "6px 8px", fontSize: 13, color: "var(--text-secondary)" }}>
                  {EVENT_TYPE_LABEL[e.event_type]}
                </td>
                <td style={{ padding: "6px 8px", fontWeight: 600 }}>
                  {e.source_url ? (
                    <a href={e.source_url} target="_blank" rel="noreferrer">
                      {e.headline}
                    </a>
                  ) : (
                    e.headline
                  )}
                </td>
                <td style={{ padding: "6px 8px", fontSize: 13, color: "var(--text-secondary)" }}>{e.date}</td>
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
