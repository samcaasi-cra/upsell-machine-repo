import { useCallback, useEffect, useState } from "react";
import "./OpportunityBoard.css";
import { api } from "../api/client";
import { BoardControls, loadFontScale, loadViewMode, useFontScale, type ViewMode } from "./BoardControls";
import { CustomerLogo } from "./CustomerLogo";
import { CustomerPicker } from "./CustomerPicker";
import { EmailDrawer } from "./EmailDrawer";
import { ExternalLinkIcon, LiveIcon, ResearchedIcon, SampleIcon } from "./icons";
import { InfoPopover } from "./InfoPopover";
import type { OpportunityBoardResponse, OpportunityCard, OpportunityGroup } from "../types";

// Static per confirmation with the team -- update here if the portfolio moves.
const SSC_PORTFOLIO_URL =
  "https://platform.securityscorecard.io/#/portfolios/0a74076a-b02b-5ac9-b1d1-2b60e023ca5a/companies";

export const GROUPS: { key: OpportunityGroup; label: string; blurb: string }[] = [
  {
    key: "proof",
    label: "Own Cyber Posture",
    blurb: "Evidence the customer's own security is already paying off — cite it before they ask.",
  },
  {
    key: "adoption",
    label: "Usage",
    blurb: "Platform usage telling you the account is ready for more — deepen or expand it now.",
  },
  {
    key: "expansion",
    label: "Monitoring Opportunities",
    blurb: "Third-party and sector risk, plus new people worth bringing into monitoring or engagement.",
  },
  {
    key: "engagement",
    label: "Growing attack surface",
    blurb: "Company news that expands the customer's own footprint — acquisitions, new offices, new products.",
  },
];

function relTime(iso: string): string {
  const then = new Date(iso + "T00:00:00");
  if (Number.isNaN(then.getTime())) return "";
  const diffDays = Math.round((then.getTime() - Date.now()) / 86_400_000);
  if (diffDays === 0) return "today";
  if (diffDays > 0) return `in ${diffDays} day${diffDays === 1 ? "" : "s"}`;
  const past = Math.abs(diffDays);
  return `${past} day${past === 1 ? "" : "s"} ago`;
}

export function OpportunityBoard() {
  const [board, setBoard] = useState<OpportunityBoardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [openCardId, setOpenCardId] = useState<string | null>(null);
  const [actioned, setActioned] = useState<Set<string>>(new Set());
  const [research, setResearch] = useState<Awaited<ReturnType<typeof api.getResearchStatus>> | null>(null);
  const [showConcepts, setShowConcepts] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>(loadViewMode);
  const [fontScale, setFontScale] = useState<number>(loadFontScale);

  useFontScale(fontScale);

  const loadBoard = useCallback(() => {
    api
      .getOpportunityBoard(showConcepts)
      .then(setBoard)
      .catch((err) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false));
  }, [showConcepts]);

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
  if (error) return <p style={{ color: "var(--status-critical)" }}>Failed to load: {error}</p>;
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
          <BoardControls viewMode={viewMode} onViewMode={setViewMode} fontScale={fontScale} onFontScale={setFontScale} />
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
        <label className="opp-concept-toggle" title="Show illustrative cards for triggers from the brief that aren't built yet">
          <input
            type="checkbox"
            checked={showConcepts}
            onChange={(e) => {
              setShowConcepts(e.target.checked);
              setLoading(true);
            }}
          />
          Show unbuilt triggers as concepts
        </label>
      </div>

      <main className="opp-lanes" aria-label="Opportunity feed">
        {GROUPS.map((g) => {
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
                  {g.label}{" "}
                  <span className="opp-lane-count">({items.length})</span>
                  <InfoPopover label={`What counts as ${g.label}`}>{g.blurb}</InfoPopover>
                </div>
              </div>
              <div className="opp-lane-body">
                {items.length === 0 ? (
                  <div className="opp-lane-empty">
                    No open {g.label.toLowerCase()} right now{selectedIds.size > 0 ? " for this selection" : ""}.
                  </div>
                ) : (
                  items.map((c) => (
                    <Ticket
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

function Ticket({
  card,
  domain,
  viewMode,
  actioned,
  onOpen,
}: {
  card: OpportunityCard;
  domain: string;
  viewMode: ViewMode;
  actioned: boolean;
  onOpen: () => void;
}) {
  const showDetailInline = viewMode === "detailed" && card.detail;
  const showDetailPopover = viewMode !== "detailed" && viewMode !== "compact" && card.detail;

  return (
    <article
      className="opp-ticket"
      tabIndex={0}
      role="button"
      data-actioned={actioned}
      data-source={card.data_source}
      aria-label={`Open drafted email for ${card.customer_name}`}
      onClick={onOpen}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onOpen();
        }
      }}
    >
      <div className="opp-ticket-top">
        <span className="opp-ticket-account">
          <CustomerLogo domain={domain} name={card.customer_name} size={16} />
          {card.customer_name}
        </span>
        <span className="opp-ticket-source" onClick={(e) => e.stopPropagation()}>
          {card.data_source === "live" && (
            <InfoPopover
              label="Where this data comes from"
              align="right"
              icon={<LiveIcon style={{ color: "var(--moss)" }} />}
            >
              <span className="opp-source-pop-head">Live — SecurityScorecard API</span>
              {card.source_detail}
            </InfoPopover>
          )}
          {card.data_source === "researched" && (
            <InfoPopover
              label="Where this data comes from"
              align="right"
              icon={<ResearchedIcon style={{ color: "var(--petrol)" }} />}
            >
              <span className="opp-source-pop-head">Researched — assembled, then cached</span>
              {card.source_detail}
            </InfoPopover>
          )}
          {card.data_source === "sample" && (
            <InfoPopover
              label="Where this data comes from"
              align="right"
              icon={<SampleIcon style={{ color: "var(--slate)" }} />}
            >
              <span className="opp-source-pop-head">Sample data — placeholder</span>
              {card.source_detail}
            </InfoPopover>
          )}
          {card.data_source === "concept" && (
            <InfoPopover
              label="Not built — proposed source"
              align="right"
              icon={<span className="opp-concept-tag">⚑</span>}
            >
              <span className="opp-source-pop-head">
                Not built — concept{card.concept_trigger ? ` · Trigger ${card.concept_trigger}` : ""}
              </span>
              {card.source_detail}
            </InfoPopover>
          )}
        </span>
      </div>
      {card.badge && <span className="opp-ticket-badge">{card.badge}</span>}
      <div className="opp-ticket-metric">
        <span className={`opp-metric-value sent-${card.sentiment}`}>{card.value}</span>
        <span className="opp-metric-sub">{card.label}</span>
      </div>
      <div className="opp-ticket-desc">
        {card.description}
        {showDetailPopover && (
          <span className="opp-ticket-desc-info" onClick={(e) => e.stopPropagation()}>
            <InfoPopover label="Click for more info" align="right">
              {card.detail}
            </InfoPopover>
          </span>
        )}
      </div>
      {showDetailInline && <p className="opp-ticket-detail">{card.detail}</p>}
      <div className="opp-ticket-foot">
        <time dateTime={card.detected_at}>{relTime(card.detected_at)}</time>
        <span className="opp-ticket-cta">Click to take action →</span>
      </div>
    </article>
  );
}
