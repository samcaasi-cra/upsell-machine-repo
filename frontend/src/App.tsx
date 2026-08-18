import { useEffect, useState } from "react";
import { api, authToken } from "./api/client";
import { AgentChat } from "./components/AgentChat";
import {
  loadAudience,
  loadFontScale,
  loadViewMode,
  useFontScale,
  type Audience,
  type ViewMode,
} from "./components/BoardControls";
import { LoginScreen } from "./components/LoginScreen";
import { OpportunityBoard } from "./components/OpportunityBoard";
import { SettingsMenu } from "./components/SettingsMenu";
import { SpinnerBlock } from "./components/Spinner";
import { SuccessPlanView } from "./components/SuccessPlanView";
import { TodayView } from "./components/TodayView";

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
    return <SpinnerBlock minHeight={200} />;
  }
  if (needsAuth && !signedIn) {
    return <LoginScreen onSignedIn={() => setSignedIn(true)} />;
  }

  return <Dashboard />;
}

type Tab = "opportunities" | "today" | "ask" | "success-plan";

function Dashboard() {
  const [tab, setTab] = useState<Tab>("opportunities");
  const [viewMode, setViewMode] = useState<ViewMode>(loadViewMode);
  const [fontScale, setFontScale] = useState<number>(loadFontScale);
  const [audience, setAudience] = useState<Audience>(loadAudience);

  useFontScale(fontScale);

  return (
    <div style={{ maxWidth: 1320, margin: "0 auto", padding: "32px 20px 80px" }}>
      <header style={{ marginBottom: 20 }}>
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 12 }}>
          <div>
            <h1 style={{ margin: 0, fontSize: 26, fontFamily: "var(--font-heading)" }}>Gaia</h1>
            <p style={{ margin: "4px 0 0 0", color: "var(--text-secondary)", fontSize: 14 }}>
              AI Agent to help CSMs upsell to increase ARR
            </p>
            <p style={{ margin: "2px 0 0 0", color: "var(--text-muted)", fontSize: 12 }}>
              Initiate sales motion on the best signal detected by the AI
            </p>
          </div>

          <SettingsMenu
            audience={audience}
            onAudience={setAudience}
            viewMode={viewMode}
            onViewMode={setViewMode}
            fontScale={fontScale}
            onFontScale={setFontScale}
          />
        </div>

        <nav className="nav-tabs" aria-label="View">
          {([
            ["opportunities", "1. Best action recommendations this month to drive growth across customers"],
            ["today", '2. Today’s top new signals of ‘We’re ready to buy’'],
            ["ask", "3. Ask Gaia any question about your customers"],
            ["success-plan", "4. Joint success plan"],
          ] as [Tab, string][]).map(([key, label]) => (
            <button
              key={key}
              type="button"
              className="nav-tab-wide"
              aria-pressed={tab === key}
              onClick={() => setTab(key)}
            >
              {label}
            </button>
          ))}
        </nav>
      </header>

      {/* All four views are always mounted, just hidden via CSS when not the active
          tab -- rather than conditionally rendered. That means every tab's data fetch
          starts in parallel the moment the app loads, not only once a CSM clicks into
          it, so switching tabs is instant instead of triggering a fresh fetch (and
          Ask's conversation survives being switched away from and back). */}
      <div style={{ display: tab === "opportunities" ? "block" : "none" }}>
        <OpportunityBoard viewMode={viewMode} audience={audience} />
      </div>
      <div style={{ display: tab === "today" ? "block" : "none" }}>
        <TodayView viewMode={viewMode} onSeeAll={() => setTab("opportunities")} />
      </div>
      <div style={{ display: tab === "ask" ? "block" : "none" }}>
        <AgentChat />
      </div>
      <div style={{ display: tab === "success-plan" ? "block" : "none" }}>
        <SuccessPlanView />
      </div>
    </div>
  );
}

export default App;
