import type { SignalLevel } from "../types";

const LEVEL_META: Record<SignalLevel, { label: string; icon: string; color: string; bg: string }> = {
  upsell: { label: "Upsell opportunity", icon: "▲", color: "var(--status-good)", bg: "rgba(12,163,12,0.12)" },
  retention_risk: {
    label: "Retention risk",
    icon: "!",
    color: "var(--status-critical)",
    bg: "rgba(208,59,59,0.12)",
  },
  neutral: { label: "Neutral", icon: "•", color: "var(--text-muted)", bg: "rgba(137,135,129,0.12)" },
};

export function SignalBadge({ level }: { level: SignalLevel }) {
  const meta = LEVEL_META[level];
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        padding: "3px 10px",
        borderRadius: 999,
        fontSize: 12,
        fontWeight: 600,
        color: meta.color,
        background: meta.bg,
        whiteSpace: "nowrap",
      }}
    >
      <span aria-hidden="true">{meta.icon}</span>
      {meta.label}
    </span>
  );
}
