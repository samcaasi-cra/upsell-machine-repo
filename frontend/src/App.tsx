import { useEffect, useState } from "react";
import { api, authToken } from "./api/client";
import { LoginScreen } from "./components/LoginScreen";
import { OpportunityBoard } from "./components/OpportunityBoard";

/** Time-of-day greeting, so the board reads like it was opened for you just now. */
function greeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

function App() {
  // null = still checking whether this deployment requires a password
  const [needsAuth, setNeedsAuth] = useState<boolean | null>(null);
  const [signedIn, setSignedIn] = useState(false);
  const [csmName, setCsmName] = useState("");

  useEffect(() => {
    api
      .checkHealth()
      .then((h) => {
        setNeedsAuth(h.auth_required);
        setCsmName(h.csm_name);
        if (!h.auth_required || authToken.get()) setSignedIn(true);
      })
      .catch(() => setNeedsAuth(false)); // backend unreachable -- let the app surface it
  }, []);

  if (needsAuth === null) {
    return <p style={{ padding: 32, color: "var(--text-secondary)" }}>Loading…</p>;
  }
  if (needsAuth && !signedIn) {
    return <LoginScreen onSignedIn={() => setSignedIn(true)} />;
  }

  return <Dashboard csmName={csmName} />;
}

function Dashboard({ csmName }: { csmName: string }) {
  return (
    <div style={{ maxWidth: 1320, margin: "0 auto", padding: "32px 20px 80px" }}>
      <header style={{ marginBottom: 20 }}>
        {csmName && (
          <p style={{ margin: "0 0 2px", color: "var(--text-secondary)", fontSize: 13 }}>
            {greeting()}, {csmName}
          </p>
        )}
        <h1 style={{ margin: 0, fontSize: 26, fontFamily: "var(--font-heading)" }}>Gaia ARR Growth Agent</h1>
        <p style={{ margin: "4px 0 0", color: "var(--text-secondary)", fontSize: 14 }}>
          AI Agent to help CSMs upsell from Titan Watch to Titan MAX
        </p>
      </header>

      <OpportunityBoard />
    </div>
  );
}

export default App;
