import { useEffect, useState } from "react";
import { api, authToken } from "./api/client";
import { AgentChat } from "./components/AgentChat";
import { BoardControls, loadFontScale, loadViewMode, useFontScale, type ViewMode } from "./components/BoardControls";
import { LoginScreen } from "./components/LoginScreen";
import { OpportunityBoard } from "./components/OpportunityBoard";
import { TodayView } from "./components/TodayView";

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

type Tab = "today" | "opportunities" | "ask";

function Dashboard({ csmName }: { csmName: string }) {
  const [tab, setTab] = useState<Tab>("today");
  const [viewMode, setViewMode] = useState<ViewMode>(loadViewMode);
  const [fontScale, setFontScale] = useState<number>(loadFontScale);

  useFontScale(fontScale);

  return (
    <div style={{ maxWidth: 1320, margin: "0 auto", padding: "32px 20px 80px" }}>
      <header style={{ marginBottom: 20 }}>
        {csmName && (
          <p style={{ margin: "0 0 2px", color: "var(--text-secondary)", fontSize: 13 }}>
            {greeting()}, {csmName}
          </p>
        )}
        <h1 style={{ margin: 0, fontSize: 26, fontFamily: "var(--font-heading)" }}>ARR Upsell Machine</h1>
        <p style={{ margin: "4px 0 0 0", color: "var(--text-secondary)", fontSize: 14 }}>
          AI Agent to help CSMs upsell to increase ARR
        </p>
        <p style={{ margin: "2px 0 0 0", color: "var(--text-muted)", fontSize: 12 }}>
          Initiate sales motion on the best signal detected by the AI
        </p>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: 12,
            marginTop: 14,
          }}
        >
          <div className="board-controls-group" role="group" aria-label="View">
            {([
              ["today", "Today"],
              ["opportunities", "Opportunities"],
              ["ask", "Ask"],
            ] as [Tab, string][]).map(([key, label]) => (
              <button
                key={key}
                type="button"
                className="board-controls-btn"
                aria-pressed={tab === key}
                onClick={() => setTab(key)}
              >
                {label}
              </button>
            ))}
          </div>

          <BoardControls viewMode={viewMode} onViewMode={setViewMode} fontScale={fontScale} onFontScale={setFontScale} />
        </div>
      </header>

      {tab === "today" && <TodayView viewMode={viewMode} onSeeAll={() => setTab("opportunities")} />}
      {tab === "opportunities" && <OpportunityBoard viewMode={viewMode} />}
      {tab === "ask" && <AgentChat />}
    </div>
  );
}

export default App;
