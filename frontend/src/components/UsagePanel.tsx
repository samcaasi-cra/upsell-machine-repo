import type { UsageSummary } from "../types";

function DeltaTag({ value }: { value: number }) {
  if (value === 0) return <span style={{ color: "var(--text-muted)", fontSize: 12 }}>flat</span>;
  const color = value > 0 ? "var(--delta-good)" : "var(--status-critical)";
  return (
    <span style={{ color, fontSize: 12, fontWeight: 600 }}>
      {value > 0 ? "+" : ""}
      {value} vs prior week
    </span>
  );
}

export function UsagePanel({ usage }: { usage: UsageSummary }) {
  const utilizationPct = usage.licensed_slots > 0 ? Math.round((usage.slots_used / usage.licensed_slots) * 100) : 0;
  const nearCapacity = utilizationPct >= 85;

  return (
    <div>
      {usage.is_sample_data && (
        <span
          style={{
            fontSize: 11,
            fontWeight: 600,
            color: "var(--status-warning)",
            background: "rgba(250,178,25,0.15)",
            padding: "2px 8px",
            borderRadius: 999,
          }}
        >
          Sample data — platform usage feed not yet connected
        </span>
      )}

      <div style={{ display: "flex", gap: 24, margin: "14px 0", flexWrap: "wrap" }}>
        <div>
          <div style={{ fontSize: 22, fontWeight: 700 }}>{usage.slots_filled_7d}</div>
          <div style={{ fontSize: 12, color: "var(--text-secondary)" }}>Slots filled (7d)</div>
          <DeltaTag value={usage.slots_delta_7d} />
        </div>
        <div>
          <div style={{ fontSize: 22, fontWeight: 700 }}>{usage.reports_generated_7d}</div>
          <div style={{ fontSize: 12, color: "var(--text-secondary)" }}>Reports generated (7d)</div>
          <DeltaTag value={usage.reports_delta_7d} />
        </div>
        <div style={{ minWidth: 160 }}>
          <div style={{ fontSize: 22, fontWeight: 700, color: nearCapacity ? "var(--status-critical)" : undefined }}>
            {usage.slots_used} / {usage.licensed_slots}
          </div>
          <div style={{ fontSize: 12, color: "var(--text-secondary)" }}>Licensed vendor slots used</div>
          <div style={{ height: 4, background: "var(--gridline)", borderRadius: 999, marginTop: 6, width: 140 }}>
            <div
              style={{
                height: 4,
                width: `${Math.min(100, utilizationPct)}%`,
                background: nearCapacity ? "var(--status-critical)" : "var(--series-1)",
                borderRadius: 999,
              }}
            />
          </div>
        </div>
      </div>

      <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 6, fontWeight: 600 }}>
        Visits per individual (7d)
      </div>
      <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "grid", gap: 4 }}>
        {usage.individuals.map((i) => {
          const isNew = usage.new_individuals.includes(i.name);
          return (
            <li key={i.name} style={{ display: "flex", justifyContent: "space-between", fontSize: 13 }}>
              <span>
                {i.name}
                {isNew && (
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
              </span>
              <span style={{ fontVariantNumeric: "tabular-nums", color: "var(--text-secondary)" }}>
                {i.visits_7d}
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
