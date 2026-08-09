import { useCallback, useEffect, useState } from "react";
import { api } from "./api/client";
import { AddCustomerModal } from "./components/AddCustomerModal";
import { CustomerDetail } from "./components/CustomerDetail";
import { CustomerTable } from "./components/CustomerTable";
import { OpportunityBoard } from "./components/OpportunityBoard";
import type { CustomerSummary } from "./types";

type Tab = "opportunities" | "customers";

function App() {
  const [tab, setTab] = useState<Tab>("opportunities");
  const [rows, setRows] = useState<CustomerSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [showAdd, setShowAdd] = useState(false);

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
            {(["opportunities", "customers"] as Tab[]).map((t) => (
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
                {t === "opportunities" ? "Opportunities" : "Customers"}
              </button>
            ))}
          </nav>
          {tab === "customers" && !selectedId && (
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
          )}
        </div>
      </header>

      {tab === "opportunities" ? (
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
