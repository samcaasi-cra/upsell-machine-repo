import { Spinner } from "./Spinner";

/**
 * Feedback banner for the auto-research flow.
 *
 * This exists because auto-research takes 30-60s (web search + scrape + LLM call), and
 * a run that legitimately finds nothing new otherwise changes nothing on screen -- both
 * of which read as "the button is broken".
 */
export function AutoResearchStatus({
  researching,
  status,
}: {
  researching: boolean;
  status: { text: string; kind: "ok" | "error" } | null;
}) {
  if (researching) {
    return (
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          fontSize: 13,
          padding: "8px 12px",
          borderRadius: 8,
          background: "rgba(42,120,214,0.10)",
          border: "1px solid var(--border)",
          color: "var(--text-secondary)",
          marginBottom: 10,
        }}
      >
        <Spinner size={12} />
        Searching the web and extracting results — this usually takes 30–60 seconds.
      </div>
    );
  }

  if (!status) return null;

  const isError = status.kind === "error";
  return (
    <div
      style={{
        fontSize: 13,
        padding: "8px 12px",
        borderRadius: 8,
        marginBottom: 10,
        background: isError ? "rgba(208,59,59,0.10)" : "rgba(12,163,12,0.10)",
        border: "1px solid var(--border)",
        color: isError ? "var(--status-critical)" : "var(--delta-good)",
      }}
    >
      {isError ? "⚠ " : "✓ "}
      {status.text}
    </div>
  );
}
