import { useEffect, useState } from "react";
import { api, authToken } from "./api/client";
import { LoginScreen } from "./components/LoginScreen";
import { OpportunityBoard } from "./components/OpportunityBoard";

function App() {
  // null = still checking whether this deployment requires a password
  const [needsAuth, setNeedsAuth] = useState<boolean | null>(null);
  const [signedIn, setSignedIn] = useState(false);

  useEffect(() => {
    api
      .checkHealth()
      .then((h) => {
        setNeedsAuth(h.auth_required);
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

  return <Dashboard />;
}

function Dashboard() {
  return (
    <div style={{ maxWidth: 1320, margin: "0 auto", padding: "32px 20px 80px" }}>
      <header style={{ marginBottom: 20 }}>
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
