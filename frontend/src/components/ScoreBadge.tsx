export function ScoreBadge({
  score,
  grade,
  delta30d,
  error,
}: {
  score: number | null;
  grade: string | null;
  delta30d: number | null;
  error?: string | null;
}) {
  if (error) {
    return (
      <span style={{ fontSize: 12, color: "var(--status-critical)" }} title={error}>
        Score unavailable
      </span>
    );
  }
  if (score === null) {
    return <span style={{ fontSize: 12, color: "var(--text-muted)" }}>—</span>;
  }

  const deltaColor =
    delta30d === null || delta30d === 0
      ? "var(--text-muted)"
      : delta30d > 0
        ? "var(--delta-good)"
        : "var(--status-critical)";
  const deltaSign = delta30d !== null && delta30d > 0 ? "+" : "";

  return (
    <span style={{ display: "inline-flex", alignItems: "baseline", gap: 6 }}>
      <span style={{ fontSize: 18, fontWeight: 700, fontVariantNumeric: "tabular-nums" }}>{score}</span>
      {grade && <span style={{ fontSize: 12, color: "var(--text-muted)" }}>({grade})</span>}
      {delta30d !== null && (
        <span style={{ fontSize: 12, fontWeight: 600, color: deltaColor, fontVariantNumeric: "tabular-nums" }}>
          {deltaSign}
          {delta30d} / 30d
        </span>
      )}
    </span>
  );
}
