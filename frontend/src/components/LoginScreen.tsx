import { useState, type FormEvent } from "react";
import { api, authToken } from "../api/client";

export function LoginScreen({ onSignedIn }: { onSignedIn: () => void }) {
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const result = await api.login(password);
      authToken.set(result.token);
      onSignedIn();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 20,
      }}
    >
      <form
        onSubmit={handleSubmit}
        style={{
          background: "var(--surface-1)",
          border: "1px solid var(--border)",
          borderRadius: 12,
          padding: 28,
          width: "100%",
          maxWidth: 380,
          display: "grid",
          gap: 14,
        }}
      >
        <div>
          <div
            style={{
              fontSize: 11,
              fontWeight: 700,
              letterSpacing: 1,
              color: "var(--text-muted)",
              textTransform: "uppercase",
            }}
          >
            SecurityScorecard · Customer Success
          </div>
          <h1 style={{ margin: "4px 0 0", fontSize: 22 }}>Upsell Machine</h1>
        </div>

        <p style={{ margin: 0, fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.5 }}>
          This dashboard shows real customer data. Enter the team password to continue.
        </p>

        <label style={{ display: "grid", gap: 5, fontSize: 13 }}>
          <span style={{ fontWeight: 600 }}>Team password</span>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoFocus
            autoComplete="current-password"
            style={{
              padding: "9px 11px",
              borderRadius: 8,
              border: "1px solid var(--border)",
              background: "var(--surface-2)",
              color: "var(--text-primary)",
              fontSize: 14,
            }}
          />
        </label>

        {error && <p style={{ margin: 0, fontSize: 13, color: "var(--status-critical)" }}>{error}</p>}

        <button
          type="submit"
          disabled={!password || busy}
          style={{
            fontSize: 13,
            fontWeight: 600,
            padding: "10px 14px",
            borderRadius: 8,
            border: "none",
            background: "var(--series-1)",
            color: "white",
            cursor: password && !busy ? "pointer" : "not-allowed",
            opacity: password && !busy ? 1 : 0.6,
          }}
        >
          {busy ? "Signing in…" : "Sign in"}
        </button>
      </form>
    </div>
  );
}
