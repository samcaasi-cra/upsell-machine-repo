import { useEffect, useState } from "react";
import { GAIA_ACTIONS, type Tab } from "./actions";
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
import { Landing } from "./components/Landing";
import { LoginScreen } from "./components/LoginScreen";
import { OpportunityBoard } from "./components/OpportunityBoard";
import { PartnerFitView } from "./components/PartnerFitView";
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

  return <Shell />;
}

/* Landing page first; the dashboard mounts in the background so its data is already
   loading while the viewer reads the intro. */
function Shell() {
  const [showLanding, setShowLanding] = useState(true);
  const [tab, setTab] = useState<Tab>("opportunities");

  const enter = (t: Tab) => {
    setTab(t);
    setShowLanding(false);
    window.scrollTo(0, 0);
  };

  return (
    <>
      {showLanding && <Landing onEnter={enter} />}
      <div style={{ display: showLanding ? "none" : "block" }}>
        <Dashboard
          tab={tab}
          setTab={setTab}
          onHome={() => {
            setShowLanding(true);
            window.scrollTo(0, 0);
          }}
        />
      </div>
    </>
  );
}

function Dashboard({ tab, setTab, onHome }: { tab: Tab; setTab: (t: Tab) => void; onHome: () => void }) {
  const [viewMode, setViewMode] = useState<ViewMode>(loadViewMode);
  const [fontScale, setFontScale] = useState<number>(loadFontScale);
  const [audience, setAudience] = useState<Audience>(loadAudience);

  useFontScale(fontScale);

  return (
    <div style={{ maxWidth: 1320, margin: "0 auto", padding: "32px 20px 80px" }}>
      <header style={{ marginBottom: 20 }}>
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 12 }}>
          <div>
            <h1 className="app-wordmark">
              <button type="button" className="home-link" onClick={onHome} title="Back to the Gaia intro">
                Gaia
              </button>
            </h1>
            <p style={{ margin: "6px 0 0 0", color: "var(--text-secondary)", fontSize: 17 }}>
              AI Agent to help CSMs upsell to increase ARR
            </p>
            <p style={{ margin: "3px 0 0 0", color: "var(--text-muted)", fontSize: 14 }}>
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
          {GAIA_ACTIONS.map((a) => (
            <button
              key={a.tab}
              type="button"
              className="nav-tab-wide"
              aria-pressed={tab === a.tab}
              onClick={() => setTab(a.tab)}
            >
              <span className="nav-tab-num">{a.number}</span>
              <span className="nav-tab-text">
                <span className="nav-tab-title">{a.title}</span>
                {a.subtitle !== a.title && <span className="nav-tab-sub">{a.subtitle}</span>}
              </span>
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
      <div style={{ display: tab === "partner-fit" ? "block" : "none" }}>
        <PartnerFitView />
      </div>
    </div>
  );
}

export default App;
