import { useState } from "react";

function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[1][0]).toUpperCase();
}

// Deterministic pick from the purple family so avatars stay on-brand and stable per name.
function hueFor(name: string): string {
  const palette = ["#5422FF", "#673EF3", "#8B7BC5", "#342378", "#9A25AE"];
  let hash = 0;
  for (let i = 0; i < name.length; i++) hash = (hash * 31 + name.charCodeAt(i)) >>> 0;
  return palette[hash % palette.length];
}

/** Best-effort brand logo via Clearbit's public logo API, keyed by domain -- falls back
 * to an initials avatar when the domain has no coverage or the request fails. */
export function CustomerLogo({ domain, name, size = 20 }: { domain: string; name: string; size?: number }) {
  const [failed, setFailed] = useState(!domain);

  if (failed) {
    return (
      <span
        className="cust-logo cust-logo-fallback"
        style={{ width: size, height: size, fontSize: size * 0.42, background: hueFor(name) }}
        aria-hidden="true"
      >
        {initials(name)}
      </span>
    );
  }

  return (
    <img
      className="cust-logo"
      src={`https://logo.clearbit.com/${domain}?size=${size * 2}`}
      alt=""
      width={size}
      height={size}
      style={{ width: size, height: size }}
      onError={() => setFailed(true)}
    />
  );
}
