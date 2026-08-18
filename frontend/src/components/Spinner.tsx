/** A small rotating-circle loader, no text -- every "waiting on data" state in the app
 * uses this instead of a "Loading…" message. Reuses the opp-spin keyframes defined
 * once in OpportunityBoard.css. */
export function Spinner({ size = 16 }: { size?: number }) {
  return (
    <span
      style={{
        width: size,
        height: size,
        border: "2px solid var(--border)",
        borderTopColor: "var(--series-1)",
        borderRadius: "50%",
        display: "inline-block",
        animation: "opp-spin 0.8s linear infinite",
        flexShrink: 0,
      }}
    />
  );
}

/** Centered full-area variant for a component's first-load state (replaces a page's
 * entire content area, rather than sitting inline next to other UI). */
export function SpinnerBlock({ minHeight = 160 }: { minHeight?: number }) {
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight }}>
      <Spinner size={22} />
    </div>
  );
}
