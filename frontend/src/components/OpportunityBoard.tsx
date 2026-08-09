import { useEffect, useState } from "react";
import "./OpportunityBoard.css";
import { api } from "../api/client";
import { EmailDrawer } from "./EmailDrawer";
import type { AccountChip, OpportunityBoardResponse, OpportunityCard, OpportunityGroup, Sentiment } from "../types";

export const GROUPS: { key: OpportunityGroup; label: string; blurb: string }[] = [
  {
    key: "proof",
    label: "Proof of Value",
    blurb: "Evidence the platform is already paying off — cite it before the customer asks.",
  },
  {
    key: "adoption",
    label: "Adoption Signals",
    blurb: "Usage telling you the account is ready for more — deepen or expand it now.",
  },
  {
    key: "expansion",
    label: "Expansion Events",
    blurb: "Business change from outside SSC that changes what needs covering.",
  },
  {
    key: "engagement",
    label: "Engagement Prompts",
    blurb: "People and moments worth a direct, timely touch.",
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

function gradePillClass(sentiment: Sentiment): string {
  return `opp-grade-pill opp-grade-${sentiment}`;
}

export function OpportunityBoard() {
  const [board, setBoard] = useState<OpportunityBoardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedAccountId, setSelectedAccountId] = useState<string | null>(null);
  const [openCardId, setOpenCardId] = useState<string | null>(null);
  const [actioned, setActioned] = useState<Set<string>>(new Set());

  useEffect(() => {
    api
      .getOpportunityBoard()
      .then(setBoard)
      .catch((err) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false));
  }, []);

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

  const visibleCards = selectedAccountId
    ? board.cards.filter((c) => c.customer_id === selectedAccountId)
    : board.cards;
  const accountsWithOpps = new Set(visibleCards.map((c) => c.customer_id));
  const totalCount = visibleCards.length;
  const openCard = openCardId ? board.cards.find((c) => c.card_id === openCardId) ?? null : null;

  return (
    <div className="opp-board">
      <header className="opp-topbar">
        <div>
          <span className="opp-eyebrow">SecurityScorecard · Customer Success</span>
          <h2>Opportunity Signals</h2>
        </div>
        <div className="opp-topbar-meta">
          <span className="opp-illustrative-badge">Live SSC scores · sample usage data</span>
          <span className="opp-live-count">
            <span className="opp-live-dot" aria-hidden="true" />
            {totalCount} open opportunit{totalCount === 1 ? "y" : "ies"} across {accountsWithOpps.size} account
            {accountsWithOpps.size === 1 ? "" : "s"}
          </span>
        </div>
      </header>

      <nav className="opp-account-strip" aria-label="Filter opportunities by account">
        {board.chips.map((chip: AccountChip) => {
          const pressed = selectedAccountId === chip.customer_id;
          return (
            <button
              key={chip.customer_id}
              type="button"
              className="opp-account-chip"
              aria-pressed={pressed}
              onClick={() => setSelectedAccountId(pressed ? null : chip.customer_id)}
            >
              <span className={gradePillClass(chip.sentiment)}>{chip.grade ?? "—"}</span>
              <span className="opp-chip-text">
                <span className="opp-chip-name">{chip.customer_name}</span>
                <span className="opp-chip-industry">
                  {chip.industry ? chip.industry.replace(/_/g, " ") : "—"}
                  {chip.score !== null && ` · ${chip.score}`}
                </span>
              </span>
              <span className={`opp-chip-count${chip.open_opportunities === 0 ? " zero" : ""}`}>
                {chip.open_opportunities}
              </span>
            </button>
          );
        })}
      </nav>

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
                <p className="opp-lane-name">
                  <span className="opp-lane-swatch" aria-hidden="true" />
                  {g.label}{" "}
                  <span style={{ fontFamily: "var(--font-mono)", fontWeight: 400, color: "var(--slate)", fontSize: "0.75rem" }}>
                    ({items.length})
                  </span>
                </p>
                <p className="opp-lane-blurb">{g.blurb}</p>
              </div>
              <div className="opp-lane-body">
                {items.length === 0 ? (
                  <div className="opp-lane-empty">
                    No open {g.label.toLowerCase()} right now{selectedAccountId ? " for this account" : ""}.
                  </div>
                ) : (
                  items.map((c) => (
                    <Ticket key={c.card_id} card={c} actioned={actioned.has(c.card_id)} onOpen={() => setOpenCardId(c.card_id)} />
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

function Ticket({ card, actioned, onOpen }: { card: OpportunityCard; actioned: boolean; onOpen: () => void }) {
  return (
    <article
      className="opp-ticket"
      tabIndex={0}
      role="button"
      data-actioned={actioned}
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
        <span className="opp-ticket-account">{card.customer_name}</span>
        <span className="opp-ticket-industry">{card.industry ? card.industry.replace(/_/g, " ") : ""}</span>
      </div>
      {card.badge && <span className="opp-ticket-badge">{card.badge}</span>}
      <div className="opp-ticket-metric">
        <span className={`opp-metric-value sent-${card.sentiment}`}>{card.value}</span>
        <span className="opp-metric-sub">{card.label}</span>
      </div>
      <p className="opp-ticket-desc">{card.description}</p>
      <div className="opp-ticket-foot">
        <time dateTime={card.detected_at}>{relTime(card.detected_at)}</time>
        <span className="opp-ticket-cta">Draft email →</span>
      </div>
    </article>
  );
}
