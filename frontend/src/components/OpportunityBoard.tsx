import { useCallback, useEffect, useState } from "react";
import "./OpportunityBoard.css";
import { api } from "../api/client";
import type { Audience, ViewMode } from "./BoardControls";
import { CustomerPicker } from "./CustomerPicker";
import { EmailDrawer } from "./EmailDrawer";
import { ExternalLinkIcon, LiveIcon, MockupIcon, ResearchedIcon, SampleIcon } from "./icons";
import { InfoPopover } from "./InfoPopover";
import { OpportunityTicket } from "./OpportunityTicket";
import type { OpportunityBoardResponse, OpportunityGroup } from "../types";

// Static per confirmation with the team -- update here if the portfolio moves.
const SSC_PORTFOLIO_URL =
  "https://platform.securityscorecard.io/#/portfolios/0a74076a-b02b-5ac9-b1d1-2b60e023ca5a/companies";

export const GROUPS: { key: OpportunityGroup; label: string; blurb: string }[] = [
  {
    key: "proof",
    label: "Change in score",
    blurb: "Evidence the customer's own security score is moving — cite it before they ask.",
  },
  {
    key: "adoption",
    label: "Change in Usage",
    blurb: "Platform usage metrics — slots, logins, questionnaires — telling you the account is ready for more.",
  },
  {
    key: "expansion",
    label: "Change in Risk",
    blurb: "Third-party supplier and sector risk worth escalating monitoring for.",
  },
  {
    key: "engagement",
    label: "Change at Customer",
    blurb:
      "Everything happening at the customer's own organisation — new people, company news, and " +
      "relationship signals like email, CRM, tickets, and surveys.",
  },
];

