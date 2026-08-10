import { useCallback, useEffect, useState } from "react";
import { api, authToken } from "./api/client";
import { AddCustomerModal } from "./components/AddCustomerModal";
import { AgentChat } from "./components/AgentChat";
import { CustomerDetail } from "./components/CustomerDetail";
import { CustomerTable } from "./components/CustomerTable";
import { LoginScreen } from "./components/LoginScreen";
import { OpportunityBoard } from "./components/OpportunityBoard";
import type { CustomerSummary } from "./types";

type Tab = "ask" | "opportunities" | "customers";

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
  const [tab, setTab] = useState<Tab>("opportunities");
  const [rows, setRows] = useState<CustomerSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [showAdd, setShowAdd] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [syncMessage, setSyncMessage] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    api
      .listSignals()
      .then(setRows)
      .catch((err) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (tab === "customers") load();
  }, [tab, load]);

  async function handleSync() {
    setSyncing(true);
    setSyncMessage(null);
    try {
      const result = await api.syncFromPortfolio();
      setSyncMessage(
        result.added_count > 0
          ? `Added ${result.added_count} customer${result.added_count === 1 ? "" : "s"} from the portfolio.`
          : "Already up to date with the portfolio."
      );
      load();
    } catch (err) {
      setSyncMessage(`Sync failed: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setSyncing(false);
    }
  }

  return (
    <div style={{ maxWidth: 1320, margin: "0 auto", padding: "32px 20px 80px" }}>
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: 20 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 26 }}>Upsell Machine</h1>
          <p style={{ margin: "4px 0 0", color: "var(--text-secondary)", fontSize: 14 }}>
            Project 5 — Customer Upsell, Retention &amp; Decision-Making Automation
          </p>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <nav style={{ display: "flex", gap: 4, background: "var(--surface-2)", borderRadius: 8, padding: 3 }}>
            {(["ask", "opportunities", "customers"] as Tab[]).map((t) => (
              <button
                key={t}
                onClick={() => {
                  setTab(t);
                  setSelectedId(null);
                }}
                style={{
                  fontSize: 13,
                  fontWeight: 600,
                  padding: "6px 12px",
                  borderRadius: 6,
                  border: "none",
                  cursor: "pointer",
                  background: tab === t ? "var(--surface-1)" : "transparent",
                  color: tab === t ? "var(--text-primary)" : "var(--text-secondary)",
                  boxShadow: tab === t ? "0 1px 2px var(--border)" : "none",
                }}
              >
                {t === "ask" ? "Ask" : t === "opportunities" ? "Opportunities" : "Customers"}
              </button>
            ))}
          </nav>
          {tab === "customers" && !selectedId && (
            <>
              <button
                onClick={handleSync}
                disabled={syncing}
                style={{
                  fontSize: 13,
                  fontWeight: 600,
                  padding: "8px 14px",
                  borderRadius: 8,
                  border: "1px solid var(--border)",
                  background: "var(--surface-2)",
                  color: "var(--text-primary)",
                  cursor: "pointer",
                }}
              >
                {syncing ? "Syncing…" : "Sync from portfolio"}
              </button>
              <button
                onClick={() => setShowAdd(true)}
                style={{
                  fontSize: 13,
                  fontWeight: 600,
                  padding: "8px 14px",
                  borderRadius: 8,
                  border: "none",
                  background: "var(--series-1)",
                  color: "white",
                  cursor: "pointer",
                }}
              >
                + Add customer
              </button>
            </>
          )}
        </div>
      </header>

      {tab === "customers" && syncMessage && (
        <p style={{ fontSize: 13, color: "var(--text-secondary)", marginTop: -8, marginBottom: 12 }}>
          {syncMessage}
        </p>
      )}

      {tab === "ask" ? (
        <AgentChat />
      ) : tab === "opportunities" ? (
        <OpportunityBoard />
      ) : (
        <div>
          {selectedId ? (
            <CustomerDetail customerId={selectedId} onBack={() => setSelectedId(null)} />
          ) : loading ? (
            <p style={{ color: "var(--text-secondary)" }}>Loading customers…</p>
          ) : error ? (
            <p style={{ color: "var(--status-critical)" }}>Failed to load: {error}</p>
          ) : (
            <CustomerTable rows={rows} onSelect={setSelectedId} />
          )}
        </div>
      )}

      {showAdd && <AddCustomerModal onClose={() => setShowAdd(false)} onCreated={load} />}
    </div>
  );
}

export default App;