export function OpportunityBoard({ viewMode, audience }: { viewMode: ViewMode; audience: Audience }) {
  const [board, setBoard] = useState<OpportunityBoardResponse | null>(null);
  // Only gates the very first load -- once we have data, a refetch (audience/concepts
  // toggle, the research-poll interval) happens quietly in the background instead of
  // blanking the board back to a loading placeholder.
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [openCardId, setOpenCardId] = useState<string | null>(null);
  const [actioned, setActioned] = useState<Set<string>>(new Set());
  const [research, setResearch] = useState<Awaited<ReturnType<typeof api.getResearchStatus>> | null>(null);
  const [showConcepts, setShowConcepts] = useState(false);

  const loadBoard = useCallback(() => {
    setRefreshing(true);
    api
      .getOpportunityBoard(showConcepts, audience)
      .then((data) => {
        setBoard(data);
        setError(null);
      })
      .catch((err) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => {
        setLoading(false);
        setRefreshing(false);
      });
  }, [showConcepts, audience]);

  useEffect(() => {
    loadBoard();
  }, [loadBoard]);

  const refreshResearchStatus = useCallback(() => {
    api.getResearchStatus().then(setResearch).catch(() => setResearch(null));
  }, []);

  useEffect(() => {
    refreshResearchStatus();
  }, [refreshResearchStatus]);

  // While a batch is running, poll so the board picks up new cards as they land.
  useEffect(() => {
    if (!research?.running) return;
    const id = setInterval(() => {
      refreshResearchStatus();
      loadBoard();
    }, 15000);
    return () => clearInterval(id);
  }, [research?.running, refreshResearchStatus, loadBoard]);

  async function handleRunNow() {
    await api.runResearchNow();
    setTimeout(refreshResearchStatus, 500);
  }

  function toggleActioned(id: string) {
    setActioned((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  if (loading) return <p style={{ color: "var(--text-secondary)" }}>Loading opportunities…</p>;
  if (error && !board) return <p style={{ color: "var(--status-critical)" }}>Failed to load: {error}</p>;
  if (!board) return null;

  const visibleCards = selectedIds.size === 0 ? board.cards : board.cards.filter((c) => selectedIds.has(c.customer_id));
  const accountsWithOpps = new Set(visibleCards.map((c) => c.customer_id));
  const totalCount = visibleCards.length;
  const openCard = openCardId ? board.cards.find((c) => c.card_id === openCardId) ?? null : null;
  const domainByCustomerId = new Map(board.chips.map((c) => [c.customer_id, c.domain]));

  return (
    <div className="opp-board" data-view={viewMode}>
      <header className="opp-topbar">
        <div className="opp-topbar-primary">
          <span className="opp-live-count">
            {totalCount} engagement opportunit{totalCount === 1 ? "y" : "ies"}
            <span className="opp-live-count-sub">
              across {accountsWithOpps.size} account{accountsWithOpps.size === 1 ? "" : "s"}
            </span>
          </span>
          <a className="opp-portfolio-link" href={SSC_PORTFOLIO_URL} target="_blank" rel="noreferrer">
            View in SecurityScorecard <ExternalLinkIcon />
          </a>
        </div>
        <div className="opp-topbar-controls">
          {refreshing && <span className="opp-refreshing-note">Refreshing…</span>}
          {error && <span className="opp-refresh-error-note">Couldn't refresh: {error}</span>}
          {audience === "customer" && (
            <span className="opp-audience-note">Viewing as customer — commercial signals hidden</span>
          )}
          {research && (
            <span className="opp-research-status">
              {research.running
                ? "Daily research running…"
                : research.last_run_at
                  ? `Auto-researched ${new Date(research.last_run_at).toLocaleDateString()}`
                  : "Auto-research runs daily"}
              {research.enabled && !research.running && (
                <button onClick={handleRunNow} className="opp-btn opp-btn-tiny">
                  Run now
                </button>
              )}
            </span>
          )}
        </div>
      </header>

      <div className="opp-picker-row">
        <CustomerPicker chips={board.chips} selected={selectedIds} onChange={setSelectedIds} />
      </div>

      <div className="opp-legend">
        <span className="opp-legend-item">
          <LiveIcon style={{ color: "var(--moss)" }} />
          <InfoPopover label="Click for more info">Scores, industry &amp; supplier detection — live SSC API.</InfoPopover>
        </span>
        <span className="opp-legend-item">
          <ResearchedIcon style={{ color: "var(--petrol)" }} />
          <InfoPopover label="Click for more info">News &amp; decision-makers — researched, then cached.</InfoPopover>
        </span>
        <span className="opp-legend-item">
          <SampleIcon style={{ color: "var(--slate)" }} />
          <InfoPopover label="Click for more info">
            Platform usage (logins, slots) — placeholder until the usage feed is connected.
          </InfoPopover>
        </span>
        <span className="opp-legend-item">
          <MockupIcon style={{ color: "var(--petrol)" }} />
          <InfoPopover label="Click for more info">
            Illustrative example of a source we haven't integrated yet — email, CRM, tickets, surveys.
          </InfoPopover>
        </span>
        <label className="opp-concept-toggle" title="Show illustrative cards for triggers from the brief that aren't built yet">
          <input
            type="checkbox"
            checked={showConcepts}
            onChange={(e) => setShowConcepts(e.target.checked)}
          />
          Show unbuilt triggers as concepts
        </label>
      </div>

      <p className="opp-lanes-intro">
        You have {totalCount} engagement opportunit{totalCount === 1 ? "y" : "ies"} across {accountsWithOpps.size}{" "}
        account{accountsWithOpps.size === 1 ? "" : "s"} sorted below in the four types of upsell alert.
      </p>

      <main className="opp-lanes" aria-label="Opportunity feed">
        {GROUPS.map((g, i) => {
          let items = visibleCards.filter((c) => c.group === g.key);
          items = items
            .slice()
            .sort((a, b) =>
              g.key === "engagement"
                ? new Date(a.detected_at).getTime() - new Date(b.detected_at).getTime()
                : new Date(b.detected_at).getTime() - new Date(a.detected_at).getTime()
            );

          return (
            <section key={g.key} className="opp-lane" data-group={g.key}>
              <div className="opp-lane-head">
                <div className="opp-lane-name">
                  <span className="opp-lane-swatch" aria-hidden="true" />
                  <span className="opp-lane-label-text">
                    {i + 1}. {g.label}
                  </span>
                  <InfoPopover label={`What counts as ${g.label}`}>{g.blurb}</InfoPopover>
                </div>
                <span className="opp-lane-count">
                  {items.length} card{items.length === 1 ? "" : "s"}
                </span>
              </div>
              <div className="opp-lane-body">
                {items.length === 0 ? (
                  <div className="opp-lane-empty">
                    No open {g.label.toLowerCase()} right now{selectedIds.size > 0 ? " for this selection" : ""}.
                  </div>
                ) : (
                  items.map((c) => (
                    <OpportunityTicket
                      key={c.card_id}
                      card={c}
                      domain={domainByCustomerId.get(c.customer_id) ?? ""}
                      viewMode={viewMode}
                      actioned={actioned.has(c.card_id)}
                      onOpen={() => setOpenCardId(c.card_id)}
                    />
                  ))
                )}
              </div>
            </section>
          );
        })}
      </main>

      {openCard && (
        <EmailDrawer
          card={openCard}
          groupLabel={GROUPS.find((g) => g.key === openCard.group)?.label ?? openCard.group}
          actioned={actioned.has(openCard.card_id)}
          onClose={() => setOpenCardId(null)}
          onToggleActioned={() => toggleActioned(openCard.card_id)}
        />
      )}
    </div>
  );
}

